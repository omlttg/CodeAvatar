#!/bin/bash
# run_docker.sh - Safe launch script for CodeAvatar in Docker container
# English: Builds and runs CodeAvatar isolated in Docker with strict CPU and RAM caps.
# Vietnamese: Build và chạy CodeAvatar cô lập trong Docker với giới hạn CPU và RAM an toàn.

IMAGE_NAME="codeavatar-isolated:latest"
CONTAINER_NAME="codeavatar_runner"
HOST_PORT="${PORT:-8005}"

echo "🐳 Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

echo "🛑 Stopping existing container if running..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

echo "🚀 Launching CodeAvatar isolated container on port $HOST_PORT (CPUs: 8, RAM: 16GB)..."
docker run -d \
  --name $CONTAINER_NAME \
  --cpus="8.0" \
  --memory="16g" \
  --memory-swap="16g" \
  -p ${HOST_PORT}:8000 \
  -v "$(pwd)/storage:/app/storage" \
  $IMAGE_NAME

echo "✅ App running at http://localhost:${HOST_PORT} (Isolated from Host OS)"
