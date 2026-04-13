"""
nurturing_seed.py
Carga inicial de mensajes de la secuencia en la BD.
Ejecutar UNA sola vez: python nurturing_seed.py

Variables disponibles en cada mensaje:
  {nombre}    → nombre del líder
  {barrio}    → sector/barrio del líder
  {candidato} → Carlos Julio Socha
"""
from database import SessionLocal, engine
from nurturing_models import NurturingSequence, NurturingLog, Base

Base.metadata.create_all(bind=engine)

CANDIDATO = "Carlos Julio Socha"
LEMA = "Un Nuevo Tiempo"

# ──────────────────────────────────────────────────────────────
# SECUENCIA GLOBAL (aplica a TODOS los barrios si sector=None)
# ──────────────────────────────────────────────────────────────
SECUENCIA_GLOBAL = [
    {
        "dia": 0,
        "orden": 1,
        "mensaje": (
            "Hola {nombre}, soy el equipo de {candidato}. "
            "Gracias por ser parte del cambio que necesita {barrio} y Villa del Rosario. "
            "Tu liderazgo es clave para construir Un Nuevo Tiempo. "
            "Pronto te compartiremos información importante para tu comunidad."
        ),
    },
    {
        "dia": 1,
        "orden": 1,
        "mensaje": (
            "Buenos días {nombre}. "
            "{candidato} sabe lo que significa liderar una comunidad como {barrio}. "
            "Por eso su propuesta parte de escuchar a quienes, como tú, conocen de verdad las necesidades del barrio. "
            "¿Qué es lo que más le falta hoy a {barrio}?"
        ),
    },
    {
        "dia": 3,
        "orden": 1,
        "mensaje": (
            "Hola {nombre}, te compartimos algo importante. "
            "{candidato} ha trabajado durante años en proyectos concretos para barrios como {barrio}: "
            "vías, servicios, seguridad y empleo. "
            "El hombre que transformó Villa del Rosario regresa con más fuerza. "
            "Un Nuevo Tiempo ya comenzó."
        ),
    },
    {
        "dia": 7,
        "orden": 1,
        "mensaje": (
            "Hola {nombre}, ha pasado una semana desde que te uniste. "
            "Queremos invitarte a ser parte activa del equipo de {candidato} en {barrio}. "
            "Tu papel como líder es fundamental. "
            "¿Podemos contar contigo para hablar con tus vecinos?"
        ),
    },
    {
        "dia": 15,
        "orden": 1,
        "mensaje": (
            "{nombre}, desde el equipo de {candidato} te enviamos un saludo especial. "
            "Sabemos que {barrio} merece atención y compromiso real. "
            "Juntos lo vamos a lograr. Un Nuevo Tiempo es de todos."
        ),
    },
    {
        "dia": 30,
        "orden": 1,
        "mensaje": (
            "Hola {nombre}, ya es un mes desde que te sumaste a este proyecto. "
            "{candidato} sigue firme en su compromiso con {barrio} y con toda Villa del Rosario. "
            "Gracias por tu confianza y tu liderazgo. "
            "Pronto tendremos novedades importantes para compartirte."
        ),
    },
]

# ──────────────────────────────────────────────────────────────
# MENSAJES ESPECÍFICOS POR BARRIO (día 3 personalizado)
# Puedes agregar más barrios y días aquí
# ──────────────────────────────────────────────────────────────
SECUENCIA_POR_BARRIO = {
    "CENTRO": {
        "dia": 3,
        "mensaje": (
            "Hola {nombre}, el Centro de Villa del Rosario es el corazón del municipio. "
            "{candidato} tiene una visión clara para revitalizar el comercio, "
            "mejorar el espacio público y garantizar seguridad para todos. "
            "Un Nuevo Tiempo empieza aquí."
        ),
    },
    "SENDEROS DE PAZ": {
        "dia": 3,
        "mensaje": (
            "Hola {nombre}, Senderos de Paz merece exactamente lo que su nombre dice: tranquilidad y progreso. "
            "{candidato} conoce este barrio y tiene propuestas concretas de infraestructura y convivencia. "
            "Cuéntanos, ¿qué necesita Senderos de Paz hoy?"
        ),
    },
    "GRAN COLOMBIA": {
        "dia": 3,
        "mensaje": (
            "Hola {nombre}, Gran Colombia tiene un potencial enorme. "
            "{candidato} apuesta por el desarrollo de los barrios periféricos con vías, "
            "alumbrado y espacios deportivos. Tu barrio también merece Un Nuevo Tiempo."
        ),
    },
    "GALAN": {
        "dia": 3,
        "mensaje": (
            "Hola {nombre}, Galán es un barrio con historia y con gente comprometida como tú. "
            "{candidato} sabe que el progreso de Villa del Rosario se construye barrio a barrio. "
            "Juntos vamos a hacer de Galán un ejemplo de transformación."
        ),
    },
    "20 DE JULIO": {
        "dia": 3,
        "mensaje": (
            "Hola {nombre}, el 20 de Julio es más que un barrio, es una comunidad unida. "
            "{candidato} tiene propuestas de mejoramiento de calles, parques y servicios "
            "que tu barrio necesita. Un Nuevo Tiempo es para todos."
        ),
    },
}


def seed():
    db = SessionLocal()
    try:
        existing = db.query(NurturingSequence).count()
        if existing > 0:
            print(f"Ya existen {existing} secuencias en la BD. Borra la tabla y vuelve a correr si quieres reiniciar.")
            return

        total = 0

        # Insertar secuencia global
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

        # Insertar mensajes específicos por barrio (sobrescriben el global en día 3)
        for barrio, item in SECUENCIA_POR_BARRIO.items():
            seq = NurturingSequence(
                sector=barrio,
                canal="whatsapp",
                dia=item["dia"],
                orden=1,
                mensaje=item["mensaje"],
            )
            db.add(seq)
            total += 1

        db.commit()
        print(f"✓ Seed completado: {total} mensajes insertados en nurturing_sequences")
        print("  Puedes editar los mensajes directamente desde pgAdmin en la tabla nurturing_sequences")

    finally:
        db.close()


if __name__ == "__main__":
    seed()