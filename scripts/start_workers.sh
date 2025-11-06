#!/bin/bash
#
# Start Celery workers for different queues
#
# Usage:
#   ./scripts/start_workers.sh
#

set -e

echo "Starting Celery workers..."

# Start default queue worker
celery -A celery_worker worker \
    -Q default \
    --concurrency=2 \
    --loglevel=info \
    --logfile=logs/celery-default.log \
    --pidfile=logs/celery-default.pid \
    --detach

echo "✓ Started default queue worker"

# Start simulation queue worker (long-running tasks)
celery -A celery_worker worker \
    -Q simulation \
    --concurrency=2 \
    --max-tasks-per-child=10 \
    --loglevel=info \
    --logfile=logs/celery-simulation.log \
    --pidfile=logs/celery-simulation.pid \
    --detach

echo "✓ Started simulation queue worker"

# Start analysis queue worker
celery -A celery_worker worker \
    -Q analysis \
    --concurrency=4 \
    --loglevel=info \
    --logfile=logs/celery-analysis.log \
    --pidfile=logs/celery-analysis.pid \
    --detach

echo "✓ Started analysis queue worker"

# Start cleanup queue worker (low priority)
celery -A celery_worker worker \
    -Q cleanup \
    --concurrency=1 \
    --loglevel=info \
    --logfile=logs/celery-cleanup.log \
    --pidfile=logs/celery-cleanup.pid \
    --detach

echo "✓ Started cleanup queue worker"

# Start high priority queue worker
celery -A celery_worker worker \
    -Q high \
    --concurrency=2 \
    --loglevel=info \
    --logfile=logs/celery-high.log \
    --pidfile=logs/celery-high.pid \
    --detach

echo "✓ Started high priority queue worker"

echo ""
echo "All Celery workers started successfully!"
echo ""
echo "Monitor workers with:"
echo "  celery -A celery_worker inspect active"
echo "  celery -A celery_worker inspect stats"
echo ""
echo "Or start Flower monitoring:"
echo "  celery -A celery_worker flower --port=5555"
