"""
nurturing_engine.py — PolitiCRM
Motor principal del sistema de nurturing automático.

Responsabilidades:
  1. enqueue_contact()           → encola secuencia para un contacto nuevo
  2. process_pending()           → envía mensajes pendientes (llamado por scheduler)
  3. enqueue_lideres_existentes() → encola los 800+ líderes ya en la BD
  4. start_scheduler()           → inicia APScheduler integrado en FastAPI

Flujo:
  Nuevo líder/contacto
      ↓
  enqueue_contact()  →  crea NurturingLog(PENDING) por cada día de la secuencia
      ↓
  start_scheduler()  →  cada hora llama process_pending()
      ↓
  process_pending()  →  envía los mensajes cuyo scheduled_for ya pasó

Variables de entorno (.env):
  CANDIDATO_NOMBRE   → nombre del candidato
  WA_PHONE_NUMBER_ID → requerido para envío real de WhatsApp
  WA_ACCESS_TOKEN    → requerido para envío real de WhatsApp
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Literal

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database import SessionLocal
from nurturing_models import NurturingSequence, NurturingLog
from whatsapp_sender import enviar_mensaje_whatsapp

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [NURTURING] %(message)s")

CANDIDATO = os.getenv("CANDIDATO_NOMBRE", "Carlos Julio Socha")

# Hora de envío en UTC (Colombia = UTC-5, entonces 9 AM COL = 14:00 UTC)
HORA_ENVIO_UTC = int(os.getenv("NURTURING_HORA_UTC", "14"))


# ================================================================
# HELPER — renderizar mensaje
# ================================================================

def _renderizar_mensaje(template: str, nombre: str, barrio: str) -> str:
    """
    Reemplaza variables {nombre}, {barrio}, {candidato} en el mensaje.
    Aplica title-case para nombres y barrios.
    """
    return (
        template
        .replace("{nombre}",    nombre.title()  if nombre else "Líder")
        .replace("{barrio}",    barrio.title()  if barrio else "tu barrio")
        .replace("{candidato}", CANDIDATO)
    )


# ================================================================
# 1. ENCOLAR UN CONTACTO NUEVO
# ================================================================

def enqueue_contact(
    db: Session,
    contact_id: int,
    contact_type: Literal["lider", "contact"],
    nombre: str,
    telefono: str,
    sector: str = None,
    fecha_registro: datetime = None,
) -> int:
    """
    Genera todos los NurturingLog (PENDING) para un contacto recién registrado.

    Llama esta función cuando:
      - Un líder se agrega manualmente (POST /lideres/)
      - Un nuevo contacto completa el formulario en Messenger

    La prioridad de secuencias es:
      sector específico > global (para el mismo día y orden)

    Args:
        db:             Sesión de SQLAlchemy.
        contact_id:     ID del contacto (en tabla contacts o lideres_seguros).
        contact_type:   "lider" o "contact".
        nombre:         Nombre para personalizar mensajes.
        telefono:       Teléfono en formato E.164 (ej: +573001234567).
        sector:         Barrio/sector del contacto (opcional).
        fecha_registro: Fecha base para calcular los días (default: ahora).

    Returns:
        Número de mensajes encolados. 0 si ya estaba encolado.
    """
    if fecha_registro is None:
        fecha_registro = datetime.utcnow()

    # Verificar si ya tiene secuencia — no duplicar
    ya_encolado = (
        db.query(NurturingLog)
        .filter(
            NurturingLog.contact_type == contact_type,
            NurturingLog.contact_id   == contact_id,
        )
        .first()
    )
    if ya_encolado:
        logger.info(
            f"Contacto {contact_type}:{contact_id} ya tiene secuencia encolada — omitiendo"
        )
        return 0

    # ── Obtener secuencias aplicables ────────────────────────
    # Específicas del sector (prioridad alta)
    secuencias_sector = {}
    if sector:
        for seq in db.query(NurturingSequence).filter(
            NurturingSequence.sector == sector.upper(),
            NurturingSequence.activo == True,
        ).all():
            secuencias_sector[(seq.dia, seq.orden)] = seq

    # Globales (sector=None)
    secuencias_global = {}
    for seq in db.query(NurturingSequence).filter(
        NurturingSequence.sector == None,
        NurturingSequence.activo == True,
    ).all():
        secuencias_global[(seq.dia, seq.orden)] = seq

    # Merge: sector tiene prioridad sobre global en mismo (dia, orden)
    todas = {**secuencias_global, **secuencias_sector}

    if not todas:
        logger.warning(
            f"No hay secuencias activas en la BD. "
            f"Ejecuta python nurturing_seed.py primero."
        )
        return 0

    # ── Crear NurturingLog por cada secuencia ─────────────────
    total = 0
    for (dia, orden), seq in sorted(todas.items()):
        # Calcular fecha de envío: fecha_registro + días, a la hora configurada
        scheduled_for = (fecha_registro + timedelta(days=dia)).replace(
            hour=HORA_ENVIO_UTC,
            minute=0,
            second=0,
            microsecond=0,
        )

        # Si el día 0 ya pasó la hora de envío, enviarlo de inmediato (+5 min)
        if dia == 0 and scheduled_for < datetime.utcnow():
            scheduled_for = datetime.utcnow() + timedelta(minutes=5)

        log = NurturingLog(
            contact_type=contact_type,
            contact_id=contact_id,
            contact_phone=telefono,
            contact_name=nombre,
            contact_sector=sector,
            sequence_id=seq.id,
            canal=seq.canal,
            status="PENDING",
            scheduled_for=scheduled_for,
        )
        db.add(log)
        total += 1

    db.commit()
    logger.info(
        f"✓ Encolados {total} mensajes para {contact_type}:{contact_id} "
        f"({nombre}) | sector={sector or 'GLOBAL'}"
    )
    return total


# ================================================================
# 2. PROCESAR MENSAJES PENDIENTES
# ================================================================

def process_pending(batch_size: int = 50) -> dict:
    """
    Busca NurturingLogs PENDING cuyo scheduled_for ya pasó y los envía.
    El scheduler llama esta función cada hora automáticamente.

    Args:
        batch_size: Máximo de mensajes a procesar por ciclo (default: 50).

    Returns:
        Dict con resumen: {procesados, enviados, fallidos}.
    """
    db = SessionLocal()
    ahora = datetime.utcnow()

    try:
        pendientes = (
            db.query(NurturingLog)
            .filter(
                NurturingLog.status        == "PENDING",
                NurturingLog.scheduled_for <= ahora,
            )
            .order_by(NurturingLog.scheduled_for)
            .limit(batch_size)
            .all()
        )

        if not pendientes:
            logger.info("Sin mensajes pendientes en este ciclo")
            return {"procesados": 0, "enviados": 0, "fallidos": 0}

        logger.info(f"Procesando {len(pendientes)} mensajes pendientes...")
        enviados, fallidos = 0, 0

        for log in pendientes:
            # Usar db.get() — método correcto en SQLAlchemy 2.x
            seq = db.get(NurturingSequence, log.sequence_id)

            if not seq:
                log.status    = "SKIPPED"
                log.error_msg = "Secuencia no encontrada en BD"
                db.commit()
                logger.warning(f"Secuencia {log.sequence_id} no encontrada — SKIPPED")
                continue

            # Renderizar mensaje con variables del contacto
            mensaje = _renderizar_mensaje(
                template=seq.mensaje,
                nombre=log.contact_name or "Líder",
                barrio=log.contact_sector or "",
            )

            # Enviar por WhatsApp (o template si está configurado)
            resultado = enviar_mensaje_whatsapp(
                telefono_e164=log.contact_phone,
                mensaje=mensaje if not seq.template_name else None,
                template_name=seq.template_name or None,
            )

            # Actualizar estado del log
            if resultado["ok"]:
                log.status  = "SENT"
                log.sent_at = datetime.utcnow()
                enviados += 1
                logger.info(
                    f"✓ Enviado a {log.contact_name} ({log.contact_phone}) "
                    f"| día {seq.dia} | {log.contact_sector or 'GLOBAL'}"
                )
            else:
                log.status    = "FAILED"
                log.error_msg = resultado.get("error", "Error desconocido")
                fallidos += 1
                logger.warning(
                    f"✗ Falló envío a {log.contact_name} ({log.contact_phone}): "
                    f"{log.error_msg}"
                )

            db.commit()

        resumen = {
            "procesados": len(pendientes),
            "enviados":   enviados,
            "fallidos":   fallidos,
        }
        logger.info(f"✓ Ciclo nurturing completo: {resumen}")
        return resumen

    except Exception as exc:
        logger.error(f"Error crítico en process_pending: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


# ================================================================
# 3. ENCOLAR LÍDERES EXISTENTES (ejecutar una sola vez)
# ================================================================

def enqueue_lideres_existentes(batch_size: int = 100) -> int:
    """
    Encola la secuencia completa para los líderes que ya están en la BD
    y aún no tienen mensajes programados.

    Ejecutar UNA sola vez desde:
        POST /nurturing/encolar-lideres  (en /docs de FastAPI)

    Args:
        batch_size: Procesa los líderes en lotes para no saturar la BD.

    Returns:
        Total de mensajes encolados.
    """
    from lider_model import LiderSeguro, Barrio

    db = SessionLocal()
    total_encolados = 0

    try:
        # Solo líderes activos con teléfono
        lideres = (
            db.query(LiderSeguro)
            .filter(
                LiderSeguro.activo   == True,
                LiderSeguro.telefono != None,
            )
            .all()
        )

        logger.info(f"Encolando secuencia para {len(lideres)} líderes existentes...")

        for i, lider in enumerate(lideres):
            telefono = lider.telefono_e164()
            if not telefono:
                logger.warning(f"Líder {lider.id} ({lider.nombre}) sin teléfono válido — omitiendo")
                continue

            # Obtener nombre del barrio para personalizar mensajes
            barrio = db.get(Barrio, lider.barrio_id)
            sector = barrio.nombre if barrio else None

            n = enqueue_contact(
                db=db,
                contact_id=lider.id,
                contact_type="lider",
                nombre=lider.nombre,
                telefono=telefono,
                sector=sector,
                # Fecha base = ahora para los existentes
                fecha_registro=datetime.utcnow(),
            )
            total_encolados += n

            # Log de progreso cada 100 líderes
            if (i + 1) % batch_size == 0:
                logger.info(f"  Progreso: {i + 1}/{len(lideres)} líderes procesados...")

        logger.info(
            f"✓ Encolamiento masivo completado: "
            f"{total_encolados} mensajes para {len(lideres)} líderes"
        )
        return total_encolados

    except Exception as exc:
        logger.error(f"Error en enqueue_lideres_existentes: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


# ================================================================
# 4. ESTADÍSTICAS DE NURTURING
# ================================================================

def get_nurturing_stats(db: Session) -> dict:
    """
    Retorna estadísticas del estado actual del nurturing.
    Usado en el endpoint GET /nurturing/stats.
    """
    from sqlalchemy import func

    stats_by_status = dict(
        db.query(NurturingLog.status, func.count(NurturingLog.id))
        .group_by(NurturingLog.status)
        .all()
    )

    stats_by_canal = dict(
        db.query(NurturingLog.canal, func.count(NurturingLog.id))
        .group_by(NurturingLog.canal)
        .all()
    )

    proximos = (
        db.query(NurturingLog)
        .filter(NurturingLog.status == "PENDING")
        .order_by(NurturingLog.scheduled_for)
        .limit(5)
        .all()
    )

    return {
        "por_estado": stats_by_status,
        "por_canal":  stats_by_canal,
        "total":      sum(stats_by_status.values()),
        "proximos_5": [
            {
                "nombre":        p.contact_name,
                "telefono":      p.contact_phone,
                "sector":        p.contact_sector,
                "scheduled_for": p.scheduled_for.isoformat() if p.scheduled_for else None,
                "canal":         p.canal,
            }
            for p in proximos
        ],
    }


# ================================================================
# 5. INICIAR EL SCHEDULER (APScheduler)
# ================================================================

def start_scheduler():
    """
    Inicia APScheduler integrado en FastAPI.
    Llama process_pending() cada hora automáticamente.

    Se llama desde el evento @app.on_event("startup") en app.py.

    Requiere: pip install apscheduler
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler(timezone="America/Bogota")

        # Procesar mensajes pendientes cada hora
        scheduler.add_job(
            process_pending,
            trigger="interval",
            hours=1,
            id="nurturing_processor_hourly",
            replace_existing=True,
            kwargs={"batch_size": 50},
        )

        # También corre al iniciar la app (por si hubo mensajes
        # mientras el servidor estaba apagado)
        scheduler.add_job(
            process_pending,
            trigger="date",
            id="nurturing_processor_startup",
            replace_existing=True,
            kwargs={"batch_size": 100},
        )

        scheduler.start()
        logger.info("✓ Scheduler de nurturing iniciado (cada hora | timezone: Bogotá)")
        return scheduler

    except ImportError:
        logger.error(
            "✗ APScheduler no está instalado. "
            "Ejecuta: pip install apscheduler"
        )
        return None
    except Exception as exc:
        logger.error(f"✗ Error iniciando scheduler: {exc}")
        return None