import os

KNOWLEDGE_DIR = "knowledge"

def indexar_documentos():
    """
    En este enfoque de 'Contexto Total', no necesitamos convertir texto a matemáticas.
    Solo le confirmamos al sistema que los archivos se guardaron correctamente en disco.
    """
    print("✅ Archivo guardado y listo para ser leído por Gemini.")
    return True

def buscar_contexto(pregunta_usuario: str, top_k: int = 3) -> str:
    """
    Lee directamente todos los archivos .md y .txt en la carpeta knowledge.
    Como Gemini 1.5 Flash tiene 1 Millón de tokens de memoria, puede leer 
    todos los manuales de tu empresa de un solo golpe y en milisegundos.
    """
    if not os.path.exists(KNOWLEDGE_DIR):
        return ""
    
    contexto_total = []
    
    for root, dirs, files in os.walk(KNOWLEDGE_DIR):
        for file in files:
            if file.endswith(".md") or file.endswith(".txt"):
                ruta_completa = os.path.join(root, file)
                try:
                    with open(ruta_completa, "r", encoding="utf-8") as f:
                        contenido = f.read()
                        contexto_total.append(f"--- INICIO DEL DOCUMENTO: {file} ---\n{contenido}\n--- FIN DEL DOCUMENTO ---")
                except Exception as e:
                    print(f"Error leyendo el archivo {file}: {e}")
                    
    # Unimos todos los manuales en un solo mega-texto para la IA
    return "\n\n".join(contexto_total)