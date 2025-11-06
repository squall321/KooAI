#!/usr/bin/env python
"""
Celery worker entry point

Usage:
    # Start worker with all queues
    celery -A celery_worker worker --loglevel=info

    # Start worker for specific queue
    celery -A celery_worker worker -Q simulation --loglevel=info

    # Start worker with concurrency
    celery -A celery_worker worker --concurrency=4 --loglevel=info

    # Start beat scheduler
    celery -A celery_worker beat --loglevel=info

    # Start flower monitoring
    celery -A celery_worker flower --port=5555
"""

from src.infrastructure.tasks import celery_app


# Expose celery app for CLI
app = celery_app


if __name__ == "__main__":
    app.start()
