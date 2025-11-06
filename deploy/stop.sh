#!/bin/bash
# Stop KooAI services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping KooAI Services${NC}"
echo "=========================================="

# Parse arguments
REMOVE_VOLUMES=${1:-false}

# Stop services
echo -e "${YELLOW}Stopping containers...${NC}"
docker-compose down

# Remove volumes if requested
if [ "${REMOVE_VOLUMES}" = "clean" ] || [ "${REMOVE_VOLUMES}" = "volumes" ]; then
  echo -e "${YELLOW}Removing volumes...${NC}"
  docker-compose down -v
  echo -e "${GREEN}✓ Services stopped and volumes removed${NC}"
else
  echo -e "${GREEN}✓ Services stopped (volumes preserved)${NC}"
fi

echo ""
echo "To start services again:"
echo "  ./deploy/start.sh [profile] [build]"
echo ""
echo "To remove volumes on next stop:"
echo "  ./deploy/stop.sh clean"
