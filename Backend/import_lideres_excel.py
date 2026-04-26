"""
import_lideres_excel.py — PolitiCRM
================================================================
Importa líderes masivamente desde un archivo Excel del trabajo
casa-a-casa de la avanzada, con:

  - Mapeo flexible de columnas (acepta "lider", "LIDER", "Nombre", etc.)
  - Deduplicación en cascada: cedula → teléfono → nombre+barrio
  - UPSERT: si el líder ya existe, completa solo los campos vacíos
  - Tolerancia a datos faltantes (filas con solo nombre+barrio se aceptan)
  - Reporte de calidad de datos en Excel al finalizar

Uso:
    python import_lideres_excel.py archivo.xlsx
    python import_lideres_excel.py archivo.xlsx --dry-run   # simulación
    python import_lideres_excel.py archivo.xlsx --hoja "Hoja1"

Columnas que reconoce del Excel (cualquier variante):
    nombre / lider / nombre completo
    cedula / documento / cc / id          ← se guarda en columna 'cedula'
    telefono / celular / movil / whatsapp
    direccion / domicilio
    barrio / sector / zona
    (fecha y observacion se IGNORAN intencionalmente)

Estructura del reporte de salida (reporte_importacion_TIMESTAMP.xlsx):
    Hoja 1: Resumen        → estadísticas generales
    Hoja 2: Insertados     → líderes nuevos agregados
    Hoja 3: Actualizados   → líderes existentes a los que se les completó info
    Hoja 4: Duplicados     → ya estaban completos, se omitieron
    Hoja 5: Incompletos    → filas sin nombre o sin barrio (no insertables)
================================================================
"""
import sys
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from lider_model import LiderSeguro, Barrio


# ================================================================
# CONFIGURACIÓN
# ================================================================

# Alias aceptados para cada columna (todo en minúsculas, sin tildes)
# La clave del dict es el nombre LÓGICO interno; los valores son
# los nombres que el Excel puede traer.
ALIAS_COLUMNAS = {
    "nombre": [
        "lider", "líder", "nombre", "nombres", "nombre completo",
        "lider nombre", "nombrecompleto",
    ],
    "cedula": [
        "cedula", "cédula", "documento", "cc", "c.c.", "c.c",
        "identificacion", "identificación", "id", "no documento",
        "no. documento", "numero documento", "número documento",
        "no cedula", "no. cedula", "numero cedula",
    ],
    "telefono": [
        "celular", "telefono", "teléfono", "tel", "movil", "móvil",
        "whatsapp", "wpp", "numero", "número", "contacto",
    ],
    "direccion": [
        "direccion", "dirección", "dir", "domicilio", "ubicacion",
        "ubicación",
    ],
    "barrio": [
        "barrio", "sector", "zona", "comuna",
    ],
}

CODIGO_PAIS_DEFAULT = "57"   # Colombia
TAMANO_LOTE_COMMIT  = 500    # commit cada N registros


# ================================================================
# UTILIDADES DE NORMALIZACIÓN
# ================================================================

def normalizar_columna(nombre: str) -> str:
    """Normaliza un nombre de columna para matchear con los alias."""
    if not nombre:
        return ""
    return (
        str(nombre)
        .strip()
        .lower()
        .replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        .replace("_", " ").replace("-", " ")
    )


def detectar_columnas(df: pd.DataFrame) -> dict:
    """
    Detecta qué columna del Excel corresponde a cada campo lógico.
    Retorna dict: {"nombre": "Lider", "telefono": "Celular", ...}
    """
    mapeo = {}
    columnas_normalizadas = {normalizar_columna(c): c for c in df.columns}

    for campo_logico, alias_lista in ALIAS_COLUMNAS.items():
        for alias in alias_lista:
            alias_norm = normalizar_columna(alias)
            if alias_norm in columnas_normalizadas:
                mapeo[campo_logico] = columnas_normalizadas[alias_norm]
                break
    return mapeo


