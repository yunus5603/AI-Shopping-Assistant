FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

WORKDIR /app

# curl is only needed for the HEALTHCHECK.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY flipkart/ flipkart/
COPY static/ static/
COPY templates/ templates/
COPY app.py .

RUN useradd --create-home appuser
USER appuser

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/health || exit 1

# One worker keeps per-session chat memory in a single process; threads handle concurrency.
CMD gunicorn --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:${PORT} "app:create_app()"
