# =============================================================================
# Stage 1: Builder - Install dependencies and build the package
# =============================================================================
FROM python:3.10-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definitions first (layer caching)
COPY pyproject.toml ./

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

# Create non-root user for security
RUN groupadd -r tasker && useradd -r -g tasker -d /app -s /sbin/nologin tasker \
    && chown -R tasker:tasker /app

# Environment variables for configuration
ENV NEO4J_URI=bolt://localhost:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV TASKER_STORAGE_BACKEND=neo4j

# Expose the API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Switch to non-root user
USER tasker

# Default command: start the FastAPI server
CMD ["sh", "-c", "uvicorn socialseed_tasker.entrypoints.web_api.app:create_app --factory --host ${API_HOST} --port ${API_PORT}"]