def normalizar_telefono(raw, codigo_pais: str = CODIGO_PAIS_DEFAULT) -> str:
    """
    Normaliza teléfonos a formato E.164. Misma lógica que LiderSeguro.telefono_e164().
    Maneja: '3222615734', '320 555 1234', '+573201234567', '3506867946 - 3143805345'
    
    Si el valor parece NO ser un teléfono (ej: contiene 'cra', 'cll', 'calle', etc.
    típico de direcciones que se pegaron en columna celular por error), devuelve "".
    """
    if raw is None or pd.isna(raw):
        return ""
    raw = str(raw).strip()
    if not raw or raw.lower() in ("nan", "none", "null", "-"):
        return ""

    # 🚨 Detectar valores que parecen direcciones, no teléfonos
    palabras_direccion = [
        "cra", "cll", "calle", "carrera", "kr ", "av ", "avenida",
        "manzana", "mz ", "casa", "transv", "diagonal",
    ]
    raw_lower = raw.lower()
    if any(p in raw_lower for p in palabras_direccion):
        return ""

    # Si hay múltiples números, tomar el primero
    for sep in ["\n", "\r", "-", "/", ",", ";"]:
        if sep in raw:
            raw = raw.split(sep)[0].strip()
            break

    # Quedarse solo con dígitos y +
    numero = "".join(c for c in raw if c.isdigit() or c == "+")

    if numero.startswith("+"):
        return numero
    if numero.startswith("0"):
        numero = numero[1:]
    if not numero:
        return ""

    # Validar longitud razonable (móvil colombiano = 10 dígitos)
    if len(numero) < 7 or len(numero) > 15:
        return ""

    # Si ya tiene 12 dígitos y empieza con 57, asumir que ya viene con código país
    if len(numero) == 12 and numero.startswith(codigo_pais):
        return f"+{numero}"

    return f"+{codigo_pais}{numero}"


def normalizar_cedula(raw) -> str:
    """
    Limpia la cédula: solo dígitos (quita puntos, guiones, comas, espacios).
    Si vienen MÚLTIPLES cédulas separadas por \n, /, , o ; → toma la primera.
    Si después de limpiar queda muy larga (>15 dígitos) → probablemente eran
    dos cédulas pegadas, devuelve vacío para evitar guardar basura.
    """
    if raw is None or pd.isna(raw):
        return ""
    raw = str(raw).strip()
    if not raw or raw.lower() in ("nan", "none", "null", "-"):
        return ""

    # Si hay múltiples valores, tomar el primero
    for sep in ["\n", "\r", "/", ";", "|"]:
        if sep in raw:
            raw = raw.split(sep)[0].strip()
            break

    # Solo dígitos
    cedula = "".join(c for c in raw if c.isdigit())

    # Cédulas colombianas tienen entre 6 y 10 dígitos
    # Si quedó más larga, son dos pegadas → descartar
    if len(cedula) > 12:
        return ""

    # Si quedó muy corta (<5), probablemente no era cédula
    if len(cedula) < 5:
        return ""

    return cedula


def normalizar_texto(raw) -> str:
    """Limpia un texto general (nombre, dirección, barrio)."""
    if raw is None or pd.isna(raw):
        return ""
    raw = str(raw).strip()
    if raw.lower() in ("nan", "none", "null", "-"):
        return ""
    return raw


# ================================================================
# LÓGICA DE BÚSQUEDA Y UPSERT
# ================================================================

def buscar_lider_existente(db, cedula: str, tel_norm: str,
                            nombre: str, barrio_id: int) -> LiderSeguro | None:
    """
    Busca un líder usando jerarquía de llaves:
      1. cedula     (más confiable)
      2. teléfono normalizado
      3. nombre + barrio_id
    Retorna el primer match o None.
    """
    # 🥇 Por cédula
    if cedula:
        match = db.query(LiderSeguro).filter(
            LiderSeguro.cedula == cedula
        ).first()
        if match:
            return match

    # 🥈 Por teléfono normalizado
    if tel_norm:
        # Recorrer líderes con teléfono y normalizar al vuelo
        candidatos = db.query(LiderSeguro).filter(
            LiderSeguro.telefono.isnot(None)
        ).all()
        for c in candidatos:
            if c.telefono_e164() == tel_norm:
                return c

    # 🥉 Por nombre + barrio
    if nombre and barrio_id:
        match = db.query(LiderSeguro).filter(
            LiderSeguro.nombre.ilike(nombre),
            LiderSeguro.barrio_id == barrio_id,
        ).first()
        if match:
            return match

    return None


