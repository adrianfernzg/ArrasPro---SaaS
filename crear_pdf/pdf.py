"""
pdf.py - Script independiente para generar un contrato PDF de prueba.
Útil para testear la generación de PDF sin necesidad de la API.

Ejecutar desde la raíz del proyecto:
    python -m crear_pdf.pdf
"""

import os
from controlador.servicios.servicio_ia import extraer_datos_nota_simple
from controlador.servicios.servicio_pdf import generar_contrato_pdf

# Ruta al PDF de prueba de Nota Simple
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_NOTA_SIMPLE = os.path.join(BASE_DIR, "controlador", "api", "notasimple.pdf")


def main():
    """Flujo de prueba: extraer datos con IA → generar PDF."""

    # 1. Verificar que existe el archivo de prueba
    if not os.path.exists(RUTA_NOTA_SIMPLE):
        print(f"❌ No se encontró el archivo de prueba: {RUTA_NOTA_SIMPLE}")
        print("   Coloca un archivo 'notasimple.pdf' en la carpeta controlador/api/")
        return

    # 2. Extraer datos con IA
    print("📄 Extrayendo datos de la Nota Simple con IA...")
    resultado = extraer_datos_nota_simple(RUTA_NOTA_SIMPLE)

    if not resultado:
        print("❌ No se pudieron extraer datos de la IA. Abortando.")
        return

    print(f"📋 Datos extraídos: {resultado}")

    # 3. Construir el objeto de contrato con datos de prueba
    datos_contrato = {
        "tipo": "arras_sin_cargas",
        "vendedores": [{
            "nombre": resultado.get("NOMBRE_VENDEDOR", ""),
            "dni": resultado.get("DNI_VENDEDOR", ""),
            "domicilio": resultado.get("DOMICILIO_VENDEDOR", "")
        }],
        "compradores": [{
            "nombre": "Comprador de Prueba",
            "dni": "87654321B",
            "domicilio": "Dirección de prueba"
        }],
        "finca": {
            "direccion": resultado.get("DIRECCION_FINCA", ""),
            "precio": "250.000",
            "arras": "25.000"
        },
        "fechas": {
            "firma": "20/03/2026",
            "limite": "20/06/2026"
        }
    }

    # 4. Generar el PDF
    ruta_pdf = generar_contrato_pdf(datos_contrato)
    print(f"\n🎉 ¡PDF generado con éxito!")
    print(f"   Ruta: {ruta_pdf}")


if __name__ == "__main__":
    main()