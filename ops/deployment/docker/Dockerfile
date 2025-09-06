# Ultimate Discord Intelligence Bot - Production Dockerfile

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy project metadata and sources, then install (editable)
COPY pyproject.toml ./
COPY src/ ./src/
COPY config/ ./config/
RUN pip install -e .[metrics]
COPY ops/deployment/scripts/deploy.sh ./

# Create required directories
RUN mkdir -p logs data

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash bot && \
    chown -R bot:bot /app
USER bot

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command
CMD ["python", "-m", "ultimate_discord_intelligence_bot.setup_cli", "run", "discord"]

# Multi-stage build for smaller production image
FROM python:3.11-slim as production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only necessary files from builder
COPY --from=0 /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=0 /usr/local/bin /usr/local/bin
COPY --from=0 /app/src ./src
COPY --from=0 /app/config ./config

RUN useradd --create-home --shell /bin/bash bot && \
    mkdir -p logs data && \
    chown -R bot:bot /app

USER bot

EXPOSE 8000

CMD ["python", "-m", "ultimate_discord_intelligence_bot.setup_cli", "run", "discord"]
