import os
import ssl

# --- BYPASS PARA REDES CORPORATIVAS (Evita el bloqueo SSL del Firewall) ---
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context
# --------------------------------------------------------------------------

from datetime import datetime, timedelta
from core.database import SessionLocal, MensajeHilo
from slack_sdk.errors import SlackApiError
from apscheduler.schedulers.background import BackgroundScheduler

# NUEVAS IMPORTACIONES PARA LA IA
from core.rag_engine import buscar_contexto
from langchain_google_genai import ChatGoogleGenerativeAI

scheduler = BackgroundScheduler()
scheduler.start()

hilos_pendientes = {}

def register_listeners(app, default_channel):

    def enviar_recordatorio(channel_id, thread_ts, original_ts, client):
        if hilos_pendientes.get(thread_ts):
            bloques = [
                {"type": "section", "text": {"type": "mrkdwn", "text": "¡Hola de nuevo! 🕵️‍♂️ Pasaba a revisar si mi respuesta anterior solucionó tu problema o si necesitas que escale el caso."}},
                {"type": "actions", "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "✅ Sí, resuelto", "emoji": True}, "style": "primary", "action_id": "btn_ticket_resuelto", "value": original_ts},
                    {"type": "button", "text": {"type": "plain_text", "text": "🚨 Escalar con el equipo", "emoji": True}, "style": "danger", "action_id": "btn_ticket_escalar", "value": original_ts}
                ]}
            ]
            try:
                client.chat_postMessage(channel=channel_id, thread_ts=thread_ts, blocks=bloques, text="Recordatorio de PayGuard")
            except SlackApiError:
                pass

    @app.event("message")
    def handle_message_events(body, logger, client, say):
        event = body.get("event", {})
        if "bot_id" in event or event.get("subtype"):
            return
        
        channel_id = event.get("channel")
        user_id = event.get("user")
        text = event.get("text")
        ts = event.get("ts")
        thread_ts = event.get("thread_ts", ts)
        hoy = datetime.now()

        # A) REACCIÓN: "Ojitos"
        try:
            client.reactions_add(channel=channel_id, name="eyes", timestamp=ts)
        except SlackApiError:
            pass

        db = SessionLocal()
        try:
            db.add(MensajeHilo(thread_ts=thread_ts, remitente=f"<@{user_id}>", tipo="usuario", contenido=text, fecha=hoy.strftime("%Y-%m-%d"), hora=hoy.strftime("%H:%M")))
            db.commit()
        finally:
            db.close()

        # =====================================================================
        # B) RESPUESTA IA (RAG + GEMINI)
        # =====================================================================
        # 1. Buscamos en ChromaDB si hay algún documento que hable de esto
        contexto_rag = buscar_contexto(text)
        
        # 2. Inicializamos Gemini (Flash es la versión más rápida)
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
        
        # 3. Le damos las instrucciones maestras (System Prompt)
        prompt = f"""
        Eres 'PayGuard', un bot experto en soporte de ciberseguridad (SecOps).
        Responde al usuario de Slack de forma muy amable, profesional y concisa.
        
        CONTEXTO DE LA EMPRESA (Reglas de negocio):
        {contexto_rag if contexto_rag else "No hay documentos específicos para esta consulta. Responde con tus conocimientos generales de ciberseguridad."}
        
        PREGUNTA DEL USUARIO:
        {text}
        """
        
        try:
            respuesta_gemini = llm.invoke(prompt)
            respuesta_ia = respuesta_gemini.content
        except Exception as e:
            respuesta_ia = f"Ocurrió un error al procesar la IA: {str(e)}"
        # =====================================================================

        # C) BOTONES
        bloques = [
            {"type": "section", "text": {"type": "mrkdwn", "text": respuesta_ia}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "🕵️‍♂️ *¿Pude resolver tu problema?*"}},
            {"type": "actions", "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "✅ Sí, resuelto", "emoji": True}, "style": "primary", "action_id": "btn_ticket_resuelto", "value": ts},
                {"type": "button", "text": {"type": "plain_text", "text": "🚨 Escalar con el equipo", "emoji": True}, "style": "danger", "action_id": "btn_ticket_escalar", "value": ts}
            ]}
        ]

        say(blocks=bloques, text="Respuesta de PayGuard", thread_ts=thread_ts)

        hilos_pendientes[thread_ts] = True
        scheduler.add_job(enviar_recordatorio, 'date', run_date=datetime.now() + timedelta(minutes=1), args=[channel_id, thread_ts, ts, client])

        db = SessionLocal()
        try:
            db.add(MensajeHilo(thread_ts=thread_ts, remitente="PayGuard Bot", tipo="bot", contenido=respuesta_ia, fecha=hoy.strftime("%Y-%m-%d"), hora=hoy.strftime("%H:%M")))
            db.commit()
        finally:
            db.close()

    @app.action("btn_ticket_resuelto")
    def handle_resuelto(ack, body, client, logger):
        ack()
        channel_id = body["channel"]["id"]
        message_ts = body["message"]["ts"]
        user_id = body["user"]["id"]
        original_ts = body["actions"][0]["value"]
        thread_ts = body["message"].get("thread_ts", original_ts)
        hilos_pendientes[thread_ts] = False

        client.chat_update(channel=channel_id, ts=message_ts, blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": f"✅ <@{user_id}> ha marcado este incidente como *Resuelto*. ¡Excelente!"}}], text="Incidente resuelto.")
        try:
            client.reactions_add(channel=channel_id, name="white_check_mark", timestamp=original_ts)
        except SlackApiError:
            pass

    @app.action("btn_ticket_escalar")
    def handle_escalar(ack, body, client, logger):
        ack()
        channel_id = body["channel"]["id"]
        message_ts = body["message"]["ts"]
        user_id = body["user"]["id"]
        original_ts = body["actions"][0]["value"]
        thread_ts = body["message"].get("thread_ts", original_ts)
        hilos_pendientes[thread_ts] = False
        
        client.chat_update(channel=channel_id, ts=message_ts, blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": f"🚨 <@{user_id}> ha solicitado escalar el caso.\n\n⏳ *Conectando con Jira para crear el ticket...*"}}], text="Escalando incidente.")