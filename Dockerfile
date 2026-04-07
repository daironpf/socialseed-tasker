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

# Environment variables for Neo4j configuration
ENV TASKER_NEO4J_URI=bolt://localhost:7687
ENV TASKER_NEO4J_USERNAME=neo4j
ENV TASKER_NEO4J_PASSWORD=
ENV TASKER_API_HOST=0.0.0.0
ENV TASKER_API_PORT=8000

# Expose the API port
EXPOSE 8000

# Health check - verifies both API and Neo4j connectivity
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command: start the FastAPI server with Neo4j repository
CMD ["python", "-m", "socialseed_tasker.entrypoints.web_api"]
