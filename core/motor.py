"""
core/motor.py
Motor central unificado de IA para PayGuard Admin.
Orquesta el triage entre Access (🟣) e InfoSec (🟢) basándose en las bases de conocimiento.
Genera respuestas estructuradas usando Slack Block Kit con integración REAL de LLM.
"""

import os
import re
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from core.knowledge import buscar_en_conocimiento

# Forzamos la carga del .env antes de inicializar la clase
load_dotenv()

class MotorIA:
    def __init__(self):
        # Detecta si hay una API Key configurada en el .env
        self.api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.en_produccion = bool(self.api_key)
        
        if self.en_produccion:
            self.client = OpenAI(api_key=self.api_key)

    def generar_respuesta(
        self,
        agente_nombre: str,
        area: str,
        system_prompt: str,
        mensaje_usuario: str,
        user_id: str
    ) -> Dict[str, Any]:
        
        # 1. Búsqueda en los documentos físicos (RAG)
        analisis = buscar_en_conocimiento(area, mensaje_usuario)
        
        # Si NO hay API Key, usamos el simulador
        if not self.en_produccion:
            return self._simular_triage_secops(agente_nombre, system_prompt, analisis, mensaje_usuario, user_id)

        # =========================================================
        # MODO PRODUCCIÓN: GENERACIÓN CON LLM REAL (OpenAI)
        # =========================================================
        equipo = analisis["equipo"]
        emoji = analisis["emoji"]
        fragmentos = analisis["fragmentos"]
        
        codigo_error_match = re.search(r'\b(4\d{2}|5\d{2})\b', mensaje_usuario)
        codigo_error = codigo_error_match.group(1) if codigo_error_match else None

        contexto_rag = ""
        url_ticket = None
        
        if fragmentos:
            contexto_rag = "\n\n".join([f["texto"] for f in fragmentos])
            urls_encontradas = re.findall(r"https?://[^\s\)\>\"\'\]]+", contexto_rag)
            if urls_encontradas:
                # Limpiar el punto ortográfico u otros signos al final de la URL
                url_ticket = urls_encontradas[0].rstrip(".,;!?")
        else:
            contexto_rag = "No se encontró información en la base de conocimiento para esta consulta."

        prompt_interno = (
            f"{system_prompt}\n\n"
            f"REGLAS ESTRICTAS DE RESPUESTA:\n"
            f"1. Eres el agente {agente_nombre}.\n"
            f"2. Basa tu respuesta ÚNICAMENTE en la siguiente directiva de la base de conocimiento.\n"
            f"3. Responde al usuario de forma natural, explicando los pasos a seguir de manera concisa (máximo 2-3 párrafos).\n"
            f"4. NO saludes (el sistema ya lo hace en la cabecera).\n"
            f"5. NO incluyas las URLs en el texto si detectas que son de Jira (el sistema creará un botón automático).\n\n"
            f"--- INICIO DIRECTIVA RECUPERADA ---\n"
            f"{contexto_rag}\n"
            f"--- FIN DIRECTIVA RECUPERADA ---\n"
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", 
                messages=[
                    {"role": "system", "content": prompt_interno},
                    {"role": "user", "content": mensaje_usuario}
                ],
                temperature=0.3
            )
            respuesta_llm = response.choices[0].message.content.strip()
        except Exception as e:
            respuesta_llm = f"❌ *Error de conexión con el Motor de IA:* `{str(e)}`\nPor favor, notifica al equipo de SecOps."

        bloques = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hola <@{user_id}>, soy *{agente_nombre}* 🛡️.\nHe canalizado tu solicitud para el equipo de *{equipo}* {emoji}."
                }
            }
        ]

        if codigo_error:
            bloques.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⚠️ *Patrón detectado:* Se identificó el código de error HTTP/Sistema *{codigo_error}*."
                    }
                ]
            })

        bloques.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": respuesta_llm
            }
        })

        if url_ticket:
            bloques.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": f"🎫 Crear Ticket para {equipo}",
                            "emoji": True
                        },
                        "action_id": "click_jira",
                        "value": "jira_portal_link",
                        "url": url_ticket,
                        "style": "primary"
                    }
                ]
            })

        bloques.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "⏱️ _SLA estándar de atención: 3 días hábiles tras aprobaciones._"
                }
            ]
        })

        texto_fallback = f"Resolución de triage generada por IA para {equipo} {emoji}"
        return {"texto": texto_fallback, "bloques": bloques}

    def _simular_triage_secops(
        self,
        agente_nombre: str,
        system_prompt: str,
        analisis: Dict[str, Any],
        mensaje_usuario: str,
        user_id: str
    ) -> Dict[str, Any]:
        equipo = analisis["equipo"]
        emoji = analisis["emoji"]
        fragmentos = analisis["fragmentos"]
        codigo_error_match = re.search(r'\b(4\d{2}|5\d{2})\b', mensaje_usuario)
        codigo_error = codigo_error_match.group(1) if codigo_error_match else None

        if fragmentos:
            mejor_fragmento = fragmentos[0]["texto"]
            lineas = [l.strip() for l in mejor_fragmento.split("\n") if l.strip()]
            resumen_directiva = "\n".join(lineas[:6])
            
            # Extraer y limpiar URL
            urls_encontradas = re.findall(r"https?://[^\s\)\>\"\'\]]+", mejor_fragmento)
            url_ticket = urls_encontradas[0].rstrip(".,;!?") if urls_encontradas else None

            bloques = [
                {"type": "section", "text": {"type": "mrkdwn", "text": f"Hola <@{user_id}>, soy *{agente_nombre}* (Simulador offline) 🛡️.\nHe canalizado tu solicitud para el equipo de *{equipo}* {emoji}."}}
            ]
            if codigo_error:
                bloques.append({"type": "context", "elements": [{"type": "mrkdwn", "text": f"⚠️ *Patrón detectado:* Código de error *{codigo_error}*."}]})
            bloques.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Directiva oficial (`{analisis['archivo']}`):*\n> {resumen_directiva}"}})
            
            if url_ticket:
                bloques.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": f"🎫 Crear Ticket para {equipo}",
                                "emoji": True
                            },
                            "action_id": "click_jira",
                            "value": "jira_portal_link",
                            "url": url_ticket,
                            "style": "primary"
                        }
                    ]
                })
            
            bloques.append({"type": "context", "elements": [{"type": "mrkdwn", "text": "⏱️ _SLA estándar de atención: 3 días hábiles._"}]})
            return {"texto": "Resolución de triage (Simulador)", "bloques": bloques}

        bloques_fallback = [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"Hola <@{user_id}>, soy *{agente_nombre}* 🛡️.\n\nNo encontré un protocolo específico en la base de conocimiento para tu consulta."}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "Por favor indícame la herramienta o el sistema específico para canalizarte al formulario correcto."}]}
        ]
        if codigo_error:
            bloques_fallback.insert(1, {"type": "context", "elements": [{"type": "mrkdwn", "text": f"⚠️ *Nota:* Noté que mencionaste el error *{codigo_error}*."}]})
        return {"texto": "No se encontró protocolo.", "bloques": bloques_fallback}

motor_ia = MotorIA()