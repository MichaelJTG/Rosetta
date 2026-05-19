# ROSETTA - imagen de la aplicacion FastAPI
# Base ligera Debian; instala dependencias de sistema para WeasyPrint (PDF)
# y el binario nmap usado por el adaptador Red Team.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# --- Dependencias de sistema -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    curl \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libjpeg62-turbo \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Dependencias Python (capa cacheada salvo cambio en pyproject) -----------
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install .

# --- Codigo de la aplicacion -------------------------------------------------
COPY . .

# Directorio de datos persistentes (SQLite de sesion)
RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "rosetta.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
