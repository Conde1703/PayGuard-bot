# Base de Conocimiento - Soporte y Seguridad de la Información (InfoSec)

Bienvenido a la base de conocimiento de soporte. Este documento contiene la información esencial sobre nuestras políticas de seguridad, gestión de accesos y el catálogo de servicios de InfoSec para canalizar tus requerimientos.

---

## 1. Políticas de Seguridad y Prevención de Pérdida de Datos (DLP)

Para nuestra compañía, la protección de la información es una prioridad. Nuestra estrategia de Prevención de Pérdida de Datos (DLP) está diseñada para salvaguardar la confidencialidad de los activos de información, mitigando los riesgos de fuga o exposición no autorizada.[cite: 1]

### 1.1 Vectores de Protección
Monitoreamos y protegemos la información a través de tres canales principales:
* **Navegación Web (Agente DLP):** Supervisión continua del tráfico web y la transferencia de datos a través de navegadores.[cite: 1]
* **Endpoints (XDR):** Control contra la exfiltración en puntos finales y dispositivos físicos.[cite: 1] Como medida preventiva, la política restringe el almacenamiento masivo externo, permitiendo exclusivamente el uso de periféricos de entrada esenciales (como teclados o mouses vía USB y Bluetooth) para no afectar la productividad del usuario.[cite: 8]
* **Correo Corporativo:** Inspección del flujo de información en el servicio de email para asegurar el cumplimiento normativo.[cite: 1][cite: 10]

### 1.2 Estrategia de Monitoreo
Nuestras herramientas no buscan bloquear el trabajo diario, sino proteger nuestros activos críticos. Por ello, el sistema opera bajo una estrategia de "Reducción de Fricción Operativa".[cite: 2] 
* Se utilizan umbrales de detección basados en el volumen de datos.[cite: 2] 
* Esto permite diferenciar entre un error operativo legítimo y un intento de extracción masiva o anomalía.[cite: 2] 

**¿Qué tipo de información protegemos automáticamente?**
* **Datos Financieros:** Información regulada por el estándar PCI-DSS, incluyendo números de tarjetas de crédito y débito.[cite: 2][cite: 10]
* **Datos Personales (PII):** Información que identifica de manera única a individuos (empleados o clientes), como documentos de identidad (CC, DNI, CPF, CDC), correos electrónicos y teléfonos, con reglas adaptadas a las regulaciones de cada país.[cite: 2][cite: 10][cite: 25]
* **Datos Técnicos:** Información interna de infraestructura, como envíos masivos de direcciones IP.[cite: 10]

---

## 2. Gestión de Accesos a Repositorios (GitHub)

El acceso al código fuente y repositorios se maneja estrictamente a través de la pertenencia a equipos (Teams).
* **Asignación Automática:** Todo usuario que sea agregado a un equipo obtendrá automáticamente los accesos y permisos correspondientes a todos los repositorios que sean propiedad de dicho equipo.[cite: 13]
* **Permisos de Escritura:** El equipo que figure como propietario de un repositorio tendrá permisos de escritura (Write), lo que le permite a sus miembros leer, clonar, subir cambios (push) y gestionar pull requests.[cite: 14]
* **Protección del Código (CODEOWNERS):** Para proteger la integridad de nuestros desarrollos, utilizamos restricciones mediante archivos CODEOWNERS.[cite: 14]
* **Aprobación de Cambios:** Este archivo define qué equipo es el responsable oficial de revisar el código; por lo tanto, cualquier cambio propuesto requerirá obligatoriamente la revisión y aprobación del equipo asignado antes de poder integrarse.[cite: 14]

*(Nota: Si requieres acceso a un repositorio, debes solicitar a tu Engineering Lead que te agregue al equipo correspondiente mediante los canales oficiales).*

---

## 3. Catálogo de Servicios y Solicitudes InfoSec (Ticktera)

Si necesitas solicitar un acceso, reportar una alerta o pedir una excepción, por favor utiliza los siguientes formularios. **Haz clic en el enlace o cópialo en tu navegador para generar tu ticket:**

### Categoría: InfoSec
**URL de la sección:** https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/1963

