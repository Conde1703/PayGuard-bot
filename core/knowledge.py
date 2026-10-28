import os
from typing import Dict, Any, List

def buscar_en_conocimiento(area: str, consulta: str) -> Dict[str, Any]:
    """
    Escanea las carpetas de SecOps_Global (Access e InfoSec).
    Retorna el equipo detectado, los extractos del documento y las URLs encontradas.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Mapeo flexible para garantizar que siempre apunte a SecOps_Global
    nombre_carpeta = "SecOps_Global" if "secops" in area.lower() else area
    knowledge_dir = os.path.join(base_dir, "knowledge", nombre_carpeta)

    resultado = {
        "equipo": None,
        "emoji": "🛡️",
        "archivo": None,
        "fragmentos": []
    }

    if not os.path.exists(knowledge_dir):
        return resultado

    consulta_tokens = [t for t in consulta.lower().replace("?", "").replace("¿", "").split() if len(t) > 2]

    # Recorrer subcarpetas: Access e InfoSec
    for raiz, _, archivos in os.walk(knowledge_dir):
        subequipo = os.path.basename(raiz)  # 'Access' o 'InfoSec'
        
        for filename in archivos:
            if filename.endswith(".md") or filename.endswith(".txt"):
                ruta = os.path.join(raiz, filename)
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        contenido = f.read()

                    # Dividir por bloques de texto / encabezados
                    secciones = contenido.split("\n## ")
                    
                    for sec in secciones:
                        sec_limpia = sec.lower()
                        # Evaluar coincidencias de palabras clave de la consulta en la sección
                        coincidencias = sum(1 for token in consulta_tokens if token in sec_limpia)
                        
                        if coincidencias > 0:
                            resultado["fragmentos"].append({
                                "equipo": subequipo,
                                "archivo": filename,
                                "puntos": coincidencias,
                                "texto": "## " + sec.strip() if not sec.startswith("#") else sec.strip()
                            })
                except Exception as e:
                    print(f"[KNOWLEDGE ERROR] No se pudo leer {filename}: {e}")

    if resultado["fragmentos"]:
        # Ordenar por mayor coincidencia semántica
        resultado["fragmentos"].sort(key=lambda x: x["puntos"], reverse=True)
        mejor_match = resultado["fragmentos"][0]
        resultado["equipo"] = mejor_match["equipo"]
        resultado["archivo"] = mejor_match["archivo"]
        resultado["emoji"] = "🟣" if mejor_match["equipo"] == "Access" else "🟢"

    return resultado