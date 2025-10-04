"""Celery application configuration"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "rag_anything",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.document_tasks",
        "app.tasks.embedding_tasks",
        "app.tasks.graph_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_send_sent_event=True,
    task_routes={
        "app.tasks.document_tasks.*": {"queue": "documents"},
        "app.tasks.embedding_tasks.*": {"queue": "embeddings"},
        "app.tasks.graph_tasks.*": {"queue": "graph"},
    },
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
)

# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-tasks": {
        "task": "app.tasks.document_tasks.cleanup_old_tasks",
        "schedule": 3600.0,  # Every hour
    },
}
