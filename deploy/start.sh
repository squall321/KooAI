#!/bin/bash
# Start KooAI services using docker-compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting KooAI Services${NC}"
echo "=========================================="

# Parse arguments
PROFILE=${1:-default}
BUILD=${2:-false}

echo -e "${YELLOW}Configuration:${NC}"
echo "  Profile: ${PROFILE}"
echo "  Build images: ${BUILD}"
echo ""

# Create necessary directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p data logs

# Build images if requested
if [ "${BUILD}" = "build" ] || [ "${BUILD}" = "true" ]; then
  echo -e "${BLUE}Building Docker images...${NC}"
  docker-compose build
fi

# Start services based on profile
case ${PROFILE} in
  production)
    echo -e "${BLUE}Starting production services (with Nginx)...${NC}"
    docker-compose --profile production up -d
    ;;
  monitoring)
    echo -e "${BLUE}Starting services with monitoring...${NC}"
    docker-compose --profile monitoring up -d
    ;;
  all)
    echo -e "${BLUE}Starting all services...${NC}"
    docker-compose --profile production --profile monitoring up -d
    ;;
  *)
    echo -e "${BLUE}Starting core services...${NC}"
    docker-compose up -d postgres redis api
    ;;
esac

# Wait for services to be healthy
echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 5

# Check service status
echo ""
echo -e "${GREEN}Service Status:${NC}"
docker-compose ps

# Show logs for API service
echo ""
echo -e "${BLUE}Recent API logs:${NC}"
docker-compose logs --tail=20 api

echo ""
echo -e "${GREEN}✓ KooAI services started successfully!${NC}"
echo ""
echo "Access points:"
echo "  API:          http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health"
if [[ ${PROFILE} == "production" ]] || [[ ${PROFILE} == "all" ]]; then
  echo "  Nginx:        http://localhost:80"
fi
if [[ ${PROFILE} == "monitoring" ]] || [[ ${PROFILE} == "all" ]]; then
  echo "  Prometheus:   http://localhost:9090"
  echo "  Grafana:      http://localhost:3000 (admin/admin)"
fi
echo ""
echo "To view logs:"
echo "  docker-compose logs -f [service_name]"
echo ""
echo "To stop services:"
echo "  docker-compose down"
