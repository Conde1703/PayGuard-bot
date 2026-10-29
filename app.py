import os
import ssl
import shutil
import threading
from datetime import datetime
from core.rag_engine import indexar_documentos

# =========================================================================
# 1. BYPASS SSL GLOBAL (Soluciona el error CERTIFICATE_VERIFY_FAILED)
# =========================================================================
ssl._create_default_https_context = ssl._create_unverified_context

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.web import WebClient

from core.database import SessionLocal, init_db, Agente, MensajeHilo, Secreto, encriptar
from core.slack_events import register_listeners

load_dotenv()

# =========================================================================
# 2. INICIALIZACIÓN BASE DE DATOS Y FASTAPI
# =========================================================================
init_db()

fastapi_app = FastAPI(title="PayGuard Admin API")

os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# =========================================================================
# 3. CONFIGURAR SLACK Y SOCKETS
# =========================================================================
ssl_context = ssl._create_unverified_context()

web_client = WebClient(
    token=os.getenv("SLACK_BOT_TOKEN"),
    ssl=ssl_context
)

slack_app = App(client=web_client)

allowed_channel = os.getenv("SLACK_CHANNEL_ID")
register_listeners(slack_app, allowed_channel)

def run_slack_socket():
    app_token = os.getenv("SLACK_APP_TOKEN")
    if app_token:
        handler = SocketModeHandler(slack_app, app_token)
        handler.client.web_client.ssl = ssl_context
        handler.connect()

threading.Thread(target=run_slack_socket, daemon=True).start()

# =========================================================================
# 4. RUTAS DE LA VISTA PRINCIPAL (DASHBOARD)
# =========================================================================
@fastapi_app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    db = SessionLocal()
    try:
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        
        agentes = db.query(Agente).all()
        agentes_count = len([a for a in agentes if a.activo])
        
        hilos_totales = db.query(MensajeHilo.thread_ts).distinct().all()
        total_incidentes = len(hilos_totales)
        
        incidentes_hoy = db.query(MensajeHilo.thread_ts).filter(
            MensajeHilo.fecha == hoy_str,
            MensajeHilo.tipo == "usuario"
        ).distinct().count()

        usuarios_unicos = db.query(MensajeHilo.remitente).filter(
            MensajeHilo.tipo == "usuario"
        ).distinct().count()

        documentos = []
        base_dir = "knowledge"
        if os.path.exists(base_dir):
            for area in os.listdir(base_dir):
                area_path = os.path.join(base_dir, area)
                if os.path.isdir(area_path):
                    for equipo in os.listdir(area_path):
                        equipo_path = os.path.join(area_path, equipo)
                        if os.path.isdir(equipo_path):
                            for archivo in os.listdir(equipo_path):
                                if archivo.endswith((".md", ".txt")):
                                    file_path = os.path.join(equipo_path, archivo)
                                    stat = os.stat(file_path)
                                    documentos.append({
                                        "archivo": archivo,
                                        "area": area,
                                        "equipo": equipo,
                                        "tamano": round(stat.st_size / 1024, 1),
                                        "modificacion": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                                    })

        mensajes_iniciales = db.query(MensajeHilo).filter(
            MensajeHilo.tipo == "usuario"
        ).order_by(MensajeHilo.id.desc()).all()

        vistos = set()
        interacciones = []
        for m in mensajes_iniciales:
            if m.thread_ts not in vistos:
                vistos.add(m.thread_ts)
                tiene_jira = db.query(MensajeHilo).filter(
                    MensajeHilo.thread_ts == m.thread_ts,
                    MensajeHilo.contenido.like("%Jira%")
                ).first() is not None

                interacciones.append({
                    "thread_ts": m.thread_ts,
                    "hora": m.hora,
                    "fecha": m.fecha,
                    "remitente": m.remitente,
                    "contenido": m.contenido,
                    "tiene_ticket": tiene_jira
                })

        bot_status = "En línea (Producción)" if os.getenv("GEMINI_API_KEY") else "En línea y conectado"

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "bot_status": bot_status,
                "agentes_count": agentes_count,
                "incidentes_hoy": incidentes_hoy,
                "total_incidentes": total_incidentes,
                "usuarios_unicos": usuarios_unicos,
                "default_channel": allowed_channel or "C08EVE7EBDC",
                "documentos": documentos,
                "agentes": agentes,
                "interacciones": interacciones
            }
        )
    finally:
        db.close()

