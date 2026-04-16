# ============================================================
# Dockerfile - ArrasPro API
# ============================================================
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Shell form para que Railway pueda inyectar $PORT
CMD ["sh", "-c", "uvicorn controlador.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