* 🟢 **Github - Ticket informativo Alta/Baja/Modificacion**
  * *Descripción:* Ticket informativo Alta/Baja/Modificacion en Github Rpp
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1315
* 🟢 **Github - ABM team en repositorios RPP-CO**
  * *Descripción:* Ticket para solicitar que se agregue un team a un repo en RRP-CO
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1316
* 🟢 **Github - ABM Github apps**
  * *Descripción:* Formulario para solicitar Acceso/Modificacion a una Github App
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1317
* 🟢 **Alertas PaloAlto DLP**
  * *Descripción:* Formulario para dejar registro de alertas mensuales de Zscaler
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1318
* 🟢 **Alertas Cortex**
  * *Descripción:* Formulario para dejar registro de alertas mensuales de Cortex
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1319
* 🟢 **Creación Usuario externo en tenant Okta Rpp**
  * *Descripción:* Solicitud de creación de usuario externo Rpp en Okta
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1320
* 🟢 **Solicitud Aplicación AI & ML**
  * *Descripción:* Solicitud para la creación o implementación de aplicaciones de IA y ML.
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1321
* 🟢 **Liberación de correos en cuarentena**
  * *Descripción:* Formulario para liberar correos en Cuarentena de Gmail
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1322
* 🟢 **Whitelist/Blacklist de Dominios**
  * *Descripción:* Incluir un dominio de proveedor/cuenta de correo en lista blanca o negra.
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1323
* 🟢 **Global Protect - Soporte o excepción de dominio**
  * *Descripción:* Soporte o excepción de un dominio en whitelist de Zscaler
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1324
* 🟢 **Zscaler - ABM usuarios**
  * *Descripción:* Formulario para solicitar Alta, Modificación y Baja a Zscaler.
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1325
* 🟢 **Zscaler - Excepción/Deslogueo**
  * *Descripción:* Excepción de un usuario para salir de Zscaler
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1326
* 🟢 **Zscaler - Excepción DLP**
  * *Descripción:* Excepción de un usuario del DLP
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1327
* 🟢 **Soporte Cortex EDR**
  * *Descripción:* Soporte o solicitudes de Cortex
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1328
* 🟢 **Excepción Bloqueo USB y Bluetooth Cortex**
  * *Descripción:* Soporte o solicitudes sobre excepciones o bloqueos de USB en Cortex EDR
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1329
* 🟢 **Solicitar informe o requerimiento de Auditoría**
  * *Descripción:* ¿Necesitas ayuda con un informe o análisis de datos? Envía una solicitud aquí.
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1330
* 🟢 **Soporte Infosec**
  * *Descripción:* Solicitud de soporte o requerimiento en general
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1331
* 🟢 **Excepciones**
  * *Descripción:* Pedido general
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1332
* 🟢 **AWS - Creación de cuentas**
  * *Descripción:* Formulario para solicitar un nueva cuenta de AWS
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1333
* 🟢 **Control de cambios Infosec**
  * *Descripción:* Registro de control de cambios herramientas Infosec
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1334
* 🟢 **GSuite - Bloqueo por ausencias**
  * *Descripción:* Solicitud para bloqueo por ausencias en GSuite
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1335

### Categoría: AWS (Accesos y Roles)
**URL de la sección:** https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/4321

* 🟣 **AWS - ABM Usuario de Servicio**
  * *Descripción:* Formulario para solicitud de usuarios de servicios de AWS
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1188
* 🟣 **AWS - ABM Roles**
  * *Descripción:* Formulario para solicitud de roles en AWS
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1189
* 🟣 **AWS - ABM Usuario Personal**
  * *Descripción:* Formulario para solicitud de usuarios personales de AWS
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/create/1190

### Categoría: Data & Bases de Datos (Snowflake / Airflow)
**URL de la sección:** https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/4332

* 🟣 **Seteo credenciales usuarios de servicio Snowflake**
  * *Descripción:* Formulario para solicitar seteo de credenciales de usuarios de servicio en Snowflake
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/group/4332/create/4
* 🟣 **Seteo credenciales conexión Airflow**
  * *Descripción:* Formulario para solicitar seteo de credenciales en una conexión
  * *URL:* https://rappidev.atlassian.net/servicedesk/customer/portal/1190/group/4332/create/6

### Categoría: Herramientas N8N & Automatización
**URL de la sección:** https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/5614

* 🟢 **Paso a producción proyecto N8N**
  * *Descripción:* Paso a producción proyecto N8N
  * *URL:* https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/5614/create/13013
* 🟢 **Restablecer contraseña N8N**
  * *Descripción:* Solicitud de restablecimiento contraseña N8N
  * *URL:* https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/5614/create/13014
* 🟢 **ABM Langfuse**
  * *Descripción:* Formulario para solicitar ABM en Langfuse
  * *URL:* https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/5614/create/13015
* 🟢 **ABM LiteLLM**
  * *Descripción:* Formulario para solicitar ABM en LiteLLM
  * *URL:* https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/5614/create/13016
* 🟢 **Usuario N8N**
  * *Descripción:* Solicitud de acceso o usuario para N8N
  * *URL:* https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/5614/create/13017