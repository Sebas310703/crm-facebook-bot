"""
nurturing_seed.py — PolitiCRM
Carga inicial de mensajes de la secuencia de nurturing en la BD.

Ejecutar UNA sola vez:
    python nurturing_seed.py

Variables disponibles en cada mensaje:
    {nombre}    → nombre del líder o contacto
    {barrio}    → sector/barrio del líder
    {candidato} → nombre del candidato (desde .env o default)

Estructura:
    - SECUENCIA_GLOBAL     → aplica a TODOS los barrios (sector=None)
    - SECUENCIA_POR_BARRIO → mensaje del día 3 personalizado por barrio
"""
import os
from dotenv import load_dotenv
from database import SessionLocal, engine
from nurturing_models import NurturingSequence, NurturingLog, Base

load_dotenv()
Base.metadata.create_all(bind=engine)

CANDIDATO = os.getenv("CANDIDATO_NOMBRE", "Carlos Julio Socha")
LEMA      = "Un Nuevo Tiempo"

# ================================================================
# SECUENCIA GLOBAL
# Aplica a todos los barrios si no hay mensaje específico.
# Días: 0, 1, 3, 7, 15, 30
# ================================================================

SECUENCIA_GLOBAL = [
    {
        "dia": 0,
        "orden": 1,
        "mensaje": (
            f"Hola {{nombre}}, soy el equipo de {CANDIDATO}. "
            f"Gracias por ser parte del cambio que necesita {{barrio}} y Villa del Rosario. "
            f"Tu liderazgo es clave para construir {LEMA}. "
            f"Pronto te compartiremos información importante para tu comunidad. 🙌"
        ),
    },
    {
        "dia": 1,
        "orden": 1,
        "mensaje": (
            f"Buenos días {{nombre}}. "
            f"{CANDIDATO} sabe lo que significa liderar una comunidad como {{barrio}}. "
            f"Por eso su propuesta parte de escuchar a quienes, como tú, conocen de verdad "
            f"las necesidades del barrio. "
            f"¿Qué es lo que más le falta hoy a {{barrio}}? 👂"
        ),
    },
    {
        "dia": 3,
        "orden": 1,
        "mensaje": (
            f"Hola {{nombre}}, te compartimos algo importante. "
            f"{CANDIDATO} ha trabajado durante años en proyectos concretos para barrios como {{barrio}}: "
            f"vías, servicios, seguridad y empleo. "
            f"El hombre que transformó Villa del Rosario regresa con más fuerza. "
            f"{LEMA} ya comenzó. 💪"
        ),
    },
    {
        "dia": 7,
        "orden": 1,
        "mensaje": (
            f"Hola {{nombre}}, ha pasado una semana desde que te uniste. "
            f"Queremos invitarte a ser parte activa del equipo de {CANDIDATO} en {{barrio}}. "
            f"Tu papel como líder es fundamental. "
            f"¿Podemos contar contigo para hablar con tus vecinos? 🤝"
        ),
    },
    {
        "dia": 15,
        "orden": 1,
        "mensaje": (
            f"{{nombre}}, desde el equipo de {CANDIDATO} te enviamos un saludo especial. "
            f"Sabemos que {{barrio}} merece atención y compromiso real. "
            f"Juntos lo vamos a lograr. {LEMA} es de todos. 🌟"
        ),
    },
    {
        "dia": 30,
        "orden": 1,
        "mensaje": (
            f"Hola {{nombre}}, ya es un mes desde que te sumaste a este proyecto. "
            f"{CANDIDATO} sigue firme en su compromiso con {{barrio}} y con toda Villa del Rosario. "
            f"Gracias por tu confianza y tu liderazgo. "
            f"Pronto tendremos novedades importantes para compartirte. 🙏"
        ),
    },
]


# ================================================================
# SECUENCIA POR BARRIO — día 3 personalizado
# Cubre los 45 barrios. Sobrescribe el día 3 global.
# ================================================================

