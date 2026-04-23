# Dockerfile - Privacy Filter GUI
#
# Build: docker build -t privacy-filter-gui .
# Run:   docker run --rm -p 8501:8501 privacy-filter-gui
#
# Il modello openai/privacy-filter viene scaricato al primo avvio.
# Monta una cache per evitare il re-download:
#   -v pf-cache:/root/.cache/huggingface

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl && \
    rm -rf /var/lib/apt/lists/*

COPY gui/requirements.txt /app/gui/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/gui/requirements.txt

COPY . /app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "gui/app_advanced.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]
