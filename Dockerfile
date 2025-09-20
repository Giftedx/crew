# Advanced Contextual Bandits - Production Docker Configuration

# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

# Set labels for the image
LABEL org.label-schema.build-date=$BUILD_DATE \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.version=$VERSION \
    org.label-schema.name="advanced-contextual-bandits" \
    org.label-schema.description="Production-ready Advanced Contextual Bandits for AI routing" \
    org.label-schema.vendor="Ultimate Discord Intelligence Bot" \
    maintainer="production-team@company.com"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user and directories
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir numpy>=1.24.0 scipy>=1.10.0

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libopenblas0 \
    liblapack3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directories
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser production_monitoring.py ./
COPY --chown=appuser:appuser production_config_template.json ./
COPY --chown=appuser:appuser PRODUCTION_DEPLOYMENT_GUIDE.md ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config /app/metrics && \
    chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONPATH=/app \
    ADVANCED_BANDITS_LOG_LEVEL=INFO \
    ADVANCED_BANDITS_METRICS_ENABLED=true \
    ADVANCED_BANDITS_CONFIG_PATH=/app/config/production_config.json

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 8090

# Default command
CMD ["python", "production_monitoring.py", "--config", "/app/config/production_config.json"]
