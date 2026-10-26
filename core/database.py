from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Configurar el motor de base de datos local (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///payguard.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# 2. Configurar la sesión para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Clase base para crear nuestros modelos (tablas)
Base = declarative_base()

# --- MODELOS DE DATOS ---

class Agente(Base):
    """Tabla que almacenará la configuración de nuestros bots/agentes"""
    __tablename__ = "agentes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    descripcion = Column(String)
    prompt_maestro = Column(String, nullable=True) # Aquí irá la instrucción del LLM
    activo = Column(Boolean, default=True)

# 4. Crear las tablas en el archivo de base de datos inmediatamente
Base.metadata.create_all(bind=engine)