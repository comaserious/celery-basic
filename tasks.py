from celery import Celery
import os
import asyncio
import time

celery_app = Celery(
    "celery_test_server",
    broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:30000/1"),
    backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:30000/1"),
    include=['tasks', 'document_tasks']  # 모든 작업 모듈 포함
)

@celery_app.task
def add(x, y):
    time.sleep(10)
    return x + y

@celery_app.task
def multiply(x, y):
    time.sleep(10)
    return x * y

@celery_app.task
def finalize(result):
    return f"[RESULT]: {result}"