def upsert_campos_vacios(lider: LiderSeguro, datos: dict) -> list:
    """
    Actualiza solo los campos que están vacíos en el líder existente.
    Retorna lista de campos que se actualizaron.
    """
    actualizados = []
    for campo, valor_nuevo in datos.items():
        if not valor_nuevo:
            continue
        valor_actual = getattr(lider, campo, None)
        # Solo actualiza si el valor actual está vacío/None
        if not valor_actual:
            setattr(lider, campo, valor_nuevo)
            actualizados.append(campo)
    return actualizados


# ================================================================
# BARRIOS
# ================================================================

# Tabla de equivalencias: variantes de escritura → nombre canónico.
# Si tu Excel trae el barrio escrito de varias formas, agrégalas aquí
# para que el script los unifique automáticamente.
ALIAS_BARRIOS = {
    # "VARIANTE_EN_EXCEL":  "NOMBRE_CANONICO",
    # ─── Confirmados como mismo barrio ──────────────────────────
    "BELLAVISTA":        "BELLA VISTA",
    "BELLA VISTA":       "BELLA VISTA",
    "SANGREGORIO":       "SAN GREGORIO",
    "SAN GREGORIO":      "SAN GREGORIO",
    "1 DE MAYO":         "PRIMERO DE MAYO",
    "PRIMERO DE MAYO":   "PRIMERO DE MAYO",
    # ─── Confirmados como DIFERENTES (no se unifican) ───────────
    # BUENA VISTA       → barrio aparte (NO unificar con BELLA VISTA)
    # GALAN             → barrio aparte
    # GALAN PARTE ALTA  → barrio aparte (es una zona específica
    #                     más alejada, separada para reparto de
    #                     casa-a-casa de la avanzada)
    # NARIÑO            → barrio aparte
    # NARIÑO PARTE BAJA → barrio aparte
    # ─── Agrega aquí más equivalencias que detectes ─────────────
}


def canonicalizar_barrio(nombre_barrio: str) -> str:
    """Aplica la tabla de equivalencias para devolver el nombre canónico."""
    if not nombre_barrio:
        return ""
    nombre_upper = nombre_barrio.strip().upper()
    return ALIAS_BARRIOS.get(nombre_upper, nombre_upper)


def get_or_create_barrio(db, cache_barrios: dict, nombre_barrio: str):
    """Busca el barrio en caché, BD, o lo crea. Retorna None si nombre vacío."""
    if not nombre_barrio:
        return None

    # Aplicar tabla de equivalencias
    nombre = canonicalizar_barrio(nombre_barrio)
    if nombre in cache_barrios:
        return cache_barrios[nombre]

    barrio = db.query(Barrio).filter(Barrio.nombre == nombre).first()
    if not barrio:
        barrio = Barrio(nombre=nombre)
        db.add(barrio)
        db.flush()  # asignar ID sin commit
    cache_barrios[nombre] = barrio
    return barrio


def precrear_barrios(db, cache_barrios: dict, df, mapeo: dict) -> int:
    """
    Pre-crea TODOS los barrios del Excel en una sola transacción ANTES
    de procesar líderes. Esto evita ForeignKeyViolation cuando un
    rollback de un líder borra el barrio recién creado.
    """
    if "barrio" not in mapeo:
        return 0
    col_barrio = mapeo["barrio"]
    barrios_unicos = set()
    for valor in df[col_barrio].dropna().unique():
        nombre = canonicalizar_barrio(str(valor).strip())
        if nombre:
            barrios_unicos.add(nombre)

    creados = 0
    for nombre in sorted(barrios_unicos):
        if nombre in cache_barrios:
            continue
        barrio = db.query(Barrio).filter(Barrio.nombre == nombre).first()
        if not barrio:
            barrio = Barrio(nombre=nombre)
            db.add(barrio)
            creados += 1
        cache_barrios[nombre] = barrio

    if creados > 0:
        db.commit()  # ← commit aquí los protege de rollbacks futuros
        # Recargar desde BD para asegurar que tengan ID
        for nombre in list(cache_barrios.keys()):
            cache_barrios[nombre] = db.query(Barrio).filter(
                Barrio.nombre == nombre
            ).first()
    return creados


