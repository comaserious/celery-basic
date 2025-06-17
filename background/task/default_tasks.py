
from celery import shared_task

import time, logging

@shared_task(
    queue = "default-add"
)
def add(x, y):
    time.sleep(10)

    logging.info(f"{x=}, {y=}")
    logging.info(f"Task Done : {x} + {y} = {x + y}")

    return x + y
    