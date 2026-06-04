# ============================================================
#  CareerBridge — Multi-stage Dockerfile
# ============================================================

# ---------- Stage 1: Base image with system deps ----------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        # Playwright system dependencies
        libnss3 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 \
        libatspi2.0-0 \
        libwayland-client0 \
    && rm -rf /var/lib/apt/lists/*


# ---------- Stage 2: Python dependencies ----------
FROM base AS deps

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium


# ---------- Stage 3: Application ----------
FROM deps AS app

WORKDIR /app

COPY . .

# Collect static files (uses whitenoise for serving)
RUN python manage.py collectstatic --noinput --settings=careerbridge.settings.production 2>/dev/null || true

# Default command — overridden per service in docker-compose
CMD ["gunicorn", "careerbridge.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]

EXPOSE 8000