# ================================================================
# FUNCIÓN PRINCIPAL
# ================================================================

def importar(ruta_excel: str, hoja=0, dry_run: bool = False,
             fila_encabezado: int = 0):
    print("=" * 65)
    print(f"  IMPORTACIÓN DE LÍDERES — PolitiCRM")
    print(f"  Archivo         : {ruta_excel}")
    print(f"  Hoja            : {hoja}")
    print(f"  Fila encabezado : {fila_encabezado + 1} (Excel)")
    print(f"  Modo            : {'SIMULACIÓN (dry-run)' if dry_run else 'ESCRITURA REAL'}")
    print("=" * 65)

    # ── 1) LEER EXCEL ────────────────────────────────────────────
    try:
        df = pd.read_excel(
            ruta_excel,
            sheet_name=hoja,
            dtype=str,
            header=fila_encabezado,   # ← qué fila usar como encabezado
        )
    except Exception as e:
        print(f"❌ Error leyendo Excel: {e}")
        return

    # Eliminar columnas "Unnamed" totalmente vacías
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]

    # Eliminar filas totalmente vacías
    df = df.dropna(how="all").reset_index(drop=True)

    print(f"\n📂 Filas en el Excel: {len(df)}")
    print(f"📋 Columnas detectadas: {list(df.columns)}")

    # ── 2) DETECTAR MAPEO DE COLUMNAS ────────────────────────────
    mapeo = detectar_columnas(df)
    print(f"\n🔗 Mapeo de columnas:")
    for campo, col in mapeo.items():
        print(f"   {campo:12s} → {col!r}")

    if "nombre" not in mapeo:
        print("\n❌ No se encontró columna de NOMBRE en el Excel.")
        print(f"   Alias aceptados: {ALIAS_COLUMNAS['nombre']}")
        return
    if "barrio" not in mapeo:
        print("\n⚠️ No se encontró columna de BARRIO. Las filas sin barrio NO se insertarán.")

    # ── 3) ABRIR SESIÓN Y PRECARGAR ──────────────────────────────
    db = SessionLocal()
    cache_barrios = {b.nombre: b for b in db.query(Barrio).all()}
    print(f"\n🏘️  Barrios ya en BD: {len(cache_barrios)}")
    print(f"👥 Líderes ya en BD: {db.query(LiderSeguro).count()}")

    # ── 3.5) PRE-CREAR BARRIOS (evita ForeignKeyViolation) ───────
    if not dry_run:
        nuevos_barrios = precrear_barrios(db, cache_barrios, df, mapeo)
        if nuevos_barrios > 0:
            print(f"🆕 Barrios nuevos pre-creados: {nuevos_barrios}")
    else:
        # En dry-run, solo simular en caché sin commit
        if "barrio" in mapeo:
            for valor in df[mapeo["barrio"]].dropna().unique():
                nombre = canonicalizar_barrio(str(valor).strip())
                if nombre and nombre not in cache_barrios:
                    fake_barrio = Barrio(nombre=nombre)
                    db.add(fake_barrio)
                    db.flush()
                    cache_barrios[nombre] = fake_barrio

    # ── 3.6) DETECTAR CÉDULAS DUPLICADAS DENTRO DEL EXCEL ────────
    # Si la misma cédula aparece varias veces en el Excel, solo la
    # primera se insertará. Las demás se contarán como duplicadas.
    cedulas_excel_vistas = set()

    # ── 4) PROCESAR FILAS ────────────────────────────────────────
    insertados   = []
    actualizados = []
    duplicados   = []
    incompletos  = []

    print(f"\n🚀 Procesando {len(df)} filas...\n")

    for idx, row in df.iterrows():
        try:
            # Extraer y normalizar campos
            nombre    = normalizar_texto(row.get(mapeo.get("nombre", ""), ""))
            cedula    = normalizar_cedula(row.get(mapeo.get("cedula", ""), ""))
            tel_raw   = normalizar_texto(row.get(mapeo.get("telefono", ""), ""))
            tel_norm  = normalizar_telefono(tel_raw)
            direccion = normalizar_texto(row.get(mapeo.get("direccion", ""), ""))
            barrio_nm = normalizar_texto(row.get(mapeo.get("barrio", ""), ""))

            # Validar mínimo viable: nombre + barrio
            if not nombre:
                incompletos.append({
                    "fila": idx + 2,  # +2 = fila Excel (encabezado + 1-indexed)
                    "razon": "Sin nombre",
                    "datos": dict(row),
                })
                continue

            if not barrio_nm:
                incompletos.append({
                    "fila": idx + 2,
                    "razon": "Sin barrio",
                    "datos": dict(row),
                })
                continue

            # ── DETECTAR CÉDULA DUPLICADA EN EL MISMO EXCEL ──────
            if cedula and cedula in cedulas_excel_vistas:
                duplicados.append({
                    "fila": idx + 2,
                    "id": None,
                    "nombre": nombre,
                    "razon": f"Cédula {cedula} ya apareció antes en este Excel",
                })
                continue
            if cedula:
                cedulas_excel_vistas.add(cedula)

            # Obtener/crear barrio
            barrio = get_or_create_barrio(db, cache_barrios, barrio_nm)
            if not barrio:
                incompletos.append({
                    "fila": idx + 2,
                    "razon": "Barrio inválido",
                    "datos": dict(row),
                })
                continue

            # ── BUSCAR EXISTENTE ─────────────────────────────────
            existente = buscar_lider_existente(
                db, cedula, tel_norm, nombre, barrio.id
            )

            # Si tel_raw existe pero tel_norm está vacío → era texto basura
            # (ej: "cra 8 # 10-517"). En ese caso NO guardamos teléfono.
            telefono_a_guardar = tel_raw if tel_norm else None

            datos_excel = {
                "nombre":    nombre,
                "cedula":    cedula or None,
                "telefono":  telefono_a_guardar,
                "direccion": direccion or None,
            }

            if existente:
                # ── UPSERT: completar solo campos vacíos ─────────
                campos_actualizados = upsert_campos_vacios(existente, datos_excel)
                if campos_actualizados:
                    actualizados.append({
                        "fila": idx + 2,
                        "id": existente.id,
                        "nombre": existente.nombre,
                        "campos_actualizados": ", ".join(campos_actualizados),
                        "matcheo_por": (
                            "cedula" if cedula and existente.cedula == cedula
                            else "telefono" if tel_norm and existente.telefono_e164() == tel_norm
                            else "nombre+barrio"
                        ),
                    })
                else:
                    duplicados.append({
                        "fila": idx + 2,
                        "id": existente.id,
                        "nombre": existente.nombre,
                        "razon": "Ya completo, sin campos nuevos para añadir",
                    })
            else:
                # ── INSERTAR NUEVO ───────────────────────────────
                lider = LiderSeguro(
                    nombre=nombre,
                    cedula=cedula or None,
                    telefono=telefono_a_guardar,
                    direccion=direccion or None,
                    barrio_id=barrio.id,
                )
                db.add(lider)
                insertados.append({
                    "fila": idx + 2,
                    "nombre": nombre,
                    "cedula": cedula or "",
                    "telefono": tel_raw or "",
                    "barrio": barrio.nombre,
                    "tiene_telefono": "Sí" if tel_norm else "NO",
                })

            # Commit por lotes
            if (len(insertados) + len(actualizados)) % TAMANO_LOTE_COMMIT == 0 \
                    and (len(insertados) + len(actualizados)) > 0:
                if not dry_run:
                    db.commit()
                print(f"   💾 Procesados: {len(insertados)} nuevos | "
                      f"{len(actualizados)} actualizados | "
                      f"{len(duplicados)} duplicados")

        except IntegrityError as e:
            db.rollback()
            duplicados.append({
                "fila": idx + 2,
                "razon": f"Constraint BD: {str(e)[:100]}",
            })
        except Exception as e:
            db.rollback()
            incompletos.append({
                "fila": idx + 2,
                "razon": f"Error inesperado: {str(e)[:100]}",
                "datos": dict(row),
            })

    # ── 5) COMMIT FINAL ──────────────────────────────────────────
    if dry_run:
        db.rollback()
        print("\n🧪 DRY-RUN: cambios revertidos, BD intacta.")
    else:
        db.commit()
        print("\n💾 Commit final ejecutado.")

    # ── 6) GENERAR REPORTE ───────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_reporte = f"reporte_importacion_{timestamp}.xlsx"
    ruta_reporte = Path(ruta_excel).parent / nombre_reporte

    resumen = {
        "Métrica": [
            "Filas leídas del Excel",
            "Insertados (nuevos)",
            "Actualizados (UPSERT)",
            "Duplicados (sin cambios)",
            "Incompletos (no insertados)",
            "Insertados sin teléfono",
        ],
        "Cantidad": [
            len(df),
            len(insertados),
            len(actualizados),
            len(duplicados),
            len(incompletos),
            sum(1 for i in insertados if i.get("tiene_telefono") == "NO"),
        ],
    }

    with pd.ExcelWriter(ruta_reporte, engine="openpyxl") as writer:
        pd.DataFrame(resumen).to_excel(writer, sheet_name="Resumen", index=False)
        if insertados:
            pd.DataFrame(insertados).to_excel(writer, sheet_name="Insertados", index=False)
        if actualizados:
            pd.DataFrame(actualizados).to_excel(writer, sheet_name="Actualizados", index=False)
        if duplicados:
            pd.DataFrame(duplicados).to_excel(writer, sheet_name="Duplicados", index=False)
        if incompletos:
            # Aplanar el campo "datos" para que se vea bien en Excel
            inc_plano = []
            for i in incompletos:
                fila = {"fila": i["fila"], "razon": i["razon"]}
                fila.update({f"col_{k}": v for k, v in (i.get("datos") or {}).items()})
                inc_plano.append(fila)
            pd.DataFrame(inc_plano).to_excel(writer, sheet_name="Incompletos", index=False)

    db.close()

    # ── 7) IMPRIMIR RESUMEN ──────────────────────────────────────
    print("\n" + "=" * 65)
    print("✅ IMPORTACIÓN FINALIZADA")
    print("=" * 65)
    print(f"   Filas leídas       : {len(df)}")
    print(f"   ➕ Insertados       : {len(insertados)}")
    print(f"   🔄 Actualizados     : {len(actualizados)} (UPSERT)")
    print(f"   🔁 Duplicados       : {len(duplicados)}")
    print(f"   ⚠️  Incompletos     : {len(incompletos)}")
    print(f"\n📊 Reporte generado : {ruta_reporte}")
    print("=" * 65)


