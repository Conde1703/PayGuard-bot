from core.logger import logger

def register_listeners(app, allowed_channel_id):
    @app.event("message")
    def handle_message_events(event, say):
        # Ignorar mensajes de bots y eventos especiales
        if event.get("bot_id") or event.get("subtype"):
            return

        # Ignorar si no es el canal permitido
        if allowed_channel_id and event.get("channel") != allowed_channel_id:
            return

        # Leer el mensaje y el usuario
        text = (event.get("text") or "").lower()
        user_id = event.get("user")

        # Detectar solicitudes relacionadas con VPN o FortiClient
        if "vpn" not in text and "forticlient" not in text:
            return

        # Registrar el evento en los logs
        logger.info(f"ALERTA SECOPS - Usuario: {user_id} reportó: '{text}'")

        # Construcción de interfaz con Block Kit
        bloques_mensaje = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hola <@{user_id}>, soy *PayGuard-bot DEV* 🛡️.\nHe detectado que tienes problemas con tu conexión (VPN/FortiClient).\n\n¿Cómo prefieres continuar?"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📖 Ver guía de solución",
                            "emoji": True
                        },
                        "value": "btn_guia_vpn",
                        "action_id": "action_ver_guia"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🎫 Abrir ticket Jira",
                            "emoji": True
                        },
                        "value": "btn_ticket_jira",
                        "action_id": "action_abrir_ticket"
                    }
                ]
            }
        ]

        # Responder dentro del hilo
        say(
            text="Alerta de SecOps detectada", 
            blocks=bloques_mensaje,
            thread_ts=event.get("ts")
        )

    # --- NUEVO: Manejadores de botones (Actions) ---
    
    @app.action("action_ver_guia")
    def handle_ver_guia(ack, body, say):
        # 1. Acuse de recibo obligatorio para quitar el warning en Slack
        ack() 
        
        # 2. Extraer datos del evento
        user_id = body["user"]["id"]
        # Mantener la respuesta en el mismo hilo original
        thread_ts = body["message"]["thread_ts"] if "thread_ts" in body["message"] else body["message"]["ts"]
        
        # 3. Registrar en logs
        logger.info(f"INTERACCIÓN - Usuario {user_id} solicitó ver la guía de VPN.")
        
        # 4. Responder al usuario
        say(
            text=f"<@{user_id}>, revisa este artículo de nuestra base de conocimientos SecOps: *[Enlace simulado a Confluence/Notion]*",
            thread_ts=thread_ts
        )

    @app.action("action_abrir_ticket")
    def handle_abrir_ticket(ack, body, say):
        ack()
        user_id = body["user"]["id"]
        thread_ts = body["message"]["thread_ts"] if "thread_ts" in body["message"] else body["message"]["ts"]
        
        logger.info(f"INTERACCIÓN - Usuario {user_id} solicitó abrir un ticket en Jira.")
        
        say(
            text=f"Entendido <@{user_id}>. Estoy preparando la conexión con Jira... *(Módulo de automatización en construcción 🚧)*",
            thread_ts=thread_ts
        )