from celery import Celery
import os
import asyncio
import time

celery_app = Celery(
    "celery_test_server",
    broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:30000/1"),
    backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:30000/1"),
    include=['background.task.test_tasks', 'background.task.sample_tasks', 'background.task.document_tasks']  # 새로운 경로로 수정
)

