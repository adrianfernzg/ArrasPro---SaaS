# ArrasPro - Generador de Contratos Inmobiliarios con IA

ArrasPro es una aplicación web (SaaS) diseñada para simplificar y profesionalizar la creación de contratos de arras y alquiler. Utiliza Inteligencia Artificial para automatizar la extracción de datos de documentos oficiales, reduciendo errores humanos y ahorrando tiempo.

## 🚀 Características Principales

- **Generación Dinámica de PDFs:** Crea contratos de arras (con/sin cargas) y alquiler listos para firmar.
- **Extracción de Datos con IA:** Sube una Nota Simple o un DNI y la IA (Gemini) extraerá automáticamente los datos de vendedores, compradores y fincas.
- **Editor en Tiempo Real:** Visualiza cómo queda tu contrato mientras rellenas el formulario.
- **Panel de Usuario:** Guarda, gestiona y descarga tus contratos anteriores.
- **Autenticación Segura:** Registro manual con validación de contraseñas y login profesional con Google.
- **Notificaciones por Email:** Recepción de correos de bienvenida tras el registro.

## 🛠 Stack Tecnológico

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Frontend:** HTML5, CSS3, [Alpine.js](https://alpinejs.dev/) para reactividad.
- **Base de Datos:** [PostgreSQL](https://www.postgresql.org/) con SQLAlchemy.
- **IA:** [Gemini 1.5 Flash](https://ai.google.dev/) para procesamiento de documentos.
- **PDF:** [fpdf2](https://py-pdf.github.io/fpdf2/) para la generación de documentos profesionales.

## 📋 Estructura del Proyecto

```text
├── controlador/          # Lógica de negocio y servicios
│   ├── api/              # Endpoints FastAPI y routers
│   └── servicios/        # Servicios de IA, PDF, Email y Auth
├── modelo/               # Base de datos y esquemas Pydantic
├── vista/                # Frontend (HTML, CSS, JS)
├── plantillas/           # Plantillas de texto para los contratos
└── crear_pdf/            # Carpeta de salida para PDFs generados
```

## ⚙️ Instalación y Uso

1. **Clonar el repositorio.**
2. **Crear un entorno virtual:** `python -m venv .venv`
3. **Instalar dependencias:** `pip install -r requirements.txt`
4. **Configurar variables de entorno:** Crea un archivo `.env` con:
   - `DATABASE_URL`
   - `GEMINI_API_KEY`
   - `GOOGLE_CLIENT_ID`
   - `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
5. **Ejecutar el servidor:** `uvicorn controlador.api.main:app --reload --port 8080`

## ⚖️ Aviso Legal
Este software es una herramienta de apoyo. Se recomienda que todos los contratos generados sean supervisados por un profesional legal colegiado.
