# 🚀 Celery Test Harder Project

## 📋 프로젝트 개요

이 프로젝트는 **Celery**를 사용한 분산 작업 처리 시스템으로, 모듈화된 구조와 고급 기능들을 포함하고 있습니다.

## 🏗️ 프로젝트 구조

```
celery_test_harder/
├── 📂 background/                    # 백그라운드 작업 패키지
│   ├── 📄 __init__.py               # 패키지 초기화
│   ├── 📄 celery.py                 # Celery 앱 설정
│   └── 📂 task/                     # 작업 모듈들
│       ├── 📄 __init__.py           # 패키지 초기화
│       ├── 📄 test_tasks.py         # 기본 테스트 작업들
│       └── 📄 document_tasks.py     # 문서 처리 작업들
├── 📄 main.py                       # FastAPI 메인 애플리케이션
├── 📄 sample_app.py                 # 샘플 라우터
├── 📄 docker-compose.yml            # Docker 설정
├── 📄 Dockerfile                    # Docker 이미지 설정
├── 📄 requirements.txt              # Python 의존성
└── 📂 data/                         # 파일 저장소
```

---

## 🔧 Celery 인스턴스 모듈화

### ❓ 왜 Celery 인스턴스를 별도 모듈로 분리하나요?

```python
# 📁 background/celery.py
from celery import Celery

celery_app = Celery(
    "celery_test_server",
    broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:30000/1"),
    backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:30000/1"),
    include=['background.task.test_tasks', 'background.task.document_tasks']
)
```

### ✅ 장점

| 장점 | 설명 |
|------|------|
| 🔄 **확장성** | 새로운 작업 모듈을 쉽게 추가 가능 |
| 🏗️ **모듈화** | 기능별로 작업을 분리하여 관리 용이 |
| ⚙️ **설정 일관성** | Docker Compose 명령어 변경 없이 확장 |
| 🧪 **테스트 용이** | 각 모듈별로 독립적인 테스트 가능 |

### 🐳 Docker Compose 설정

```yaml
# docker-compose.yml에서 변경 없이 모듈 확장 가능
worker:
  command: celery -A background.celery.celery_app worker --loglevel=info
```

---

## 🔗 bind=True 옵션 활용

### 📚 기본 개념

각 작업에 `bind=True`를 사용하면 작업 함수에 `self` 매개변수가 추가됩니다.

```python
@celery_app.task(bind=True)
def my_task(self, data):
    task_id = self.request.id  # 🆔 고유 작업 ID 접근
    # 작업 로직...
```

### ⚡ 생명주기

```mermaid
graph LR
    A[📨 작업 요청] --> B[🔢 UUID 생성]
    B --> C[⚙️ 작업 실행]
    C --> D[🆔 self.request.id 접근]
    D --> E[✅ 작업 완료]
```

1. **작업 큐 진입** → Celery가 자동으로 UUID 생성
2. **작업 실행** → `self.request.id`로 UUID 접근 가능
3. **전체 생명주기** → 동일한 ID로 상태 추적

### 🎯 활용 사례

| 사용 목적 | 코드 예시 |
|-----------|-----------|
| **로깅** | `logger.info(f"[{self.request.id}] 작업 시작")` |
| **진행률 추적** | `save_progress(self.request.id, step, progress)` |
| **캐시 키** | `cache_key = f"result:{self.request.id}"` |
| **파일명** | `filename = f"output_{self.request.id[:8]}.txt"` |

### 🔍 self.request 속성들

```python
@celery_app.task(bind=True)
def detailed_task(self, data):
    # 📊 사용 가능한 모든 정보
    info = {
        "task_id": self.request.id,           # 🆔 작업 고유 ID
        "task_name": self.request.task,       # 📛 작업 이름
        "retries": self.request.retries,      # 🔄 재시도 횟수
        "args": self.request.args,            # 📝 위치 인수
        "kwargs": self.request.kwargs,        # 🔧 키워드 인수
        "group": self.request.group,          # 👥 그룹 ID
        "root_id": self.request.root_id,      # 🌳 루트 작업 ID
        "parent_id": self.request.parent_id,  # 👨‍👩‍👧‍👦 부모 작업 ID
    }
    return info
```

---

## 🚀 실행 방법

### 🐳 Docker로 실행

```bash
# 컨테이너 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d
```

### 🌐 접속 정보

| 서비스 | URL | 설명 |
|--------|-----|------|
| **FastAPI** | http://localhost:8000 | 🌐 메인 API 서버 |
| **Flower** | http://localhost:5555 | 🌸 Celery 모니터링 |
| **Redis** | localhost:6379 | 🔴 메시지 브로커 |

---

## 📖 API 엔드포인트

### 🧪 기본 테스트

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/add` | ➕ 덧셈 작업 |
| `POST` | `/test-request-info` | 🔍 self.request 정보 확인 |
| `GET` | `/result/{task_id}` | 📊 작업 결과 조회 |

### 🔗 고급 작업 (Chain, Group, Chord)

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/chain` | ⛓️ 순차 실행 작업 |
| `POST` | `/group` | 👥 병렬 실행 작업 |
| `POST` | `/chord` | 🎵 병렬 + 콜백 작업 |

---

## 🛠️ 주요 기능

- ✅ **모듈화된 Celery 구조**
- ✅ **실시간 작업 상태 추적**
- ✅ **Chain, Group, Chord 패턴 지원**
- ✅ **Docker 컨테이너 지원**
- ✅ **Flower 모니터링 도구**
- ✅ **Redis 백엔드**

---

## 📝 참고사항

> 💡 **팁**: `bind=True` 옵션을 사용하면 작업의 전체 생명주기와 상태를 효과적으로 관리할 수 있습니다.

> ⚠️ **주의**: production 환경에서는 적절한 보안 설정과 환경변수 관리가 필요합니다.