# =========================================================================
# ENDPOINTS REST: GESTIÓN DE AGENTES Y ESTADÍSTICAS
# =========================================================================
@fastapi_app.post("/api/agentes")
async def crear_agente(payload: dict):
    db = SessionLocal()
    try:
        nuevo = Agente(
            nombre=payload.get("nombre"),
            area=payload.get("area"),
            canal_slack=payload.get("canal_slack"),
            descripcion=payload.get("descripcion"),
            prompt_maestro=payload.get("prompt_maestro"),
            activo=True
        )
        db.add(nuevo)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()

@fastapi_app.patch("/api/agentes/{agente_id}/toggle")
def toggle_agente(agente_id: int):
    db = SessionLocal()
    try:
        agente = db.query(Agente).filter(Agente.id == agente_id).first()
        if not agente:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        agente.activo = not agente.activo
        db.commit()
        return {"status": "ok", "activo": agente.activo}
    finally:
        db.close()

@fastapi_app.get("/api/metricas/agente/{agente_id}")
def obtener_metricas_agente(agente_id: str):
    db = SessionLocal()
    try:
        hoy_str = datetime.now().strftime("%Y-%m-%d")

        if agente_id == "todos":
            hilos_query = db.query(MensajeHilo.thread_ts).distinct()
        else:
            agente = db.query(Agente).filter(Agente.id == int(agente_id)).first()
            if not agente:
                return {"error": "Agente no encontrado"}
            hilos_query = db.query(MensajeHilo.thread_ts).filter(
                MensajeHilo.remitente == agente.nombre,
                MensajeHilo.tipo == "bot"
            ).distinct()

        hilos_ids = [h[0] for h in hilos_query.all()]
        total_historico = len(hilos_ids)

        incidentes_hoy = db.query(MensajeHilo.thread_ts).filter(
            MensajeHilo.thread_ts.in_(hilos_ids),
            MensajeHilo.fecha == hoy_str,
            MensajeHilo.tipo == "usuario"
        ).distinct().count() if hilos_ids else 0

        usuarios_unicos = db.query(MensajeHilo.remitente).filter(
            MensajeHilo.thread_ts.in_(hilos_ids),
            MensajeHilo.tipo == "usuario"
        ).distinct().count() if hilos_ids else 0

        mensajes_iniciales = db.query(MensajeHilo).filter(
            MensajeHilo.thread_ts.in_(hilos_ids),
            MensajeHilo.tipo == "usuario"
        ).order_by(MensajeHilo.id.desc()).all() if hilos_ids else []

        hilos_vistos = set()
        incidentes_lista = []
        for m in mensajes_iniciales:
            if m.thread_ts not in hilos_vistos:
                hilos_vistos.add(m.thread_ts)
                tiene_jira = db.query(MensajeHilo).filter(
                    MensajeHilo.thread_ts == m.thread_ts,
                    MensajeHilo.contenido.like("%Jira%")
                ).first() is not None

                incidentes_lista.append({
                    "thread_ts": m.thread_ts,
                    "hora": m.hora,
                    "fecha": m.fecha,
                    "remitente": m.remitente,
                    "contenido": m.contenido,
                    "tiene_ticket": tiene_jira
                })

        return {
            "incidentes_hoy": incidentes_hoy,
            "total_historico": total_historico,
            "usuarios_unicos": usuarios_unicos,
            "incidentes": incidentes_lista
        }
    finally:
        db.close()

