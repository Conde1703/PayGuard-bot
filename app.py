import truststore
truststore.inject_into_ssl()

import os
import threading
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from core.slack_events import register_listeners
from core.database import SessionLocal, Agente

# Cargar las variables del archivo .env
load_dotenv()

bot_token = os.getenv("SLACK_BOT_TOKEN")
app_token = os.getenv("SLACK_APP_TOKEN")
allowed_channel_id = os.getenv("SLACK_ALLOWED_CHANNEL_ID")

if not all([bot_token, app_token, allowed_channel_id]):
    raise RuntimeError("Faltan variables en el archivo .env")

# 1. Inicializar el motor del bot de Slack
slack_app = App(token=bot_token)
register_listeners(slack_app, allowed_channel_id)

# 2. Inicializar la plataforma web
api = FastAPI(title="PayGuard Admin")

# Asegurar existencia de la carpeta static y montarla para servir recursos
os.makedirs("static", exist_ok=True)
api.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Esquema de validación para nuevos agentes
class NuevoAgenteSchema(BaseModel):
    nombre: str
    descripcion: str
    prompt_maestro: str

def seed_database():
    """Inserta un agente inicial si la base de datos está vacía"""
    db = SessionLocal()
    try:
        if db.query(Agente).count() == 0:
            agente_defecto = Agente(
                nombre="Agente Soporte VPN SecOps",
                descripcion="Diagnóstico y mitigación de problemas de conexión FortiClient y VPN",
                prompt_maestro="Eres un asistente de ciberseguridad enfocado en resolver fallas de VPN y credenciales corporativas.",
                activo=True
            )
            db.add(agente_defecto)
            db.commit()
    finally:
        db.close()

def leer_ultimos_logs(cantidad=5):
    try:
        with open("logs/payguard.log", "r", encoding="utf-8") as f:
            lineas = f.readlines()
            return [linea.strip() for linea in lineas[-cantidad:]]
    except FileNotFoundError:
        return ["Aún no hay registros de actividad."]

# Ruta web principal (Dashboard)
@api.get("/", response_class=HTMLResponse)
def web_dashboard(request: Request):
    db = SessionLocal()
    try:
        lista_agentes = db.query(Agente).all()
        total_activos = db.query(Agente).filter(Agente.activo == True).count()
    finally:
        db.close()

    alertas_recientes = leer_ultimos_logs()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html", 
        context={
            "bot_status": "En línea y conectado a Slack", 
            "agentes_count": total_activos,
            "agentes": lista_agentes,
            "logs": alertas_recientes
        }
    )

# Endpoint API para crear un nuevo agente
@api.post("/api/agentes")
def crear_agente(datos: NuevoAgenteSchema):
    db = SessionLocal()
    try:
        nuevo = Agente(
            nombre=datos.nombre.strip(),
            descripcion=datos.descripcion.strip(),
            prompt_maestro=datos.prompt_maestro.strip(),
            activo=True
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return {"status": "success", "id": nuevo.id}
    finally:
        db.close()

# 3. Función para aislar el bot de Slack
def start_slack_bot():
    print("Iniciando motor de Slack Bolt en segundo plano...")
    SocketModeHandler(slack_app, app_token).connect()

if __name__ == "__main__":
    seed_database()

    bot_thread = threading.Thread(target=start_slack_bot, daemon=True)
    bot_thread.start()
    
    print("Iniciando plataforma web PayGuard Admin...")
    uvicorn.run(api, host="0.0.0.0", port=8000)