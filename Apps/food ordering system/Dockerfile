# ============================================
# FOOD ORDERING SYSTEM - DOCKER CONFIGURATION
# ============================================
# Multi-stage Docker build for production deployment

# ============================================
# STAGE 1: Base Python Image
# ============================================
FROM python:3.12-slim as base

# Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# STAGE 2: Dependencies
# ============================================
FROM base as dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# STAGE 3: Production
# ============================================
FROM base as production

# Copy installed dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles media logs && \
    chmod -R 755 staticfiles media logs

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=5)"

# Run gunicorn
CMD ["gunicorn", "food_ordering.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
