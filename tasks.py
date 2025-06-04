from celery import Celery
import os
import asyncio
import time

celery_app = Celery(
    "celery_test_server",
    broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:30000/1"),
    backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:30000/1")
)

@celery_app.task
def add(x, y):
    time.sleep(10)
    return x+y

