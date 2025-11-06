# Multi-stage Dockerfile for KooAI

# Stage 1: Base image with system dependencies
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
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Stage 2: Development image
FROM base as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ".[dev,llm]"

# Copy application code
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "src.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Production builder
FROM base as builder

# Copy requirements
COPY pyproject.toml ./

# Install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --prefix=/install .

# Stage 4: Production image
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/install/bin:${PATH}" \
    PYTHONPATH="/install/lib/python3.11/site-packages:${PYTHONPATH}"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /install

# Copy application code
COPY --chown=appuser:appuser ./src ./src
COPY --chown=appuser:appuser ./config ./config

# Create necessary directories
RUN mkdir -p /data/storage /data/models /var/log/kooai && \
    chown -R appuser:appuser /data /var/log/kooai

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
