#!/bin/bash
# Build BMP Collector Docker Image

echo "🔨 Building BMP Collector Docker Image"
echo "======================================"

# Build the Docker image using legacy builder
DOCKER_BUILDKIT=0 docker build -t capstone-bmp-collector:latest -f cmd/bmp-collector/Dockerfile .

if [ $? -eq 0 ]; then
    echo "✅ BMP Collector image built successfully!"
    echo "Image: capstone-bmp-collector:latest"
else
    echo "❌ Failed to build BMP Collector image"
    exit 1
fi