SECUENCIA_POR_BARRIO = {

    # ── Zona Centro ─────────────────────────────────────────────
    "CENTRO": (
        "Hola {nombre}, el Centro de Villa del Rosario es el corazón del municipio. "
        f"{CANDIDATO} tiene una visión clara para revitalizar el comercio, "
        "mejorar el espacio público y garantizar seguridad para todos. "
        f"{LEMA} empieza aquí. 🏛️"
    ),
    "SANTANDER": (
        "Hola {nombre}, Santander es un barrio con mucha historia y gente trabajadora. "
        f"{CANDIDATO} apuesta por mejorar las vías, el alumbrado y los espacios "
        "comunitarios que tu barrio merece. "
        f"Con tu liderazgo, {LEMA} llega a Santander. 💡"
    ),
    "FATIMA": (
        "Hola {nombre}, Fátima tiene una comunidad unida y comprometida. "
        f"{CANDIDATO} conoce las necesidades de tu barrio y tiene propuestas concretas "
        "de infraestructura, convivencia y desarrollo social. "
        f"{LEMA} es para Fátima también. 🌿"
    ),

    # ── Zona Sur ────────────────────────────────────────────────
    "SENDEROS DE PAZ": (
        "Hola {nombre}, Senderos de Paz merece exactamente lo que su nombre dice: "
        "tranquilidad y progreso. "
        f"{CANDIDATO} conoce este barrio y tiene propuestas concretas de "
        "infraestructura y convivencia. "
        "Cuéntanos, ¿qué necesita Senderos de Paz hoy? 🕊️"
    ),
    "TURBAY AYALA": (
        "Hola {nombre}, Turbay Ayala es un barrio con potencial enorme. "
        f"{CANDIDATO} tiene en su agenda mejorar las vías internas, el parque "
        "y los servicios públicos de tu sector. "
        f"Con líderes como tú, {LEMA} llega a Turbay Ayala. 🛣️"
    ),
    "VILLA ANTIGUA": (
        "Hola {nombre}, Villa Antigua tiene una identidad única en Villa del Rosario. "
        f"{CANDIDATO} apuesta por preservar y mejorar tu barrio con proyectos de "
        "espacio público y seguridad. "
        f"{LEMA} también es para Villa Antigua. 🏡"
    ),
    "LA PARADA": (
        "Hola {nombre}, La Parada es estratégica para el municipio. "
        f"{CANDIDATO} tiene propuestas de movilidad, comercio y seguridad "
        "diseñadas específicamente para tu zona. "
        f"Tu liderazgo es clave. {LEMA} ya comenzó en La Parada. 🚦"
    ),
    "PIEDECUESTA": (
        "Hola {nombre}, Piedecuesta merece inversión y atención real. "
        f"{CANDIDATO} se compromete con proyectos de vías, servicios y "
        "oportunidades de empleo para tu comunidad. "
        f"Juntos construimos {LEMA} en Piedecuesta. ⛰️"
    ),

    # ── Zona Norte ──────────────────────────────────────────────
    "GRAN COLOMBIA": (
        "Hola {nombre}, Gran Colombia tiene un potencial enorme. "
        f"{CANDIDATO} apuesta por el desarrollo de los barrios periféricos con vías, "
        "alumbrado y espacios deportivos. "
        f"Tu barrio también merece {LEMA}. 🌟"
    ),
    "GALAN": (
        "Hola {nombre}, Galán es un barrio con historia y gente comprometida como tú. "
        f"{CANDIDATO} sabe que el progreso de Villa del Rosario se construye barrio a barrio. "
        f"Juntos vamos a hacer de Galán un ejemplo de transformación. {LEMA}. 🏆"
    ),
    "MORICHAL": (
        "Hola {nombre}, Morichal es un barrio con una comunidad activa y comprometida. "
        f"{CANDIDATO} tiene proyectos concretos de infraestructura y medio ambiente "
        "para tu sector. "
        f"Tu liderazgo hace la diferencia. {LEMA} llega a Morichal. 🌳"
    ),
    "LA PALMITA": (
        "Hola {nombre}, La Palmita tiene una comunidad resiliente. "
        f"{CANDIDATO} conoce las necesidades de tu barrio y trabaja por mejorar "
        "las vías, el alumbrado y la seguridad. "
        f"{LEMA} es para La Palmita. 🌴"
    ),
    "PARAMO": (
        "Hola {nombre}, Páramo merece atención especial. "
        f"{CANDIDATO} tiene propuestas de mejoramiento vial, servicios públicos "
        "y espacios comunitarios para tu barrio. "
        f"Con tu apoyo, {LEMA} llega a Páramo. 🏔️"
    ),

    # ── Zona Oriente ────────────────────────────────────────────
    "SAN MARTIN": (
        "Hola {nombre}, San Martín es un barrio que merece más inversión. "
        f"{CANDIDATO} se compromete con el mejoramiento de vías, parques "
        "y oportunidades para los jóvenes de tu comunidad. "
        f"{LEMA} es para San Martín. ⚽"
    ),
    "SAN JOSE": (
        "Hola {nombre}, San José tiene una comunidad unida que trabaja por el progreso. "
        f"{CANDIDATO} apuesta por mejorar la infraestructura y los servicios "
        "de tu barrio. "
        f"Tu liderazgo impulsa {LEMA} en San José. 🙏"
    ),
    "SAN JUDAS": (
        "Hola {nombre}, San Judas merece un municipio que lo escuche. "
        f"{CANDIDATO} tiene propuestas concretas de seguridad, empleo "
        "y mejoramiento barrial para tu sector. "
        f"Con líderes como tú, {LEMA} llega a San Judas. ✊"
    ),
    "SANTA BARBARA": (
        "Hola {nombre}, Santa Bárbara es un barrio lleno de familias trabajadoras. "
        f"{CANDIDATO} se compromete con mejorar las condiciones de vida, "
        "la seguridad y los espacios públicos de tu comunidad. "
        f"{LEMA} también es para Santa Bárbara. ❤️"
    ),

    # ── Zona Montevideo ─────────────────────────────────────────
    "MONTEVIDEO": (
        "Hola {nombre}, Montevideo es uno de los sectores de mayor crecimiento "
        "en Villa del Rosario. "
        f"{CANDIDATO} tiene proyectos de legalización, vías y servicios públicos "
        "para que tu barrio tenga la calidad de vida que merece. "
        f"{LEMA} llega a Montevideo. 🏗️"
    ),
    "MONTEVIDEO 2": (
        "Hola {nombre}, Montevideo 2 crece cada día y merece planeación real. "
        f"{CANDIDATO} apuesta por la legalización predial, vías pavimentadas "
        "y servicios de calidad para tu sector. "
        f"Tu liderazgo es clave para {LEMA} en Montevideo 2. 🔑"
    ),

    # ── Zona Buenavista ─────────────────────────────────────────
    "ALTOS DE BUENAVISTA": (
        "Hola {nombre}, Altos de Buenavista tiene una vista privilegiada "
        "y una comunidad que merece lo mejor. "
        f"{CANDIDATO} tiene propuestas de conectividad, servicios y "
        "espacios comunitarios para tu sector. "
        f"{LEMA} llega a Altos de Buenavista. 🌄"
    ),
    "BUENAVISTA I": (
        "Hola {nombre}, Buenavista I es un barrio con mucho por desarrollar. "
        f"{CANDIDATO} se compromete con mejorar las vías, el alumbrado "
        "y los servicios públicos de tu comunidad. "
        f"Con tu apoyo, {LEMA} transforma Buenavista I. 💪"
    ),
    "BUENAVISTA II": (
        "Hola {nombre}, Buenavista II merece el mismo nivel de atención "
        "que cualquier barrio del municipio. "
        f"{CANDIDATO} apuesta por la equidad territorial y tiene proyectos "
        "concretos para tu sector. "
        f"{LEMA} es para Buenavista II. 🤝"
    ),

    # ── Zona Occidente ──────────────────────────────────────────
    "LOMITAS": (
        "Hola {nombre}, Lomitas tiene una comunidad activa que trabaja por su progreso. "
        f"{CANDIDATO} tiene propuestas de mejoramiento vial, servicios "
        "y oportunidades de empleo para tu barrio. "
        f"Tu liderazgo impulsa {LEMA} en Lomitas. 🚀"
    ),
    "MONACO": (
        "Hola {nombre}, Mónaco es un barrio que merece inversión y atención real. "
        f"{CANDIDATO} se compromete con el desarrollo de infraestructura "
        "y la mejora de la calidad de vida en tu sector. "
        f"{LEMA} llega a Mónaco. 🏅"
    ),
    "VILLAS DE SEVILLA": (
        "Hola {nombre}, Villas de Sevilla tiene familias que merecen "
        "un municipio que trabaje por ellas. "
        f"{CANDIDATO} tiene proyectos de espacio público, seguridad "
        "y servicios para tu barrio. "
        f"Con tu liderazgo, {LEMA} transforma Villas de Sevilla. 🌺"
    ),
    "PUEBLITO ESPAÑOL": (
        "Hola {nombre}, Pueblito Español tiene una identidad cultural única. "
        f"{CANDIDATO} apuesta por preservar y potenciar lo mejor de tu sector "
        "con proyectos de espacio público y convivencia. "
        f"{LEMA} celebra la diversidad de Pueblito Español. 🎨"
    ),

    # ── Zona Rural / Periférica ─────────────────────────────────
    "JUAN FRIO": (
        "Hola {nombre}, Juan Frío merece que el municipio voltee a verlo. "
        f"{CANDIDATO} tiene propuestas concretas de vías, servicios "
        "y oportunidades para los habitantes de tu sector. "
        f"{LEMA} llega hasta Juan Frío. 🌾"
    ),
    "EL PALMAR": (
        "Hola {nombre}, El Palmar tiene una comunidad que trabaja con esfuerzo. "
        f"{CANDIDATO} se compromete con mejorar las condiciones de vida "
        "y las oportunidades económicas de tu sector. "
        f"Tu liderazgo hace que {LEMA} llegue a El Palmar. 🌿"
    ),
    "PALOGORDO": (
        "Hola {nombre}, Palogordo es un sector que merece más atención institucional. "
        f"{CANDIDATO} tiene en agenda proyectos de conectividad, agua potable "
        "y oportunidades para tu comunidad. "
        f"{LEMA} también es para Palogordo. 💧"
    ),
    "GRAMALOTE": (
        "Hola {nombre}, Gramalote tiene una comunidad resiliente y trabajadora. "
        f"{CANDIDATO} apuesta por el desarrollo rural y la mejora de servicios "
        "básicos en tu sector. "
        f"Con tu apoyo, {LEMA} llega a Gramalote. 🌱"
    ),
    "BELLAVISTA": (
        "Hola {nombre}, Bellavista merece vivir a la altura de su nombre. "
        f"{CANDIDATO} tiene propuestas de mejoramiento urbanístico, seguridad "
        "y espacios para las familias de tu barrio. "
        f"{LEMA} transforma Bellavista. 🌅"
    ),
    "SAN GREGORIO": (
        "Hola {nombre}, San Gregorio es un sector con mucho potencial. "
        f"{CANDIDATO} se compromete con proyectos de vías, servicios públicos "
        "y oportunidades de empleo para tu comunidad. "
        f"Con tu liderazgo, {LEMA} llega a San Gregorio. ⭐"
    ),
    "LA PRIMAVERA": (
        "Hola {nombre}, La Primavera merece florecer con buena gestión municipal. "
        f"{CANDIDATO} apuesta por el desarrollo de tu barrio con proyectos "
        "de infraestructura y calidad de vida. "
        f"{LEMA} hace florecer La Primavera. 🌸"
    ),
    "ANTONIO NARIÑO": (
        "Hola {nombre}, Antonio Nariño lleva el nombre de un prócer y merece "
        "un municipio a la altura de esa historia. "
        f"{CANDIDATO} tiene proyectos concretos de mejoramiento para tu barrio. "
        f"{LEMA} honra la historia de Antonio Nariño. 🇨🇴"
    ),
    "BRISAS DEL NARIÑO": (
        "Hola {nombre}, Brisas del Nariño merece servicios de calidad "
        "y un municipio que invierta en tu comunidad. "
        f"{CANDIDATO} tiene propuestas de vías, alumbrado y espacios "
        "comunitarios para tu sector. "
        f"{LEMA} llega a Brisas del Nariño. 🌬️"
    ),
    "LIMITES": (
        "Hola {nombre}, Límites es un sector estratégico para Villa del Rosario. "
        f"{CANDIDATO} apuesta por el desarrollo de las zonas fronterizas "
        "con proyectos de seguridad, movilidad y comercio. "
        f"Tu liderazgo es clave. {LEMA} llega a Límites. 🗺️"
    ),
    "NAVARRO WOLF": (
        "Hola {nombre}, Navarro Wolf es un barrio que merece reconocimiento "
        "y atención real. "
        f"{CANDIDATO} tiene propuestas de mejoramiento barrial, servicios "
        "y oportunidades para tu comunidad. "
        f"{LEMA} llega a Navarro Wolf. 🌟"
    ),
    "TRAPICHES": (
        "Hola {nombre}, Trapiches tiene una tradición productiva que merece apoyo. "
        f"{CANDIDATO} apuesta por el desarrollo económico y la mejora "
        "de infraestructura para tu sector. "
        f"Con tu liderazgo, {LEMA} impulsa a Trapiches. 🏭"
    ),
    "VILLA GRACIELA": (
        "Hola {nombre}, Villa Graciela merece una gestión municipal que la vea. "
        f"{CANDIDATO} tiene propuestas de vías, servicios y espacios "
        "comunitarios para tu barrio. "
        f"Tu apoyo hace posible que {LEMA} llegue a Villa Graciela. 🏘️"
    ),
    "CAMPO VERDE": (
        "Hola {nombre}, Campo Verde merece inversión y atención. "
        f"{CANDIDATO} apuesta por el desarrollo de zonas verdes, "
        "infraestructura y calidad de vida en tu sector. "
        f"{LEMA} hace de Campo Verde un lugar mejor para vivir. 🌿"
    ),
    "BOCONO": (
        "Hola {nombre}, Boconó es un sector que trabaja con esfuerzo cada día. "
        f"{CANDIDATO} se compromete con mejorar las condiciones de vida, "
        "las vías y los servicios de tu comunidad. "
        f"{LEMA} llega a Boconó. 💪"
    ),
    "LA ESPERANZA ALTA": (
        "Hola {nombre}, La Esperanza Alta merece que su nombre se haga realidad. "
        f"{CANDIDATO} tiene proyectos concretos de vías, servicios "
        "y oportunidades para tu comunidad. "
        f"{LEMA} cumple la esperanza de tu barrio. ✨"
    ),
    "LA ESPERANZA BAJA": (
        "Hola {nombre}, La Esperanza Baja merece el mismo nivel de atención "
        "que cualquier otro barrio del municipio. "
        f"{CANDIDATO} apuesta por la equidad y tiene propuestas concretas "
        "para mejorar tu sector. "
        f"{LEMA} es para La Esperanza Baja también. 🌟"
    ),
    "PRIMERO DE MAYO": (
        "Hola {nombre}, Primero de Mayo tiene una comunidad que trabaja con orgullo. "
        f"{CANDIDATO} reconoce el esfuerzo de tu barrio y se compromete "
        "con proyectos de mejoramiento vial, servicios y empleo. "
        f"{LEMA} celebra a Primero de Mayo. 🙌"
    ),
    "20 DE JULIO": (
        "Hola {nombre}, el 20 de Julio es más que un barrio, es una comunidad unida. "
        f"{CANDIDATO} tiene propuestas de mejoramiento de calles, parques "
        "y servicios que tu barrio necesita. "
        f"{LEMA} es para todos en el 20 de Julio. 🇨🇴"
    ),
}


