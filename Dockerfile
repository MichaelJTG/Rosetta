# syntax=docker/dockerfile:1
# ROSETTA — imagen de la aplicación FastAPI (amd64 y arm64).
#
# - Dependencias Python instaladas desde uv.lock: build reproducible y con las
#   versiones parcheadas que audita el CI (RNF-05, RNF-10, RNF-12).
# - torch en variante CPU (sin librerías CUDA): ver [tool.uv.sources].
# - Sensores Red Team: nmap (paquete Debian) y Nuclei (release oficial de
#   ProjectDiscovery, licencia MIT, verificada por SHA-256). Solo se orquestan
#   por CLI, nunca se modifican.
# - Se ejecuta con un usuario sin privilegios (B-10).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    HF_HOME=/opt/hf-cache \
    ANONYMIZED_TELEMETRY=False \
    CHROMADB_PATH=/app/.chroma \
    ROSETTA_SESSION_DB=/app/data/.rosetta_sessions.db \
    ROSETTA_CONTROLS_DB=/app/data/.rosetta_controls.db \
    ROSETTA_REPORTS_DIR=/app/reports

# --- Dependencias de sistema -------------------------------------------------
# PDF (pango/harfbuzz/fuentes), nmap, curl (healthcheck) y unzip (Nuclei).
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    curl \
    ca-certificates \
    unzip \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libjpeg62-turbo \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# --- Nuclei: binario oficial para la arquitectura de la imagen ---------------
ARG NUCLEI_VERSION=3.11.1
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "${arch}" in amd64|arm64) ;; *) echo "Nuclei no publica binario para ${arch}"; exit 1;; esac; \
    base="https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}"; \
    zip="nuclei_${NUCLEI_VERSION}_linux_${arch}.zip"; \
    cd /tmp; \
    curl -fsSLO "${base}/${zip}"; \
    curl -fsSLO "${base}/nuclei_${NUCLEI_VERSION}_checksums.txt"; \
    grep " ${zip}\$" "nuclei_${NUCLEI_VERSION}_checksums.txt" | sha256sum -c -; \
    unzip -q "${zip}" nuclei -d /usr/local/bin; \
    rm -f /tmp/nuclei_*; \
    nuclei -version

# --- Usuario sin privilegios (B-10) y directorios de datos -------------------
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin rosetta \
    && mkdir -p /app/data /app/.chroma /app/reports /opt/hf-cache \
    && chown rosetta:rosetta /app/data /app/.chroma /app/reports /opt/hf-cache

# --- uv con versión fijada ----------------------------------------------------
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv

WORKDIR /app

# --- Dependencias Python desde el lockfile (capa cacheada) -------------------
# La caché de uv va en un cache mount: no queda dentro de la imagen.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

COPY corpus/ ./corpus/

USER rosetta

# Modelo de embeddings del RAG precargado: no se descarga en cada arranque.
RUN python -c "from sentence_transformers import SentenceTransformer; \
SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Plantillas de Nuclei en el HOME del usuario (la demo no depende de descargarlas).
RUN nuclei -update-templates -silent && test -d "${HOME}/nuclei-templates"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "rosetta.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
