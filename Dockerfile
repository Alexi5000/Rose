# Multi-stage build for Rose the Healer Shaman
# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Build Python dependencies
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS python-builder

WORKDIR /app

# Install system dependencies for building libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependency management files
COPY uv.lock pyproject.toml README.md /app/

# Install the application dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY src/ /app/src/

# Install the package in editable mode
RUN uv pip install -e .

# Stage 3: Runtime image (minimal, no build tools)
FROM python:3.12-slim-bookworm

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=python-builder /app/.venv /app/.venv

# Copy application code
COPY --from=python-builder /app/src /app/src
COPY --from=python-builder /app/pyproject.toml /app/README.md /app/

# Copy frontend build from frontend-builder stage
COPY --from=frontend-builder /frontend/dist /app/frontend/build

# Create data directories for memory databases and backups
RUN mkdir -p /app/data /app/data/backups

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Define volumes
VOLUME ["/app/data"]

# Set memory limit environment variable (can be overridden at runtime)
ENV MEMORY_LIMIT=512m

# Expose the port (configurable via PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8080}/api/health')" || exit 1

# Run the Rose web interface using uvicorn
CMD uvicorn ai_companion.interfaces.web.app:app --host 0.0.0.0 --port ${PORT:-8080}
