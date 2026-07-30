# Dockerfile - Containerized CodeAvatar Service
# English: Lightweight Debian-based isolation container with resource limits.
# Vietnamese: Container Debian cô lập tài nguyên cho CodeAvatar backend & pipeline.

FROM python:3.11-slim

# Install FFMPEG & system runtime graphics libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements & install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY services/ ./services/
COPY storage/ ./storage/

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "services.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
