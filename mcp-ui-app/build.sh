#!/bin/bash

# Build and push MCP UI Docker image

set -e

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-your-dockerhub-username}"
IMAGE_NAME="mcp-ui"
TAG="latest"

echo "Building MCP UI Docker image..."

# Build the image
docker build -t ${IMAGE_NAME}:${TAG} .

# Tag for Docker Hub
docker tag ${IMAGE_NAME}:${TAG} ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}

echo "Pushing to Docker Hub..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}

echo "Successfully built and pushed ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
echo ""
echo "Update your deployment manifests to use: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
echo "Or set environment variable: MCP_UI_IMAGE=${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"