from celery import Celery
import os
import asyncio
import time

celery_app = Celery(
    "celery_test_server",
    broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1"), # 브로커 설정 메시지큐 기반으로 동작을 하기위해 큐저장용 (broker)
    backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"), # task 실행 결과를 추적하기 위해서 저장하기 위한 공간 (backend)
    include=[
        'background.task.test_tasks', 
        'background.task.sample_tasks', 
        'background.task.document_tasks', 
        'background.task.basic_tasks',
    ]  # 새로운 경로로 수정
)

