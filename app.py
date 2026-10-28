import truststore
truststore.inject_into_ssl()

import os
import shutil
import secrets
from datetime import datetime, date
import threading
import uvicorn
from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from sqlalchemy import func

from core.slack_events import register_listeners
from core.database import SessionLocal, Agente, MensajeHilo, aplicar_politica_retencion

load_dotenv()

bot_token = os.getenv("SLACK_BOT_TOKEN")
app_token = os.getenv("SLACK_APP_TOKEN")
allowed_channel_id = os.getenv("SLACK_ALLOWED_CHANNEL_ID")
admin_user = os.getenv("ADMIN_USER", "admin")
admin_pass = os.getenv("ADMIN_PASS", "SecOps2024!")

if not all([bot_token, app_token, allowed_channel_id]):
    raise RuntimeError("Faltan variables críticas en el archivo .env")

# 1. Inicializar Slack Bolt
slack_app = App(token=bot_token)
register_listeners(slack_app, allowed_channel_id)

# 2. Inicializar FastAPI
api = FastAPI(title="PayGuard Admin - Enterprise")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
api.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- CAPA DE SEGURIDAD (HTTP BASIC AUTH) ---
security = HTTPBasic()

def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)):
    """Verifica credenciales contra el .env usando comparación de tiempo constante"""
    usuario_correcto = secrets.compare_digest(credentials.username, admin_user)
    pass_correcto = secrets.compare_digest(credentials.password, admin_pass)
    
    if not (usuario_correcto and pass_correcto):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Esquemas Pydantic
class NuevoAgenteSchema(BaseModel):
    nombre: str
    area: str
    canal_slack: str
    descripcion: str
    prompt_maestro: str

# Validación segura contra Path Traversal
def validar_ruta_segura(area: str, equipo: str, archivo: str) -> str:
    for parte in [area, equipo, archivo]:
        if ".." in parte or "/" in parte or "\\" in parte:
            raise HTTPException(status_code=400, detail="Nombre o ruta de archivo inválida.")
    
    knowledge_dir = os.path.abspath(os.path.join(BASE_DIR, "knowledge"))
    ruta_final = os.path.abspath(os.path.join(knowledge_dir, area.strip(), equipo.strip(), archivo.strip()))
    
    if not ruta_final.startswith(knowledge_dir):
        raise HTTPException(status_code=400, detail="Acceso denegado: ruta fuera de knowledge.")
    
    return ruta_final

def seed_database():
    """Garantiza la existencia del agente inicial de SecOps"""
    db = SessionLocal()
    try:
        if db.query(Agente).count() == 0:
            agente_defecto = Agente(
                nombre="PayGuard-bot SecOps",
                area="SecOps_Global",
                canal_slack=allowed_channel_id,
                descripcion="Agente de Triage para equipos de seguridad (Access, InfoSec, Blue Team)",
                prompt_maestro="Eres el orquestador técnico de SecOps. Deriva las solicitudes y entrega enlaces oficiales de Jira.",
                activo=True
            )
            db.add(agente_defecto)
            db.commit()
    finally:
        db.close()

# Ruta principal: Dashboard unificado con Métricas
@api.get("/", response_class=HTMLResponse)
def web_dashboard(request: Request, username: str = Depends(verificar_credenciales)):
    db = SessionLocal()
    try:
        lista_agentes = db.query(Agente).order_by(Agente.id.asc()).all()
        total_activos = db.query(Agente).filter(Agente.activo == True).count()

        # Cálculo de Métricas SecOps
        hoy = date.today().strftime("%Y-%m-%d")
        total_incidentes = db.query(MensajeHilo).filter(MensajeHilo.tipo == "usuario").count()
        incidentes_hoy = db.query(MensajeHilo).filter(
            MensajeHilo.tipo == "usuario", 
            MensajeHilo.fecha == hoy
        ).count()
        usuarios_unicos = db.query(func.count(func.distinct(MensajeHilo.remitente))).filter(
            MensajeHilo.tipo == "usuario"
        ).scalar() or 0

        # --- EVALUACIÓN DINÁMICA DE CREACIÓN DE TICKETS EN JIRA ---
        interacciones_brutas = (
            db.query(MensajeHilo)
            .filter(MensajeHilo.tipo == "usuario")
            .order_by(MensajeHilo.id.desc())
            .limit(15)
            .all()
        )
        
        interacciones = []
        for m in interacciones_brutas:
            # Buscamos si en este hilo el bot confirmó la redirección a Jira
            tiene_ticket = db.query(MensajeHilo).filter(
                MensajeHilo.thread_ts == m.thread_ts,
                MensajeHilo.contenido.like("%portal de Jira%")
            ).first() is not None

            interacciones.append({
                "fecha": m.fecha,
                "hora": m.hora,
                "remitente": m.remitente,
                "contenido": m.contenido,
                "thread_ts": m.thread_ts,
                "tiene_ticket": tiene_ticket
            })
    finally:
        db.close()

    # Escaneo dinámico del índice RAG
    knowledge_path = os.path.join(BASE_DIR, "knowledge")
    documentos = []
    if os.path.exists(knowledge_path):
        for raiz, _, archivos in os.walk(knowledge_path):
            for archivo in archivos:
                if archivo.endswith((".md", ".txt")):
                    ruta_completa = os.path.join(raiz, archivo)
                    ruta_relativa = os.path.relpath(raiz, knowledge_path)
                    partes = ruta_relativa.replace("\\", "/").split("/")
                    area_doc = partes[0] if len(partes) > 0 and partes[0] != "." else "General"
                    equipo_doc = partes[1] if len(partes) > 1 else "General"
                    
                    fecha_mod = os.path.getmtime(ruta_completa)
                    fecha_legible = datetime.fromtimestamp(fecha_mod).strftime('%Y-%m-%d %H:%M')
                    
                    documentos.append({
                        "area": area_doc,
                        "equipo": equipo_doc,
                        "archivo": archivo,
                        "tamano": round(os.path.getsize(ruta_completa) / 1024, 1),
                        "modificacion": fecha_legible
                    })

    documentos.sort(key=lambda x: x["modificacion"], reverse=True)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html", 
        context={
            "bot_status": "En línea y conectado", 
            "agentes_count": total_activos,
            "agentes": lista_agentes,
            "interacciones": interacciones,
            "default_channel": allowed_channel_id,
            "documentos": documentos,
            "total_incidentes": total_incidentes,
            "incidentes_hoy": incidentes_hoy,
            "usuarios_unicos": usuarios_unicos
        }
    )