# =========================================================================
# ENDPOINTS REST: GESTOR DE CONOCIMIENTO (RAG)
# =========================================================================
@fastapi_app.post("/api/conocimiento/upload")
async def upload_documento(
    area: str = Form(...),
    equipo: str = Form(...),
    file: UploadFile = File(...)
):
    ruta_dir = os.path.join("knowledge", area, equipo)
    os.makedirs(ruta_dir, exist_ok=True)
    destino = os.path.join(ruta_dir, file.filename)
    with open(destino, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    indexar_documentos() # <--- REINDEXA LA BASE VECTORIAL
    return {"status": "ok", "filename": file.filename}

@fastapi_app.post("/api/conocimiento/replace")
async def replace_documento(
    area: str = Form(...),
    equipo: str = Form(...),
    archivo_original: str = Form(...),
    file: UploadFile = File(...)
):
    ruta_dir = os.path.join("knowledge", area, equipo)
    archivo_viejo = os.path.join(ruta_dir, archivo_original)
    if os.path.exists(archivo_viejo):
        os.remove(archivo_viejo)

    os.makedirs(ruta_dir, exist_ok=True)
    destino = os.path.join(ruta_dir, file.filename)
    with open(destino, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    indexar_documentos() # <--- REINDEXA LA BASE VECTORIAL
    return {"status": "ok"}

@fastapi_app.delete("/api/conocimiento/delete")
def delete_documento(area: str, equipo: str, archivo: str):
    ruta_archivo = os.path.join("knowledge", area, equipo, archivo)
    if os.path.exists(ruta_archivo):
        os.remove(ruta_archivo)
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Archivo no encontrado")

# =========================================================================
# ENDPOINTS REST: VISOR DE HILOS
# =========================================================================
@fastapi_app.get("/api/hilos/{thread_ts}")
def obtener_hilo(thread_ts: str):
    db = SessionLocal()
    try:
        mensajes = db.query(MensajeHilo).filter(
            MensajeHilo.thread_ts == thread_ts
        ).order_by(MensajeHilo.id.asc()).all()

        return [
            {
                "remitente": m.remitente,
                "tipo": m.tipo,
                "contenido": m.contenido,
                "hora": m.hora,
                "fecha": m.fecha
            }
            for m in mensajes
        ]
    finally:
        db.close()

# =========================================================================
# ENDPOINTS REST: GESTIÓN DE SECRETOS (CREDENCIALES CIFRADAS)
# =========================================================================
@fastapi_app.get("/api/secretos")
def obtener_secretos(area: str = None):
    """Retorna los secretos filtrados por área, o todos si es Global."""
    db = SessionLocal()
    try:
        query = db.query(Secreto)
        if area and area != "Global" and area != "todos":
            query = query.filter(Secreto.area == area)
            
        secretos = query.order_by(Secreto.id.desc()).all()
        return [{"id": s.id, "clave": s.clave, "area": s.area} for s in secretos]
    finally:
        db.close()

@fastapi_app.post("/api/secretos")
def guardar_secreto(payload: dict):
    db = SessionLocal()
    try:
        clave = payload.get("clave")
        valor = payload.get("valor")
        area = payload.get("area", "Global")
        
        if not clave or not valor:
            raise HTTPException(status_code=400, detail="Clave y valor requeridos")

        secreto_existente = db.query(Secreto).filter(Secreto.clave == clave).first()
        if secreto_existente:
            secreto_existente.valor_cifrado = encriptar(valor)
            secreto_existente.area = area
        else:
            nuevo_secreto = Secreto(
                clave=clave, 
                valor_cifrado=encriptar(valor),
                area=area
            )
            db.add(nuevo_secreto)
            
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()

@fastapi_app.delete("/api/secretos/{clave}")
def eliminar_secreto(clave: str):
    db = SessionLocal()
    try:
        db.query(Secreto).filter(Secreto.clave == clave).delete()
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:fastapi_app", host="0.0.0.0", port=8000, reload=True)