# Celery 인스턴스를 하나의 모듈에 구분하여 사용하는 이유

```python
from celery import Celery

celery_app = Celery(
    "celery_test_server",
    broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:30000/1"),
    backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:30000/1"),
    include=['tasks', 'document_tasks']  # 모든 작업 모듈 포함
)
```

celery_app 인 Celery 인스턴스를 사용하기 위해서는 <br>
Celery 인스턴스를 사용하려는 모듈이름을 작성해서 넣으면 <br>
docker-compose 에 command 에 <br>
celery -A tasks.celery_app worker -- loglevel=info 에서 변경하지 않고 <br>
task를 모듈화 하여 확장하기 용이하다 <br>

따라서 celery 인스턴스를 기능별로 모듈을 구분하여 사용하려면 celery 인스턴스를 생성하는 모듈을 따로 생성하여 <br>
사용하는것이 용이하다.
