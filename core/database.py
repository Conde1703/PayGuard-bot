from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta

SQLALCHEMY_DATABASE_URL = "sqlite:///payguard.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS DE DATOS ---

class Agente(Base):
    """Tabla que define la configuración de cada bot/agente en la plataforma"""
    __tablename__ = "agentes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    area = Column(String, default="SecOps")                    # Ej: SecOps, InfoSec, IT, RRHH
    canal_slack = Column(String, nullable=True)               # ID del canal en Slack (ej: C08CBG2JB...)
    # ELIMINADO: modelo_ia - El motor se gestiona a nivel central en core/engine.py
    descripcion = Column(String)
    prompt_maestro = Column(Text, nullable=True)              # System Prompt del agente
    activo = Column(Boolean, default=True)

class MensajeHilo(Base):
    """Auditoría de conversaciones por hilo"""
    __tablename__ = "mensajes_hilo"

    id = Column(Integer, primary_key=True, index=True)
    thread_ts = Column(String, index=True)
    remitente = Column(String)
    tipo = Column(String)                                     # 'usuario' o 'bot'
    contenido = Column(Text)
    fecha = Column(String)
    hora = Column(String)

Base.metadata.create_all(bind=engine)

def ejecutar_migraciones():
    """Garantiza compatibilidad de columnas si payguard.db ya existía previamente"""
    with engine.connect() as conn:
        columnas_existentes = [
            row[1] for row in conn.execute(text("PRAGMA table_info(agentes)")).fetchall()
        ]
        if "area" not in columnas_existentes:
            conn.execute(text("ALTER TABLE agentes ADD COLUMN area VARCHAR DEFAULT 'SecOps'"))
        if "canal_slack" not in columnas_existentes:
            conn.execute(text("ALTER TABLE agentes ADD COLUMN canal_slack VARCHAR"))
        conn.commit()

ejecutar_migraciones()

def aplicar_politica_retencion(dias: int = 60) -> int:
    """
    Elimina registros en MensajeHilo con antigüedad superior a `dias`.
    Garantiza la ejecución atómica y retorna el conteo de filas purgadas.
    """
    # Calculamos la fecha límite en formato YYYY-MM-DD
    fecha_corte = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")

    db = SessionLocal()
    try:
        filas_eliminadas = (
            db.query(MensajeHilo)
            .filter(MensajeHilo.fecha < fecha_corte)
            .delete(synchronize_session=False)
        )
        db.commit()
        return filas_eliminadas
    except Exception as e:
        db.rollback()
        print(f"[ERROR BD] Fallo en la retención: {e}")
        return 0
    finally:
        db.close()