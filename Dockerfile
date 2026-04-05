# =============================================================================
# Stage 1: Builder - Install dependencies and build the package
# =============================================================================
FROM python:3.10-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definitions first (layer caching)
COPY pyproject.toml ./

# Copy source code for build
COPY src/ ./src/

# Install runtime dependencies into a custom prefix
RUN pip install --no-cache-dir --prefix=/install .

# =============================================================================
# Stage 2: Runtime - Minimal image with only what's needed to run
# =============================================================================
FROM python:3.10-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY src/ ./src/

# Create data directory and set permissions BEFORE switching to non-root
RUN mkdir -p /app/data && chown -R root:root /app/data

# Environment variables for configuration
ENV TASKER_STORAGE_BACKEND=file
ENV TASKER_FILE_PATH=/app/data
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Expose the API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command: start the FastAPI server with file-based storage
CMD ["uvicorn", "socialseed_tasker.entrypoints.web_api.api:app", "--host", "0.0.0.0", "--port", "8000"]

# Switch to non-root user
USER root