from celery import Celery
import os
import asyncio
import time

celery_app = Celery(
    "celery_test_server",
    include=[
        'background.task.test_tasks', 
        'background.task.sample_tasks', 
        'background.task.document_tasks', 
        'background.task.basic_tasks',
        'background.task.default_tasks'
    ]  # 새로운 경로로 수정
)

celery_app.config_from_object('background.celeryconfig')
