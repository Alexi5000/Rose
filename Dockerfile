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

# Stage 2: Build Python application
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install the project into `/app`
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies for building libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependency management files (lock file and pyproject.toml) first
COPY uv.lock pyproject.toml README.md /app/

# Install the application dependencies
RUN uv sync --frozen --no-cache

# Copy your application code into the container
COPY src/ /app/src/

# Copy frontend build from previous stage
COPY --from=frontend-builder /frontend/dist /app/frontend/build

# Set the virtual environment environment variables
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Install the package in editable mode
RUN uv pip install -e .

# Create data directory for memory databases
RUN mkdir -p /app/data

# Define volumes
VOLUME ["/app/data"]

# Expose the port (configurable via PORT env var)
EXPOSE 8080

# Run the Rose web interface using uvicorn
CMD uvicorn ai_companion.interfaces.web.app:app --host 0.0.0.0 --port ${PORT:-8080}
