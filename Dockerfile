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

# Base stage: Core dependencies only
FROM python:3.11-slim as base

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libopenblas0 \
    liblapack3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directories
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser production_monitoring.py ./
COPY --chown=appuser:appuser production_config_template.json ./
COPY --chown=appuser:appuser PRODUCTION_DEPLOYMENT_GUIDE.md ./

# Copy requirements for optional dependencies
COPY requirements.txt pyproject.toml ./

# Install core dependencies only
RUN pip install --no-cache-dir -r requirements.txt

# Optional dependencies stage (only installed if needed)
FROM base as with-optionals

# Build arguments for optional dependencies
ARG INSTALL_REDIS=false
ARG INSTALL_TRANSFORMERS=false
ARG INSTALL_QDRANT=false
ARG INSTALL_PYANNOTE=false
ARG INSTALL_WHISPER=false
ARG INSTALL_FAST_WHISPER=false

# Install optional dependencies based on build args
RUN if [ "$INSTALL_REDIS" = "true" ]; then \
    echo "Installing Redis..." && \
    pip install --no-cache-dir redis[hiredis]; \
    fi

RUN if [ "$INSTALL_TRANSFORMERS" = "true" ]; then \
    echo "Installing sentence-transformers..." && \
    pip install --no-cache-dir sentence-transformers; \
    fi

RUN if [ "$INSTALL_QDRANT" = "true" ]; then \
    echo "Installing Qdrant client..." && \
    pip install --no-cache-dir qdrant-client; \
    fi

RUN if [ "$INSTALL_PYANNOTE" = "true" ]; then \
    echo "Installing Pyannote..." && \
    pip install --no-cache-dir pyannote.audio; \
    fi

RUN if [ "$INSTALL_WHISPER" = "true" ]; then \
    echo "Installing Whisper..." && \
    pip install --no-cache-dir openai-whisper; \
    fi

RUN if [ "$INSTALL_FAST_WHISPER" = "true" ]; then \
    echo "Installing Faster Whisper..." && \
    pip install --no-cache-dir faster-whisper; \
    fi

# Final stage
FROM with-optionals as final

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config /app/metrics && \
    chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONPATH=/app \
    ADVANCED_BANDITS_LOG_LEVEL=INFO \
    ADVANCED_BANDITS_METRICS_ENABLED=true \
    ADVANCED_BANDITS_CONFIG_PATH=/app/config/production_config.json \
    # Optional dependency feature flags (default to false for minimal image)
    ENABLE_REDIS_CACHE=false \
    ENABLE_SENTENCE_TRANSFORMERS=false \
    ENABLE_QDRANT_VECTOR_STORE=false \
    ENABLE_SPEAKER_DIARIZATION=false \
    ENABLE_WHISPER_TRANSCRIPTION=false \
    ENABLE_FAST_WHISPER=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 8090

# Default command
CMD ["python", "production_monitoring.py", "--config", "/app/config/production_config.json"]

# Production stage alias
FROM final as production
