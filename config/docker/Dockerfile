# Ultimate Discord Intelligence Bot - Multi-stage Docker Build
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Install Python dependencies using pyproject.toml (no external lockfile)
# Copy only metadata and source to leverage Docker layer caching effectively
COPY pyproject.toml README.md /app/
COPY src /app/src
# Install the package and its runtime dependencies
RUN pip install --no-cache-dir .

# Development stage
FROM base as development

# Install development dependencies (extras)
RUN pip install --no-cache-dir .[dev]

# Copy source code
COPY . /app

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: start API server with safe bootstrap
CMD ["python", "-m", "scripts.run_api", "--host", "0.0.0.0", "--port", "8000"]

# Production stage
FROM base as production

# Copy full source (including configs) for runtime
COPY . /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: start API server with safe bootstrap
CMD ["python", "-m", "scripts.run_api", "--host", "0.0.0.0", "--port", "8000"]

# Testing stage
FROM development as testing

# Install additional testing dependencies
RUN pip install --no-cache-dir \
    pytest-xdist \
    pytest-mock \
    factory-boy \
    freezegun

# Copy test configuration
COPY pytest.ini /app/pytest.ini

# Run tests
CMD ["pytest", "-v", "--cov=ultimate_discord_intelligence_bot", "--cov-report=html"]

# Build stage for optimized production image
FROM production as build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Optimize Python bytecode
RUN python -m compileall /app

# Remove unnecessary files
RUN find /app -name "*.py" -not -path "*/tests/*" -delete
RUN find /app -name "__pycache__" -type d -exec rm -rf {} +

# Final production stage
FROM python:3.11-slim as final

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy optimized application from build stage
COPY --from=build /app /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: start API server with safe bootstrap
CMD ["python", "-m", "scripts.run_api", "--host", "0.0.0.0", "--port", "8000"]
