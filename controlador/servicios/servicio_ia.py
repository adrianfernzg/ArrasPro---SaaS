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
    Lee un PDF/imagen de Nota Simple y extrae datos usando Gemini 3.
    Solo extrae: DIRECCION_FINCA, REFERENCIA_CATASTRAL, NUMERO_FINCA.
    Si el documento NO es una Nota Simple, devuelve {"error": "no_es_nota_simple"}.
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

        # 3. Construir el payload para Gemini con validación estricta del tipo de documento
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": (
                            "Eres un validador y extractor de Notas Simples del Registro de la Propiedad español. "
                            "Tarea: Analiza el documento adjunto.\n\n"
                            "PASO 1 - VALIDACIÓN: Determina si el documento es una Nota Simple oficial "
                            "(emitida por el Registro de la Propiedad). Una Nota Simple contiene típicamente: "
                            "encabezado del Registro, número de finca registral, referencia catastral, "
                            "descripción del inmueble, titulares, cargas, etc.\n\n"
                            "PASO 2 - RESPUESTA:\n"
                            "- Si el documento NO es una Nota Simple (es otra cosa: foto, factura, DNI, etc.), "
                            "devuelve EXACTAMENTE: {\"error\": \"no_es_nota_simple\"}\n"
                            "- Si SÍ es una Nota Simple, devuelve EXACTAMENTE un JSON con: "
                            "DIRECCION_FINCA (dirección completa del inmueble), "
                            "REFERENCIA_CATASTRAL (código alfanumérico catastral), "
                            "NUMERO_FINCA (número de finca registral). "
                            "Si algún campo no aparece, deja la cadena vacía.\n\n"
                            "Responde SOLO con el objeto JSON, sin texto adicional, sin markdown."
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
                            "Eres un validador y extractor de documentos de identidad españoles "
                            "(DNI, NIE o pasaporte). Tarea: Analiza el documento adjunto.\n\n"
                            "PASO 1 - VALIDACIÓN: Determina si el documento es un DNI, NIE o pasaporte español oficial "
                            "(documento de identidad con foto, nombre, número de identidad y firma).\n\n"
                            "PASO 2 - RESPUESTA:\n"
                            "- Si el documento NO es un DNI, NIE o pasaporte (es una foto de un perro, paisaje, "
                            "factura, nota simple, captura de pantalla u otro documento), "
                            "devuelve EXACTAMENTE: {\"error\": \"no_es_dni\"}\n"
                            "- Si SÍ es un DNI/NIE/pasaporte, devuelve EXACTAMENTE un JSON con: "
                            "NOMBRE (nombre y apellidos completos), "
                            "DNI (número de DNI/NIE o pasaporte), "
                            "DOMICILIO (dirección si aparece, si no cadena vacía). "
                            "Si algún campo no aparece, deja la cadena vacía.\n\n"
                            "Responde SOLO con el objeto JSON, sin texto adicional, sin markdown."
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
