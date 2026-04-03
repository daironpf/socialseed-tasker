# Issue #05: Create Multi-Stage Dockerfile for Docker Hub Distribution

## Description

Design and implement a `Dockerfile` using **multi-stage builds** to create a lightweight, production-ready Docker image for Docker Hub distribution. The image must contain both the CLI and API entrypoints of the socialseed-tasker application.

### Requirements

#### Multi-Stage Build Strategy

**Stage 1: Builder**
- Use a full Python 3.10+ base image with build tools
- Install all build-time dependencies
- Copy and install Python dependencies (pyproject.toml)
- Copy application source code
- Run any build/compilation steps

**Stage 2: Runtime**
- Use a slim Python base image (`python:3.10-slim`)
- Copy only the necessary artifacts from the builder stage
- Install only runtime dependencies (no dev/test dependencies)
- Set proper non-root user for security
- Define proper entrypoint and CMD

#### Image Requirements
- Final image size should be minimized (target < 500MB)
- Must include both CLI (Typer) and API (FastAPI) capabilities
- Must expose the API port (default 8000)
- Must support environment variable configuration for Neo4j connection
- Must have proper healthcheck endpoint

#### Dockerfile Structure
```dockerfile
# Builder stage
FROM python:3.10 AS builder
WORKDIR /build
COPY pyproject.toml poetry.lock* ./
# Install dependencies
COPY src/ ./src/
# Build package

# Runtime stage
FROM python:3.10-slim
WORKDIR /app
# Copy from builder
# Create non-root user
# Set entrypoint
```

#### Entrypoint Configuration
- Default CMD should start the FastAPI server
- Support CLI commands via entrypoint override
- Accept environment variables for configuration:
  - `NEO4J_URI` - Neo4j bolt connection string
  - `NEO4J_USER` - Neo4j username
  - `NEO4J_PASSWORD` - Neo4j password
  - `API_HOST` - API bind address
  - `API_PORT` - API port

### Business Value

A well-optimized Docker image ensures fast deployment, lower bandwidth costs, and reduced attack surface. Multi-stage builds separate build-time complexity from runtime simplicity, making the image suitable for production deployment and Docker Hub distribution.

## Status: COMPLETED
