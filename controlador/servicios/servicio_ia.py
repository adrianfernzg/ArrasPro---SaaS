"""
servicio_ia.py - Servicio de extracción de datos con Gemini 3
Envía documentos (PDF/imagen) a la API de Gemini y devuelve JSON estructurado.

REGLA CRÍTICA (AGENT.md):
  - NO usar la librería google-generativeai (da errores 404).
  - USAR peticiones requests directas a la API v1beta.
  - El PDF debe enviarse como inline_data en formato base64.
"""

import json
import os
import base64
import requests
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Clave de API de Gemini
API_KEY = os.getenv("GEMINI_API_KEY", "")

# URL del modelo Gemini 3 Flash (petición directa, sin librería)
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3-flash-preview:generateContent"
)


def extraer_datos_nota_simple(ruta_archivo: str) -> dict | None:
    """
    Lee un PDF de Nota Simple y extrae datos usando Gemini 3.
    Devuelve un diccionario con los campos extraídos, o None si falla.
    """
    print(f"📄 Leyendo: {os.path.basename(ruta_archivo)}...")

    try:
        # 1. Leer el archivo y convertirlo a base64
        with open(ruta_archivo, "rb") as f:
            archivo_base64 = base64.b64encode(f.read()).decode("utf-8")

        # 2. Determinar el mime_type según la extensión
        extension = os.path.splitext(ruta_archivo)[1].lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        mime_type = mime_types.get(extension, "application/pdf")

        # 3. Construir el payload para Gemini
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": (
                            "Analiza esta Nota Simple española. "
                            "Extrae y devuelve SOLO un JSON con estos campos: "
                            "NOMBRE_VENDEDOR, DNI_VENDEDOR, DOMICILIO_VENDEDOR, "
                            "DIRECCION_FINCA, CUOTA_PARTICIPACION. "
                            "No escribas nada más que el objeto JSON."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": archivo_base64
                        }
                    }
                ]
            }]
        }

        # 4. Enviar petición HTTP directa a Gemini (sin librería)
        print("🚀 Enviando petición a Gemini 3 Flash...")
        url = f"{GEMINI_URL}?key={API_KEY}"
        response = requests.post(url, json=payload, timeout=60)
        res_json = response.json()

        if response.status_code != 200:
            print(f"❌ Error de API ({response.status_code}): {res_json}")
            return None

        # 5. Extraer el texto de la respuesta
        texto_ia = res_json["candidates"][0]["content"]["parts"][0]["text"]

        # 6. Limpiar posibles etiquetas de markdown del JSON
        texto_limpio = texto_ia.strip()
        if texto_limpio.startswith("```"):
            texto_limpio = texto_limpio.split("\n", 1)[1]  # Quitar primera línea ```json
        if texto_limpio.endswith("```"):
            texto_limpio = texto_limpio.rsplit("```", 1)[0]  # Quitar último ```
        texto_limpio = texto_limpio.strip()

        print("✅ Datos extraídos correctamente por la IA.")
        return json.loads(texto_limpio)

    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON de la IA: {e}")
        return None
    except requests.RequestException as e:
        print(f"❌ Error de conexión con Gemini: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None


def extraer_datos_dni(ruta_archivo: str) -> dict | None:
    """
    Lee una imagen de DNI y extrae datos usando Gemini 3.
    Devuelve un diccionario con NOMBRE, DNI, DOMICILIO, o None si falla.
    """
    print(f"🪪 Leyendo DNI: {os.path.basename(ruta_archivo)}...")

    try:
        with open(ruta_archivo, "rb") as f:
            archivo_base64 = base64.b64encode(f.read()).decode("utf-8")

        extension = os.path.splitext(ruta_archivo)[1].lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        mime_type = mime_types.get(extension, "image/jpeg")

        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": (
                            "Analiza este DNI español. "
                            "Extrae y devuelve SOLO un JSON con: "
                            "NOMBRE, DNI, DOMICILIO. "
                            "No escribas nada más que el objeto JSON."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": archivo_base64
                        }
                    }
                ]
            }]
        }

        url = f"{GEMINI_URL}?key={API_KEY}"
        response = requests.post(url, json=payload, timeout=60)
        res_json = response.json()

        if response.status_code != 200:
            print(f"❌ Error de API ({response.status_code}): {res_json}")
            return None

        texto_ia = res_json["candidates"][0]["content"]["parts"][0]["text"]
        texto_limpio = texto_ia.strip()
        if texto_limpio.startswith("```"):
            texto_limpio = texto_limpio.split("\n", 1)[1]
        if texto_limpio.endswith("```"):
            texto_limpio = texto_limpio.rsplit("```", 1)[0]
        texto_limpio = texto_limpio.strip()

        print("✅ Datos del DNI extraídos correctamente.")
        return json.loads(texto_limpio)

    except Exception as e:
        print(f"❌ Error extrayendo datos del DNI: {e}")
        return None
