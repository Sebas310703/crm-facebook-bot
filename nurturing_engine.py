"""
nurturing_engine.py
Motor principal del sistema de nurturing automático.

Dos responsabilidades:
  1. enqueue_contact()  → cuando llega un nuevo líder/contacto, programa su secuencia
  2. process_pending()  → el scheduler lo llama cada hora para enviar los mensajes listos

Integración en app.py:
    from nurturing_engine import start_scheduler
    start_scheduler()
"""
import logging
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy.orm import Session

from database import SessionLocal
from nurturing_models import NurturingSequence, NurturingLog
from whatsapp_sender import enviar_mensaje_whatsapp

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [NURTURING] %(message)s")


# ─────────────────────────────────────────────
# 1. ENCOLAR UN CONTACTO NUEVO
# ─────────────────────────────────────────────

def enqueue_contact(
    db: Session,
    contact_id: int,
    contact_type: Literal["lider", "contact"],
    nombre: str,
    telefono: str,
    sector: str = None,
    fecha_registro: datetime = None,
):
    """
    Genera todos los NurturingLog (PENDING) para un contacto recién registrado.
    Llama esto cuando:
      - Un líder se agrega manualmente
      - Un nuevo contacto llega por Messenger y completa su número
    """
    if fecha_registro is None:
        fecha_registro = datetime.utcnow()

    # Ya tiene secuencia encolada? No duplicar
    ya_encolado = db.query(NurturingLog).filter(
        NurturingLog.contact_type == contact_type,
        NurturingLog.contact_id == contact_id,
    ).first()
    if ya_encolado:
        logger.info(f"Contacto {contact_type}:{contact_id} ya tiene secuencia encolada, omitiendo")
        return 0

    # Obtener secuencias aplicables:
    # Primero las específicas del sector, luego las globales (sector=None)
    # Para cada día, el específico de barrio tiene prioridad sobre el global
    secuencias_sector = {}
    if sector:
        for seq in db.query(NurturingSequence).filter(
            NurturingSequence.sector == sector,
            NurturingSequence.activo == True,
        ).all():
            secuencias_sector[(seq.dia, seq.orden)] = seq

    secuencias_global = {}
    for seq in db.query(NurturingSequence).filter(
        NurturingSequence.sector == None,
        NurturingSequence.activo == True,
    ).all():
        secuencias_global[(seq.dia, seq.orden)] = seq

    # Merge: sector tiene prioridad en el mismo (dia, orden)
    todas = {**secuencias_global, **secuencias_sector}

    total = 0
    for (dia, orden), seq in sorted(todas.items()):
        scheduled_for = fecha_registro + timedelta(days=dia)
        # Normalizar a las 9:00 AM hora local (aproximado en UTC-5)
        scheduled_for = scheduled_for.replace(hour=14, minute=0, second=0, microsecond=0)

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
    logger.info(f"✓ Encolados {total} mensajes para {contact_type}:{contact_id} ({nombre})")
    return total


# ─────────────────────────────────────────────
# 2. PROCESAR MENSAJES PENDIENTES
# ─────────────────────────────────────────────

def _renderizar_mensaje(template: str, nombre: str, barrio: str) -> str:
    """Reemplaza variables {nombre}, {barrio}, {candidato} en el mensaje."""
    return (
        template
        .replace("{nombre}", nombre.title())
        .replace("{barrio}", barrio.title() if barrio else "tu barrio")
        .replace("{candidato}", "Carlos Julio Socha")
    )


def process_pending(batch_size: int = 50):
    """
    Busca NurturingLogs PENDING cuyo scheduled_for ya pasó y los envía.
    El scheduler llama esto cada hora.
    """
    db = SessionLocal()
    ahora = datetime.utcnow()

    try:
        pendientes = (
            db.query(NurturingLog)
            .filter(
                NurturingLog.status == "PENDING",
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
            seq = db.query(NurturingSequence).get(log.sequence_id)
            if not seq:
                log.status = "SKIPPED"
                log.error_msg = "Secuencia no encontrada"
                db.commit()
                continue

            mensaje = _renderizar_mensaje(
                seq.mensaje,
                nombre=log.contact_name or "Líder",
                barrio=log.contact_sector or "",
            )

            resultado = enviar_mensaje_whatsapp(
                telefono_e164=log.contact_phone,
                mensaje=mensaje,
            )

            if resultado["ok"]:
                log.status = "SENT"
                log.sent_at = datetime.utcnow()
                enviados += 1
            else:
                log.status = "FAILED"
                log.error_msg = resultado.get("error", "")
                fallidos += 1

            db.commit()

        resumen = {"procesados": len(pendientes), "enviados": enviados, "fallidos": fallidos}
        logger.info(f"Ciclo completo: {resumen}")
        return resumen

    except Exception as exc:
        logger.error(f"Error en process_pending: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


# ─────────────────────────────────────────────
# 3. ENCOLAR LOS 800 LÍDERES EXISTENTES
# ─────────────────────────────────────────────

def enqueue_lideres_existentes(batch_size: int = 100):
    """
    Encola la secuencia para los líderes que ya están en la BD
    y aún no tienen mensajes programados.
    Ejecutar una sola vez después del seed.
    """
    from lider_model import Lider

    db = SessionLocal()
    try:
        lideres = db.query(Lider).filter(Lider.telefono.isnot(None)).all()
        total_encolados = 0

        for lider in lideres:
            n = enqueue_contact(
                db=db,
                contact_id=lider.id,
                contact_type="lider",
                nombre=lider.nombre,
                telefono=lider.telefono_e164(),
                sector=lider.sector,
            )
            total_encolados += n

        logger.info(f"✓ Líderes existentes encolados: {total_encolados} mensajes totales")
        return total_encolados
    finally:
        db.close()


# ─────────────────────────────────────────────
# 4. INICIAR EL SCHEDULER
# ─────────────────────────────────────────────

def start_scheduler():
    """
    Inicia APScheduler integrado en FastAPI.
    Llama process_pending() cada hora.

    Instalar: pip install apscheduler
    """
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler(timezone="America/Bogota")

    # Cada hora revisa mensajes pendientes
    scheduler.add_job(
        process_pending,
        trigger="interval",
        hours=1,
        id="nurturing_processor",
        replace_existing=True,
    )

    # También corre al iniciar la app (por si hubo mensajes mientras estaba apagado)
    scheduler.add_job(
        process_pending,
        trigger="date",
        id="nurturing_startup",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✓ Scheduler de nurturing iniciado (cada hora)")
    return scheduler