# ================================================================
# FUNCIÓN SEED
# ================================================================

def seed():
    db = SessionLocal()
    try:
        existing = db.query(NurturingSequence).count()
        if existing > 0:
            print(
                f"⚠️  Ya existen {existing} secuencias en la BD.\n"
                "   Si quieres reiniciar, ejecuta:\n"
                "   DELETE FROM nurturing_logs; DELETE FROM nurturing_sequences;\n"
                "   Y vuelve a correr este script."
            )
            return

        total = 0

        # ── Insertar secuencia global ──────────────────────────
        print("Insertando secuencia global...")
        for item in SECUENCIA_GLOBAL:
            seq = NurturingSequence(
                sector=None,
                canal="whatsapp",
                dia=item["dia"],
                orden=item["orden"],
                mensaje=item["mensaje"],
            )
            db.add(seq)
            total += 1

        # ── Insertar mensajes específicos por barrio ───────────
        print(f"Insertando mensajes por barrio ({len(SECUENCIA_POR_BARRIO)} barrios)...")
        for barrio, mensaje in SECUENCIA_POR_BARRIO.items():
            seq = NurturingSequence(
                sector=barrio,
                canal="whatsapp",
                dia=3,
                orden=1,
                mensaje=mensaje,
            )
            db.add(seq)
            total += 1

        db.commit()

        print(f"\n✓ Seed completado exitosamente:")
        print(f"  - Mensajes globales  : {len(SECUENCIA_GLOBAL)}")
        print(f"  - Barrios cubiertos  : {len(SECUENCIA_POR_BARRIO)}")
        print(f"  - Total insertados   : {total}")
        print(f"\n  Puedes editar los mensajes desde pgAdmin en la tabla nurturing_sequences")
        print(f"  Próximo paso: POST /nurturing/encolar-lideres desde /docs")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error durante el seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()