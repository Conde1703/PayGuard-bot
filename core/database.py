import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

# =========================================================================
# CONFIGURACIÓN DE CIFRADO (Fernet / AES)
# =========================================================================
KEY_FILE = ".fernet.key"

# Generar clave maestra si no existe (No la subas a GitHub)
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as f:
        f.write(Fernet.generate_key())

# Cargar la clave maestra
with open(KEY_FILE, "rb") as f:
    FERNET_KEY = f.read()

cipher_suite = Fernet(FERNET_KEY)

def encriptar(texto_plano: str) -> str:
    """Cifra un texto plano y devuelve el string seguro."""
    return cipher_suite.encrypt(texto_plano.encode('utf-8')).decode('utf-8')

def desencriptar(texto_cifrado: str) -> str:
    """Descifra un string seguro y devuelve el texto plano."""
    return cipher_suite.decrypt(texto_cifrado.encode('utf-8')).decode('utf-8')

# =========================================================================
# BASE DE DATOS SQLITE
# =========================================================================
SQLALCHEMY_DATABASE_URL = "sqlite:///payguard.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS DE DATOS ---
class Agente(Base):
    __tablename__ = "agentes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    area = Column(String, default="SecOps")
    canal_slack = Column(String, nullable=True)
    descripcion = Column(String)
    prompt_maestro = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)

class MensajeHilo(Base):
    __tablename__ = "mensajes_hilo"
    id = Column(Integer, primary_key=True, index=True)
    thread_ts = Column(String, index=True)
    remitente = Column(String)
    tipo = Column(String)
    contenido = Column(Text)
    fecha = Column(String)
    hora = Column(String)

class Secreto(Base):
    """Almacén seguro de credenciales (API Keys, Tokens)"""
    __tablename__ = "secretos"
    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, unique=True, index=True)  # Ej: plugin.jira.api_token
    valor_cifrado = Column(String)                   # El token encriptado
    area = Column(String, default="Global")          # A qué equipo pertenece


def ejecutar_migraciones():
    with engine.connect() as conn:
        columnas_existentes = [
            row[1] for row in conn.execute(text("PRAGMA table_info(agentes)")).fetchall()
        ]
        if "area" not in columnas_existentes:
            conn.execute(text("ALTER TABLE agentes ADD COLUMN area VARCHAR DEFAULT 'SecOps'"))
        if "canal_slack" not in columnas_existentes:
            conn.execute(text("ALTER TABLE agentes ADD COLUMN canal_slack VARCHAR"))
        conn.commit()

def init_db():
    Base.metadata.create_all(bind=engine)
    ejecutar_migraciones()