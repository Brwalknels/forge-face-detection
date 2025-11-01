FROM python:3.11-slim

# Install system dependencies for dlib and face_recognition
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create user for security (non-root)
RUN useradd -m -u 1000 facedetect && \
    chown -R facedetect:facedetect /app

# Switch to non-root user
USER facedetect

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health').raise_for_status()" || exit 1

# Run with gunicorn for production
# --workers: Number of worker processes (2 * CPU cores + 1 recommended)
# --timeout: Worker timeout in seconds (face detection can take time)
# --bind: Host and port to bind to
# --log-level: Logging level
CMD ["gunicorn", \
     "--workers", "2", \
     "--timeout", "120", \
     "--bind", "0.0.0.0:5000", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app.main:app"]