# --- ENDPOINTS DE AGENTES ---
@api.post("/api/agentes")
def crear_agente(datos: NuevoAgenteSchema, username: str = Depends(verificar_credenciales)):
    db = SessionLocal()
    try:
        nuevo = Agente(
            nombre=datos.nombre.strip(),
            area=datos.area.strip(),
            canal_slack=datos.canal_slack.strip(),
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

@api.patch("/api/agentes/{agente_id}/toggle")
def toggle_agente(agente_id: int, username: str = Depends(verificar_credenciales)):
    db = SessionLocal()
    try:
        agente = db.query(Agente).filter(Agente.id == agente_id).first()
        if not agente:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        agente.activo = not agente.activo
        db.commit()
        return {"status": "success", "activo": agente.activo}
    finally:
        db.close()

# --- ENDPOINTS DEL VISOR DE HILOS ---
@api.get("/api/hilos/{thread_ts}")
def obtener_mensajes_hilo(thread_ts: str, username: str = Depends(verificar_credenciales)):
    db = SessionLocal()
    try:
        mensajes = (
            db.query(MensajeHilo)
            .filter(MensajeHilo.thread_ts == thread_ts)
            .order_by(MensajeHilo.id.asc())
            .all()
        )
        if not mensajes:
            raise HTTPException(status_code=404, detail="Hilo no encontrado")
        return [
            {
                "id": m.id,
                "remitente": m.remitente,
                "tipo": m.tipo,
                "contenido": m.contenido,
                "fecha": m.fecha,
                "hora": m.hora
            }
            for m in mensajes
        ]
    finally:
        db.close()

# --- ENDPOINTS DEL GESTOR DOCUMENTAL (RAG CRUD) ---
@api.post("/api/conocimiento/upload")
def subir_documento(
    area: str = Form(...),
    equipo: str = Form(...),
    file: UploadFile = File(...),
    username: str = Depends(verificar_credenciales)
):
    if not file.filename.endswith((".md", ".txt")):
        raise HTTPException(status_code=400, detail="Solo se admiten extensiones .md o .txt")
    ruta = validar_ruta_segura(area, equipo, file.filename)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success", "filename": file.filename}

@api.post("/api/conocimiento/replace")
def reemplazar_documento(
    area: str = Form(...),
    equipo: str = Form(...),
    archivo_original: str = Form(...),
    file: UploadFile = File(...),
    username: str = Depends(verificar_credenciales)
):
    if not file.filename.endswith((".md", ".txt")):
        raise HTTPException(status_code=400, detail="Solo se admiten extensiones .md o .txt")
    
    ruta_original = validar_ruta_segura(area, equipo, archivo_original)

    if not os.path.exists(ruta_original):
        raise HTTPException(status_code=404, detail=f"El archivo '{archivo_original}' no existe en el servidor.")
    
    os.remove(ruta_original)
    
    nueva_ruta = validar_ruta_segura(area, equipo, file.filename)
    os.makedirs(os.path.dirname(nueva_ruta), exist_ok=True)
    with open(nueva_ruta, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"status": "success", "archivo_reemplazado": file.filename}

@api.delete("/api/conocimiento/delete")
def borrar_documento(area: str, equipo: str, archivo: str, username: str = Depends(verificar_credenciales)):
    ruta = validar_ruta_segura(area, equipo, archivo)
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Documento no localizado.")
    os.remove(ruta)
    return {"status": "success"}

# 3. Hilo de ejecución de Slack Bolt
def start_slack_bot():
    print("Iniciando motor de Slack Bolt en segundo plano...")
    SocketModeHandler(slack_app, app_token).connect()

if __name__ == "__main__":
    seed_database()
    
    # --- EJECUCIÓN DE LA POLÍTICA DE RETENCIÓN ---
    try:
        eliminados = aplicar_politica_retencion(dias=60)
        print(f"[MANTENIMIENTO] Política de retención (60 días) ejecutada. Hilos antiguos purgados: {eliminados}")
    except Exception as e:
        print(f"[ERROR] Fallo al ejecutar política de retención: {e}")

    bot_thread = threading.Thread(target=start_slack_bot, daemon=True)
    bot_thread.start()
    print("Iniciando plataforma web PayGuard Admin (Dashboard Seguro)...")
    uvicorn.run(api, host="0.0.0.0", port=8000)