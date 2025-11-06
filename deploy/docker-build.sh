#!/bin/bash
# Build Docker image for KooAI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building KooAI Docker Image${NC}"
echo "=========================================="

# Parse arguments
TAG=${1:-latest}
PLATFORM=${2:-linux/amd64}

echo -e "${YELLOW}Configuration:${NC}"
echo "  Tag: ${TAG}"
echo "  Platform: ${PLATFORM}"
echo ""

# Build image
echo -e "${GREEN}Building Docker image...${NC}"
docker build \
  --platform ${PLATFORM} \
  --tag kooai:${TAG} \
  --tag kooai:latest \
  -f Dockerfile \
  .

# Check build success
if [ $? -eq 0 ]; then
  echo ""
  echo -e "${GREEN}✓ Docker image built successfully!${NC}"
  echo ""
  echo "Image details:"
  docker images kooai:${TAG}
  echo ""
  echo "To run the image:"
  echo "  docker run -p 8000:8000 kooai:${TAG}"
else
  echo -e "${RED}✗ Docker build failed!${NC}"
  exit 1
fi
