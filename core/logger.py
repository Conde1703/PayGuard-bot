import logging
import os

# Asegurar que exista una carpeta para guardar los archivos de log
os.makedirs("logs", exist_ok=True)

# Configurar el comportamiento del logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[
        # Guarda los registros en un archivo local
        logging.FileHandler("logs/payguard.log", encoding='utf-8'),
        # También muestra los registros en la terminal
        logging.StreamHandler()
    ]
)

# Instancia central del logger para usar en toda la aplicación
logger = logging.getLogger("PayGuard")