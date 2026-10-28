# **Base de Conocimiento Global - Soporte de Accesos y VPN**

Este documento contiene la información esencial, políticas, resolución de problemas y catálogo de servicios para gestionar la VPN, accesos a URLs y herramientas de Google Workspace.

## **1. Soporte y Configuración VPN RappiPay (SI-PRO-17-PAY)**

**Contexto:** Los problemas de VPN son el motivo más frecuente de soporte (39 repeticiones en el último mes analizado), superando a Zscaler y GMAIL.

### **1.1 Instalación del Cliente**
El equipo de IT entrega el dispositivo con el agente de FortiClient instalado.
* **En caso de requerir instalación (Mac):** El usuario debe abrir la aplicación "Portal de autoservicio" (Rappi IT Department). En la lista de "Apps", debe buscar "Forti cliente MAC Rappi SAS_25". En la columna "Acción" aparecerá la opción "Reinstalar" y en comentarios "Installation successful".  
* Si hay problemas con este paso, se debe redirigir al usuario al canal de Slack #it-support.

### **1.2 Configuración de Conexión**
* **Registro Zero Trust:** En la barra lateral azul de FortiClient, el usuario debe ir a "ZERO TRUST TELEMETRY". Si el panel derecho (Register with Zero Trust Fabric) está en blanco, debe ingresar ems.security.rappipay.com:8013 en el campo de texto y presionar el botón "Conectar". El estado cambiará a "Conectado".  
* **Conexión VPN:** En el menú lateral izquierdo, seleccionar "ACCESO REMOTO". En el panel derecho, usar el menú desplegable "Nombre de VPN" para elegir el entorno (Ej. VPN RAPPI DEV, VPN RAPPIPAY PROD, etc.), ingresar usuario y contraseña, y presionar "Conectar".  
* **Agregar conexión manual:** Si la VPN no aparece en la lista, hacer clic en el ícono de tres líneas horizontales (a la derecha del campo "Nombre de VPN") y seleccionar "Adicionar una nueva conexión". Usar los siguientes datos según corresponda:  
  * **Rappi PROD:** vpn.rappi.com | Puerto 10443
  * **Rappi DEV:** vpn.dev.rappi.com | Puerto 10443
  * **RappiPay PROD:** fortipro.rappipay.com | Puerto 10443
  * **RappiPay DEV:** fortidev.rappipay.com | Puerto 10443
  * **Rappi PCI:** vpn.rappipaypci.com | Puerto 10443

### **1.3 Solicitud de Acceso a VPN y Configuración 2FA**
Para conectarse a la VPN de producción, es obligatorio solicitar el acceso por los canales oficiales y tener configurado el Doble Factor de Autenticación (2FA).

**Configuración del FortiToken (2FA):**
1. Descargar la app "FortiToken Mobile" en el celular. Si ya hay un token viejo, tocar "Manage" (arriba a la derecha), luego el ícono rojo y finalmente "Delete" para borrarlo.  
2. Ingresar desde el navegador web a: https://2fa.security.rappi.com/portal/selfservice/self-service-token-policy e iniciar sesión con usuario y contraseña de AD.  
3. En el menú lateral izquierdo rojo, ir a "Usuario" > "Registro de Token".  
4. Seleccionar la opción "FortiToken Mobile", elegir "Correo Electrónico" como método de entrega y presionar "Aceptar".  
5. Llegará un correo con el asunto "Activation on Rappi Token Self-Service" que incluye un código QR.  
6. En la app móvil, tocar "Scan Barcode" (abajo a la izquierda) y escanear el QR de la pantalla para generar el nuevo código de 6 dígitos.

### **1.4 Políticas y Restablecimiento de Contraseña**
Para cambiar o restablecer la contraseña, ingresar al Portal de Autoservicio y usar los botones "CHANGE PASSWORD" (verde) o "RESET PASSWORD" (azul). Se debe usar el usuario sin el "@rappi.com". **Políticas obligatorias:**
* Al menos 1 minúscula, 1 mayúscula, 1 número y 1 símbolo (prohibidos el "@" y el "%").  
* Entre 12 y 40 caracteres.  
* No puede ser ninguna de las últimas 4 contraseñas usadas.

### **1.5 Troubleshooting VPN**
* **Error "No cumple con los requerimientos de ZTNA" o "El servidor podría no estar disponible":** Reportar en #rappipay_secops_on_schedule etiquetando a @securityaccess_rappipay.  
* **Error "Login failed. Permission denied":** Verificar si el token expiró (escribir el nuevo código de la app), si la contraseña venció, o si realmente tiene los accesos aprobados a la VPN.  
* **Prerrequisitos:** Para que la VPN funcione, el equipo debe tener cifrado de disco, Falcon/Cortex activo, SO actualizado, Zscaler y EMS instalados.

## **2. Protocolo de Soporte: Problemas de Acceso a una URL**
Cuando un usuario reporta que no puede acceder a un enlace o página web específica, se deben seguir estos pasos de validación antes de escalar:
1. **Limpieza y Entorno:** Solicitar al usuario que borre caché y cookies del navegador. Si no funciona, debe intentar abrir la URL en una ventana de Incógnito/Privada, y posteriormente en un navegador diferente (Ej. Edge o Safari).  
2. **Validación de Red:** Preguntar si la URL es interna y requiere VPN. Si es así, pedirle que confirme que FortiClient está "Conectado".  
3. **Validación de Permisos y Tickets:** Solicitar el número de ticket donde el usuario pidió explícitamente el acceso por red a esa URL.  
   * *Si no tiene ticket:* Indicarle que debe crearlo en: https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/4336/create/8286. Informar que una vez obtenidas todas las aprobaciones gerenciales, el ticket tiene un SLA de 3 días para ser ejecutado.  
   * *Si tiene ticket y está "Resuelto" (pero sigue sin acceso):* Escalar inmediatamente al equipo Security Access RappiPay, indicando: "Por favor verifiquen el acceso a esta URL desde el AD (Active Directory)".

## **3. Catálogo de Servicios: Gmail y Google Workspace**
* 🔵 **Restablecimiento de Credenciales y Códigos de Verificación (2FA)**  
  https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/4346/create/8328
* 🔵 **Transferencia de Archivos Individuales (Internos)**  
  https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/4346/create/8330
* 🔵 **Transferencia de Google Drive (Externos)**  
  https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/4346/create/8329
* 🔵 **Creación de Correos para Externos**  
  https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/4346/create/8326
* 🔵 **Acceso a Buzón de Usuario Desvinculado (Offboarding)**  
  https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/4346/create/8324
* 🔵 **Creación o Adición de Nuevo Grupo**  
  https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/4346/create/8360

## **4. Catálogo de Servicios: Jira y Confluence**
* 🔵 **Solicitud de Accesos a Jira y Confluence**  
  https://rappidev.atlassian.net/helpcenter/rappipay/portal/1190/group/4357/create/8356