from datetime import datetime
from core.logger import logger
from core.database import SessionLocal, Agente, MensajeHilo
from core.motor import motor_ia 

def guardar_mensaje(thread_ts: str, remitente: str, tipo: str, contenido: str):
    """Registra cada turno de conversación en SQLite para auditoría y visualización web"""
    ahora = datetime.now()
    db = SessionLocal()
    try:
        nuevo_mensaje = MensajeHilo(
            thread_ts=thread_ts,
            remitente=remitente,
            tipo=tipo,
            contenido=contenido,
            fecha=ahora.strftime("%Y-%m-%d"),
            hora=ahora.strftime("%H:%M:%S")
        )
        db.add(nuevo_mensaje)
        db.commit()
    finally:
        db.close()

def obtener_agente_para_canal(canal_id: str):
    """
    Sistema de Enrutamiento Dinámico:
    1. Busca un agente activo asignado específicamente a este canal.
    2. Si no hay ninguno específico, asigna el primer agente activo disponible.
    """
    db = SessionLocal()
    try:
        # Prioridad 1: Agente asignado a este canal específico
        agente = db.query(Agente).filter(
            Agente.canal_slack == canal_id,
            Agente.activo == True
        ).first()

        # Prioridad 2: Si el canal tiene agentes registrados pero están pausados
        if not agente:
            agente_pausado = db.query(Agente).filter(
                Agente.canal_slack == canal_id,
                Agente.activo == False
            ).first()
            if agente_pausado:
                return agente_pausado, False

        # Prioridad 3: Primer agente activo por defecto
        if not agente:
            agente = db.query(Agente).filter(Agente.activo == True).first()

        return agente, True if agente and agente.activo else False
    finally:
        db.close()

def register_listeners(app, allowed_channel_id):
    @app.event("message")
    def handle_message_events(event, say):
        # Descartar mensajes generados por bots o del sistema
        if event.get("bot_id") or event.get("subtype"):
            return

        canal_actual = event.get("channel")
        text = event.get("text") or ""
        user_id = event.get("user")
        ts = event.get("ts")

        # 1. ENRUTAMIENTO DINÁMICO
        agente, esta_activo = obtener_agente_para_canal(canal_actual)

        # Si no hay agentes en el sistema
        if not agente:
            logger.info(f"SOLICITUD IGNORADA - No hay agentes configurados para canal: {canal_actual}")
            return

        # Registrar la pregunta del usuario en el hilo
        guardar_mensaje(thread_ts=ts, remitente=f"Usuario ({user_id})", tipo="usuario", contenido=text)

        # 2. VALIDAR ESTADO OPERATIVO (Gobernanza desde PayGuard Admin)
        if not esta_activo:
            mensaje_bloqueo = (
                f"⚠️ Hola <@{user_id}>, el *{agente.nombre}* (*{agente.area}*) se encuentra "
                f"actualmente *inactivo* en PayGuard Admin. Contacta a un administrador para reactivarlo."
            )
            logger.info(f"SOLICITUD DENEGADA - Agente '{agente.nombre}' inactivo. Usuario: {user_id}")
            guardar_mensaje(thread_ts=ts, remitente=agente.nombre, tipo="bot", contenido=mensaje_bloqueo)
            say(text=mensaje_bloqueo, thread_ts=ts)
            return

        # 3. PROCESAMIENTO CON EL MOTOR CENTRAL DE IA
        logger.info(f"EJECUCIÓN AGENTE - Enrutado a '{agente.nombre}' ({agente.area}) para usuario: {user_id}")
        
        resultado = motor_ia.generar_respuesta(
            agente_nombre=agente.nombre,
            area=agente.area,
            system_prompt=agente.prompt_maestro or "",
            mensaje_usuario=text,
            user_id=user_id
        )

        # 4. ENTREGA DE RESPUESTA Y AUDITORÍA
        guardar_mensaje(thread_ts=ts, remitente=agente.nombre, tipo="bot", contenido=resultado["texto"])

        if resultado.get("bloques"):
            say(text=resultado["texto"], blocks=resultado["bloques"], thread_ts=ts)
        else:
            say(text=resultado["texto"], thread_ts=ts)

    # ====================================================================
    # LISTENERS PARA BOTONES DE ACCIÓN INTERACTIVA (BLOCK KIT ACTIONS)
    # ====================================================================
    
    @app.action("click_jira")
    def handle_click_jira(ack, body, say):
        ack() 
        user_id = body["user"]["id"]
        thread_ts = body["message"].get("thread_ts") or body["message"]["ts"]
        logger.info(f"INTERACCIÓN - Usuario {user_id} hizo clic en el botón de Jira.")
        
        respuesta = f"✅ <@{user_id}>, fuiste redirigido al portal de Jira Service Desk. Si necesitas más ayuda con este incidente, indícalo en este hilo."
        guardar_mensaje(thread_ts=thread_ts, remitente="PayGuard-bot SecOps", tipo="bot", contenido=respuesta)
        say(text=respuesta, thread_ts=thread_ts)

    @app.action("action_ver_guia")
    def handle_ver_guia(ack, body, say):
        ack()
        user_id = body["user"]["id"]
        thread_ts = body["message"].get("thread_ts") or body["message"]["ts"]
        logger.info(f"INTERACCIÓN - Usuario {user_id} solicitó guía de conectividad.")
        respuesta = f"<@{user_id}>, revisa el manual oficial de conexión segura: [Base de Conocimientos SecOps]"
        guardar_mensaje(thread_ts=thread_ts, remitente="PayGuard-bot SecOps", tipo="bot", contenido=respuesta)
        say(text=respuesta, thread_ts=thread_ts)

    @app.action("action_abrir_ticket")
    def handle_abrir_ticket(ack, body, say):
        ack()
        user_id = body["user"]["id"]
        thread_ts = body["message"].get("thread_ts") or body["message"]["ts"]
        logger.info(f"INTERACCIÓN - Usuario {user_id} solicitó escalamiento a Jira.")
        respuesta = f"Entendido <@{user_id}>. Creando pre-ticket en cola SecOps... *(Integración de Jira desacoplada en preparación 🚧)*"
        guardar_mensaje(thread_ts=thread_ts, remitente="PayGuard-bot SecOps", tipo="bot", contenido=respuesta)
        say(text=respuesta, thread_ts=thread_ts)