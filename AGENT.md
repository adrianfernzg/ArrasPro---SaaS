# Contexto del Proyecto: ArrasPro (SaaS de Contratos Inteligentes)

## 🎯 Objetivo
Desarrollar una aplicación web para la generación dinámica de contratos de arras y alquiler, utilizando IA para la extracción de datos de documentos (Nota Simple y DNI) y Python para la generación de PDFs profesionales.

## 🛠 Stack Tecnológico
- **Backend:** FastAPI (Python 3.12+)
- **Frontend:** HTML5, Tailwind CSS, Alpine.js (para reactividad y estado global).
- **Base de Datos:** PostgreSQL (SaaS ready).
- **IA:** Gemini 3 Flash (vía peticiones HTTP directas a la API v1beta).
- **Generación PDF:** Library `fpdf2` en Python.

## 🔄 Flujo de Usuario y Lógica
1. **Landing:** Botón "Generar Contrato" + Header con acceso a Panel de Usuario.
2. **Selector de Tipo:** El usuario elige (Compraventa con o sin cargas / Alquiler). Esto carga una plantilla `.txt` diferente.
3. **Editor Dual (Real-time):** - Estado manejado por Alpine.js (`x-data`).
   - Panel Izquierdo: Formulario con botones para añadir/quitar "bloques" (múltiples vendedores/compradores).
   - Panel Derecho: Vista previa tipo folio A4 que se actualiza al instante (`x-text`).
   - Drag & Drop: Envía PDFs/Imágenes a Gemini 3 -> Recibe JSON -> Actualiza el estado de Alpine.
4. **Conversión:** Al intentar descargar, modal de Login/Register (Manual + Google Auth).
5. **Finalización:** Registro -> Generación de PDF en Backend -> Descarga automática -> Redirección a Panel de Usuario (CRUD de contratos).

## 📋 Reglas Técnicas Críticas

### 1. Comunicación con Gemini 3
- NO usar la librería `google-generativeai` (da errores 404 en el entorno).
- USAR peticiones `requests` directas a: 
  `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={API_KEY}`
- El PDF debe enviarse como `inline_data` en formato `base64`.

### 2. Estructura de Datos (Alpine.js)
El estado global debe permitir múltiples entidades:
```javascript
{
    tipo: 'arras',
    vendedores: [{ nombre: '', dni: '', domicilio: '' }],
    compradores: [{ nombre: '', dni: '', domicilio: '' }],
    finca: { direccion: '', precio: '', arras: '' },
    fechas: { firma: '', limite: '' }
}

### 3. Generación de PDF (Python)

La función de generación debe recibir el JSON completo del frontend.

Debe realizar bucles (for) sobre las listas de vendedores y compradores para insertar tantos bloques de texto legal como sea necesario.

Usar markdown=True en multi_cell para soportar negritas de la plantilla.

### 4. Base de Datos (PostgreSQL)

Tabla usuarios: id, nombre, email (Unique), password_hash (Nullable), google_id (Nullable), metodo_registro ('manual'|'google').

Tabla contratos: id, user_id (FK), datos_json (JSONB), fecha_creacion, estado ('activo'|'vencido').

### 5. Readme.md
Cada vez que hagas cambios nuevos y consideres necesario, actualiza el readme.md para que yo pueda entender el proyecto.
(si está vacío rellénalo)

⚠️ Restricciones
No utilizar la IA para generar el texto del contrato; el texto está en plantillas

La IA solo extrae datos de Nota Simple (Vendedores, Finca) y DNI (Nombre, DNI, Domicilio).