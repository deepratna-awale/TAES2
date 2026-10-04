# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    GRADIO_ANALYTICS_ENABLED=False \
    LITELLM_LOCAL_MODEL_COST_MAP=True \
    TAES_SERVER_NAME=0.0.0.0 \
    TAES_SERVER_PORT=7860

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Run as an unprivileged user
RUN useradd --create-home --uid 1000 taes \
    && mkdir -p logs uploads data \
    && chown -R taes:taes /app
USER taes

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ[\"TAES_SERVER_PORT\"]}/', timeout=5)" || exit 1

CMD ["python", "app.py"]
