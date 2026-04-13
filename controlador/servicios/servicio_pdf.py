"""
servicio_pdf.py - Servicio de generación de contratos PDF
Lee la plantilla .txt correspondiente al tipo de contrato,
reemplaza las variables con los datos del formulario,
y genera un PDF profesional con fpdf2.

REGLA CRÍTICA (AGENT.md):
  - Debe realizar bucles (for) sobre las listas de vendedores y compradores.
  - Usar markdown=True en multi_cell para soportar negritas de la plantilla.
"""

import os
from fpdf import FPDF

# Ruta a la carpeta de plantillas (desde la raíz del proyecto)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLANTILLAS_DIR = os.path.join(BASE_DIR, "plantillas")
OUTPUT_DIR = os.path.join(BASE_DIR, "crear_pdf")

# Mapeo de tipo de contrato -> archivo de plantilla
PLANTILLA_MAP = {
    "arras_sin_cargas": "arras_sincargas.txt",
    "arras_con_cargas": "arras_concargas.txt",
    "alquiler": "alquiler",
}


def generar_contrato_pdf(datos_contrato: dict) -> str:
    """
    Genera un PDF a partir de los datos del contrato.
    
    Args:
        datos_contrato: Diccionario con tipo, vendedores, compradores, finca, fechas.
    
    Returns:
        Ruta absoluta al PDF generado.
    
    Raises:
        FileNotFoundError: Si la plantilla no existe.
        ValueError: Si el tipo de contrato no es válido.
    """
    tipo = datos_contrato.get("tipo", "arras_sin_cargas")
    
    # 1. Seleccionar la plantilla correcta según el tipo
    archivo_plantilla = PLANTILLA_MAP.get(tipo)
    if not archivo_plantilla:
        raise ValueError(f"Tipo de contrato no reconocido: '{tipo}'")
    
    ruta_plantilla = os.path.join(PLANTILLAS_DIR, archivo_plantilla)
    
    if not os.path.exists(ruta_plantilla):
        raise FileNotFoundError(f"Plantilla no encontrada: {ruta_plantilla}")
    
    # 2. Leer la plantilla
    with open(ruta_plantilla, "r", encoding="utf-8") as f:
        contenido = f.read()
    
    # 3. Extraer datos del diccionario
    vendedores = datos_contrato.get("vendedores", [])
    compradores = datos_contrato.get("compradores", [])
    finca = datos_contrato.get("finca", {})
    fechas = datos_contrato.get("fechas", {})
    
    # 4. Reemplazar variables simples
    contenido = contenido.replace("[FECHA]", fechas.get("firma", "___/___/______"))
    contenido = contenido.replace("[DIRECCION_FINCA]", finca.get("direccion", "________________"))
    contenido = contenido.replace("[PRECIO]", finca.get("precio", "________"))
    contenido = contenido.replace("[ARRAS]", finca.get("arras", "________"))
    contenido = contenido.replace("[FECHA_LIMITE]", fechas.get("limite", "___/___/______"))
    
    # 5. Reemplazar datos del primer vendedor (para compatibilidad con plantilla simple)
    if vendedores:
        contenido = contenido.replace("[NOMBRE_VENDEDOR]", vendedores[0].get("nombre", "________________"))
        contenido = contenido.replace("[DNI_VENDEDOR]", vendedores[0].get("dni", "________________"))
        contenido = contenido.replace("[DOMICILIO_VENDEDOR]", vendedores[0].get("domicilio", "________________"))
    
    # 6. Reemplazar datos del primer comprador
    if compradores:
        contenido = contenido.replace("[NOMBRE_COMPRADOR]", compradores[0].get("nombre", "________________"))
        contenido = contenido.replace("[DNI_COMPRADOR]", compradores[0].get("dni", "________________"))
        contenido = contenido.replace("[DOMICILIO_COMPRADOR]", compradores[0].get("domicilio", "________________"))
    
    # 7. Crear el PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Si hay múltiples vendedores/compradores, generar bloques adicionales
    if len(vendedores) > 1:
        for i, v in enumerate(vendedores[1:], start=2):
            bloque = f"\nY el vendedor {i}: **{v.get('nombre', '')}** con DNI **{v.get('dni', '')}**, domicilio en **{v.get('domicilio', '')}**."
            # Insertar después de la primera mención del vendedor
            contenido += bloque
    
    if len(compradores) > 1:
        for i, c in enumerate(compradores[1:], start=2):
            bloque = f"\nY el comprador {i}: **{c.get('nombre', '')}** con DNI **{c.get('dni', '')}**, domicilio en **{c.get('domicilio', '')}**."
            contenido += bloque
    
    # 8. Añadir cláusulas adicionales si existen
    clausulas_extra = datos_contrato.get("clausulas", [])
    if clausulas_extra:
        nombres_ordinales = ["CUARTA", "QUINTA", "SEXTA", "SÉPTIMA", "OCTAVA", "NOVENA", "DÉCIMA"]
        for i, clausula in enumerate(clausulas_extra):
            nombre = nombres_ordinales[i] if i < len(nombres_ordinales) else f"{i+4}ª"
            texto_clausula = clausula.get("texto", "") if isinstance(clausula, dict) else clausula
            contenido += f"\n\n**{nombre}.** – {texto_clausula or '________________________'}"

    # 9. Añadir bloque de firmas
    contenido += "\n\n\n\n________________________          ________________________\n"
    contenido += "Fdo.: El Vendedor                 Fdo.: El Comprador"

    # 10. Escribir contenido al PDF con soporte de markdown (negritas)
    pdf.multi_cell(0, 10, txt=contenido, markdown=True)
    
    # 9. Guardar el PDF
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ruta_salida = os.path.join(OUTPUT_DIR, "Contrato_ArrasPro.pdf")
    pdf.output(ruta_salida)
    
    print(f"✅ PDF generado con éxito en: {ruta_salida}")
    return ruta_salida
