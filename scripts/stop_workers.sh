#!/bin/bash
#
# Stop all Celery workers and beat scheduler
#
# Usage:
#   ./scripts/stop_workers.sh
#

set -e

echo "Stopping Celery workers and scheduler..."

# Stop workers gracefully
pkill -f "celery.*worker" || true
echo "✓ Workers stopped"

# Stop beat scheduler
pkill -f "celery.*beat" || true
echo "✓ Beat scheduler stopped"

# Clean up PID files
rm -f logs/celery-*.pid

echo ""
echo "All Celery processes stopped"
