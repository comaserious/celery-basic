# Celery 인스턴스를 하나의 모듈에 구분하여 사용하는 이유

```python
from celery import Celery

celery_app = Celery(
    "celery_test_server",
    broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:30000/1"),
    backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:30000/1"),
    include=['background.task.test_tasks', 'background.task.document_tasks']  # 새로운 경로로 수정
)

```

celery_app 인 Celery 인스턴스를 사용하기 위해서는 <br>
Celery 인스턴스를 사용하려는 모듈이름을 작성해서 넣으면 <br>
docker-compose 에 command 에 <br>
celery -A tasks.celery_app worker -- loglevel=info 에서 변경하지 않고 <br>
task를 모듈화 하여 확장하기 용이하다 <br>

따라서 celery 인스턴스를 기능별로 모듈을 구분하여 사용하려면 celery 인스턴스를 생성하는 모듈을 따로 생성하여 <br>
사용하는것이 용이하다.

# bind=True
각 task 에 bind=True 를 사용하면 함수에 self 를 넣어야한다.<br>
작업이 큐에 들어갈때 Celery 가 자동으로 UUID 를 생성하고<br>
작업이 실행할 때 self.request.id 로 해당 UUID 접근 할 수 있다.<br>
작업전체의 생명주기 및 상태 값을 확인하고 싶다면 bind=True 옵션을 사용하여<br>
self.request.id 등을 확인할 수 있다.
