#!/bin/bash
#
# Start Celery Beat scheduler for periodic tasks
#
# Usage:
#   ./scripts/start_beat.sh
#

set -e

echo "Starting Celery Beat scheduler..."

celery -A celery_worker beat \
    --loglevel=info \
    --logfile=logs/celery-beat.log \
    --pidfile=logs/celery-beat.pid \
    --detach

echo "✓ Celery Beat scheduler started"
echo ""
echo "Scheduled tasks:"
echo "  - cleanup-old-files: Daily at 2:00 AM"
echo "  - cleanup-expired-results: Every 6 hours"
echo "  - health-check: Every 5 minutes"
echo ""
echo "Monitor schedule with:"
echo "  celery -A celery_worker inspect scheduled"
