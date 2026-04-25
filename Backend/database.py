"""
database.py — PolitiCRM
Configuración de la conexión a PostgreSQL con SQLAlchemy.

Variables de entorno requeridas (.env):
  DB_USER      → usuario de PostgreSQL       (default: postgres)
  DB_PASSWORD  → contraseña de PostgreSQL    (requerido)
  DB_HOST      → host del servidor           (default: localhost)
  DB_PORT      → puerto                      (default: 5432)
  DB_NAME      → nombre de la base de datos  (default: politicrm)

Opcional:
  DB_POOL_SIZE        → conexiones simultáneas en el pool  (default: 5)
  DB_MAX_OVERFLOW     → conexiones extra sobre el pool     (default: 10)
  DB_POOL_TIMEOUT     → segundos esperando conexión libre  (default: 30)
  DB_POOL_RECYCLE     → segundos antes de reciclar conn.   (default: 1800)
  DB_ECHO_SQL         → loguear cada SQL generado          (default: false)
"""
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [DB] %(message)s")

# =========================================================
# CONFIGURACIÓN DESDE .env
# =========================================================

DB_USER         = os.getenv("DB_USER", "postgres")
DB_PASSWORD     = os.getenv("DB_PASSWORD")
DB_HOST         = os.getenv("DB_HOST", "localhost")
DB_PORT         = int(os.getenv("DB_PORT", "5432"))
DB_NAME         = os.getenv("DB_NAME", "politicrm")

DB_POOL_SIZE    = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))
DB_ECHO_SQL     = os.getenv("DB_ECHO_SQL", "false").lower() == "true"

# Validación temprana — evita errores crípticos al arrancar
if not DB_PASSWORD:
    logger.warning(
        "⚠️  DB_PASSWORD no está configurado en .env — "
        "la conexión a PostgreSQL fallará si la BD requiere contraseña."
    )

# =========================================================
# URL DE CONEXIÓN
# =========================================================

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

# =========================================================
# ENGINE
# =========================================================

engine = create_engine(
    DATABASE_URL,
    echo=DB_ECHO_SQL,

    # Pool de conexiones — importante para FastAPI con múltiples workers
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,

    # Recicla conexiones viejas para evitar "connection closed" en producción
    pool_recycle=DB_POOL_RECYCLE,

    # Verifica que la conexión sigue viva antes de usarla
    pool_pre_ping=True,
)

# =========================================================
# SESSION FACTORY
# =========================================================

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # Evita lazy-load errors tras el commit en FastAPI
)

# =========================================================
# BASE DECLARATIVA
# =========================================================

Base = declarative_base()

# =========================================================
# DEPENDENCIA FastAPI — get_db()
# =========================================================

def get_db():
    """
    Generador de sesión para inyección de dependencias en FastAPI.

    Uso en endpoints:
        @app.get("/ejemplo")
        def ejemplo(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# =========================================================
# VERIFICACIÓN DE CONEXIÓN
# =========================================================

def verificar_conexion() -> bool:
    """
    Verifica que la BD esté accesible.
    Retorna True si la conexión es exitosa, False si falla.
    Útil para health checks y al arrancar la app.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"✓ Conexión a PostgreSQL exitosa → {DB_HOST}:{DB_PORT}/{DB_NAME}")
        return True
    except Exception as e:
        logger.error(f"✗ No se pudo conectar a PostgreSQL: {e}")
        return False


def get_db_info() -> dict:
    """
    Retorna información básica de la conexión activa.
    Útil para el endpoint de health check.
    """
    return {
        "host":     DB_HOST,
        "port":     DB_PORT,
        "database": DB_NAME,
        "user":     DB_USER,
        "pool_size": DB_POOL_SIZE,
        "echo_sql": DB_ECHO_SQL,
    }