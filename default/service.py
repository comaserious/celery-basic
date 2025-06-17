from background.task.default_tasks import add
from background.celery import celery_app
import logging

async def add_service(x, y):
    logging.info(f"add_service : {x=}, {y=}")

    celery_app.send_task(
        "background.task.default_tasks.add", # 작업을 처리할 worker(처리함수 지정)
        kwargs={"x" : x, "y" : y}, # worker 인자값 전달
        queue = "default-add" # 작업을 처리할 queue 지정
    )
    

