# ============================================================
# Dockerfile - ArrasPro API
# ============================================================
# Imagen base: Python 3.12 slim (ligera)
FROM python:3.12-slim

# Evitar prompts interactivos de apt
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements primero (para aprovechar el caché de capas de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Exponer el puerto de la API
EXPOSE 8000

# Comando de inicio compatible con plataformas que inyectan PORT (ej. Railway)
CMD ["sh", "-c", "uvicorn controlador.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
