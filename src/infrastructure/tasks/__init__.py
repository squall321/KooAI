"""
Asynchronous task processing infrastructure

Provides Celery-based background task processing for:
- Large file parsing
- Complex analysis operations
- Scheduled cleanup tasks
- Email notifications
"""

from .celery_app import celery_app, create_celery_app
from .config import CeleryConfig, get_celery_config

__all__ = [
    "celery_app",
    "create_celery_app",
    "CeleryConfig",
    "get_celery_config",
]
