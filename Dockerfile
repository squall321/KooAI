# Multi-stage build for KooAI Simulation Post-Processing Platform
# Stage 1: Builder - Install dependencies and build
FROM python:3.11-slim as builder

LABEL maintainer="KooAI Team"
LABEL description="KooAI Simulation Post-Processing API"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency files
WORKDIR /app
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install \
    numpy>=1.26.0 \
    pandas>=2.1.0 \
    scipy>=1.11.0 \
    fastapi>=0.108.0 \
    uvicorn[standard]>=0.25.0 \
    python-multipart>=0.0.6 \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    click>=8.1.0 \
    rich>=13.0.0 \
    httpx>=0.25.0 \
    python-dotenv>=1.0.0

# Stage 2: Runtime - Create minimal production image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    KOOAI_ENV=production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r kooai && useradd -r -g kooai kooai

# Create application directories
RUN mkdir -p /app /app/data /app/logs && \
    chown -R kooai:kooai /app

# Copy virtual environment from builder
COPY --from=builder --chown=kooai:kooai /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=kooai:kooai src/ ./src/
COPY --chown=kooai:kooai kooai_cli.py ./
COPY --chown=kooai:kooai pyproject.toml ./
COPY --chown=kooai:kooai README.md ./

# Switch to non-root user
USER kooai

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Default command: run API server
CMD ["uvicorn", "src.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
