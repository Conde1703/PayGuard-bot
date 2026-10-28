import logging
import os
from logging.handlers import RotatingFileHandler

# Crear la carpeta logs si no existe
os.makedirs("logs", exist_ok=True)

# Formato estandarizado para eventos SecOps
log_format = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")

# 1. Handler con Rotación: Máximo 2 MB por archivo, conserva 3 respaldos históricos
file_handler = RotatingFileHandler(
    "logs/payguard.log",
    maxBytes=2 * 1024 * 1024,  # 2 Megabytes
    backupCount=3,
    encoding="utf-8"
)
file_handler.setFormatter(log_format)
file_handler.setLevel(logging.INFO)

# 2. Handler de Consola: Para ver la actividad en la terminal de VS Code
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
console_handler.setLevel(logging.INFO)

# 3. Logger exclusivo de PayGuard (No contamina la raíz global)
logger = logging.getLogger("PayGuard")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False  # Evita duplicidad hacia el logger raíz

# 4. Silenciar la telemetría ruidosa interna de Slack Bolt y SDK
# Solo registrarán eventos si ocurre un WARNING o ERROR crítico de la librería
logging.getLogger("slack_bolt").setLevel(logging.WARNING)
logging.getLogger("slack_sdk").setLevel(logging.WARNING)