# ================================================================
# CLI
# ================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importa líderes desde Excel.")
    parser.add_argument("archivo", help="Ruta al archivo .xlsx")
    parser.add_argument("--hoja", default=0,
                        help="Nombre o índice de la hoja (default: primera)")
    parser.add_argument("--fila-encabezado", type=int, default=1,
                        help="Número de fila (1-indexed, como en Excel) "
                             "donde están los encabezados. Default: 1")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simular sin escribir en la BD")
    parser.add_argument("--inspect", action="store_true",
                        help="Solo muestra las primeras 10 filas del Excel "
                             "para identificar dónde están los encabezados")
    args = parser.parse_args()

    # Si hoja es número, convertir
    try:
        hoja = int(args.hoja)
    except ValueError:
        hoja = args.hoja

    # ── MODO INSPECCIÓN ─────────────────────────────────────────
    if args.inspect:
        print("=" * 70)
        print(f"  INSPECCIÓN DE EXCEL — primeras 10 filas")
        print(f"  Archivo: {args.archivo}")
        print("=" * 70)
        df_raw = pd.read_excel(args.archivo, sheet_name=hoja,
                               header=None, dtype=str, nrows=10)
        for idx, row in df_raw.iterrows():
            valores = [str(v)[:30] if pd.notna(v) else "—" for v in row.values]
            print(f"  Fila Excel {idx + 1:2d}: {valores}")
        print("\n💡 Identifica en qué fila están los encabezados (Lider, Cedula, etc.)")
        print("   Luego corre con: --fila-encabezado N")
        print("   Ejemplo: python import_lideres_excel.py archivo.xlsx --fila-encabezado 2")
        sys.exit(0)

    # Convertir de 1-indexed (Excel) a 0-indexed (pandas)
    fila_encabezado_pandas = max(0, args.fila_encabezado - 1)

    importar(
        args.archivo,
        hoja=hoja,
        dry_run=args.dry_run,
        fila_encabezado=fila_encabezado_pandas,
    )