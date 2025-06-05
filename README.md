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

---

## ⚖️ Task 크기 결정 가이드라인

### 🎯 적절한 Task 크기

| 구분 | 권장 기준 | 이유 |
|------|-----------|------|
| **⏱️ 실행 시간** | 30초 ~ 5분 | 너무 짧으면 오버헤드, 너무 길면 모니터링 어려움 |
| **💾 메모리 사용** | < 500MB | 메모리 부족으로 인한 실패 방지 |
| **📦 데이터 크기** | < 100MB | Redis/RabbitMQ 메시지 크기 제한 |
| **🔄 재시도 빈도** | 낮음 | 실패 시 재시도 비용 최소화 |

### ✅ 좋은 Task 예시

```python
# ✅ 적절한 크기 - 단일 문서 처리
@celery_app.task(bind=True)
def process_single_document(self, file_path: str):
    """하나의 문서를 처리 (1-3분 소요)"""
    # 1. 파일 읽기
    # 2. 텍스트 추출 
    # 3. 간단한 변환
    # 4. 결과 저장
    pass

# ✅ 적절한 크기 - 소규모 이메일 발송
@celery_app.task(bind=True) 
def send_email_batch(self, emails: list[str]):
    """최대 100개 이메일 발송 (2-4분 소요)"""
    if len(emails) > 100:
        raise ValueError("배치 크기 초과")
    # 이메일 발송 로직
    pass
```

### ❌ 피해야 할 Task 예시

```python
# ❌ 너무 큰 Task - 전체 데이터베이스 처리
@celery_app.task
def process_entire_database():
    """❌ 수시간 소요, 실패 시 처음부터 재시작"""
    for record in get_all_records():  # 수백만 건
        process_record(record)

# ❌ 너무 작은 Task - 단순 계산
@celery_app.task
def add_two_numbers(a: int, b: int):
    """❌ 1초도 안 걸리는 작업, 오버헤드가 더 큼"""
    return a + b

# ❌ 메모리 과다 사용
@celery_app.task
def load_huge_file():
    """❌ 수 GB 파일을 메모리에 로드"""
    return open('huge_file.txt').read()  # 메모리 부족 위험
```

### 🏗️ Task 분할 전략

#### 1. **시간 기반 분할**
```python
# 큰 작업을 시간 단위로 분할
@celery_app.task(bind=True)
def process_data_chunk(self, start_id: int, end_id: int):
    """1000개씩 처리 (약 2분 소요)"""
    records = get_records(start_id, end_id)
    for record in records:
        process_record(record)

# 전체 작업을 여러 청크로 분할하여 실행
def start_bulk_processing():
    total_records = get_total_count()
    chunk_size = 1000
    
    for start in range(0, total_records, chunk_size):
        end = min(start + chunk_size, total_records)
        process_data_chunk.delay(start, end)
```

#### 2. **크기 기반 분할**
```python
@celery_app.task(bind=True)
def process_file_batch(self, file_paths: list[str]):
    """최대 50MB 파일들을 배치 처리"""
    total_size = sum(os.path.getsize(f) for f in file_paths)
    if total_size > 50 * 1024 * 1024:  # 50MB 제한
        raise ValueError("배치 크기 초과")
    
    for file_path in file_paths:
        process_single_file(file_path)
```

#### 3. **단계별 분할 (Chain 활용)**
```python
# 큰 작업을 여러 단계로 분할
@celery_app.task(bind=True)
def extract_data(self, source: str):
    """1단계: 데이터 추출 (2분)"""
    pass

@celery_app.task(bind=True) 
def transform_data(self, raw_data: dict):
    """2단계: 데이터 변환 (3분)"""
    pass

@celery_app.task(bind=True)
def load_data(self, transformed_data: dict):
    """3단계: 데이터 저장 (1분)"""
    pass

# ETL 파이프라인으로 실행
def run_etl_pipeline(source: str):
    pipeline = chain(
        extract_data.s(source),
        transform_data.s(),
        load_data.s()
    )
    return pipeline.apply_async()
```

### 📊 실무 기준 및 모니터링

#### **⏱️ 시간별 분류**

| 작업 시간 | 분류 | 권장사항 |
|-----------|------|----------|
| **< 10초** | 🟥 너무 짧음 | 동기 처리 또는 배치로 묶기 |
| **10초 ~ 30초** | 🟨 짧음 | 간단한 작업만 적합 |
| **30초 ~ 5분** | 🟢 **최적** | 가장 이상적인 크기 |
| **5분 ~ 15분** | 🟨 긴 편 | 진행률 추적 필수 |
| **> 15분** | 🟥 너무 김 | 분할 검토 필요 |

#### **🔍 모니터링 지표**

```python
@celery_app.task(bind=True, soft_time_limit=300, time_limit=420)
def monitored_task(self, data):
    """모니터링이 포함된 Task"""
    start_time = time.time()
    task_id = self.request.id
    
    try:
        # 작업 수행
        result = process_data(data)
        
        # 성능 메트릭 기록
        execution_time = time.time() - start_time
        logger.info(f"[{task_id}] 실행시간: {execution_time:.2f}초")
        
        if execution_time > 300:  # 5분 초과 시 경고
            logger.warning(f"[{task_id}] 실행시간 초과: {execution_time:.2f}초")
            
        return result
        
    except Exception as e:
        logger.error(f"[{task_id}] 실행 실패: {str(e)}")
        raise
```

### 💡 실무 팁

1. **🧪 테스트 기반 결정**: 실제 데이터로 성능 테스트 후 크기 결정
2. **📈 점진적 확장**: 작은 크기로 시작해서 점진적으로 크기 증가
3. **🔄 유연한 설계**: 런타임에 배치 크기 조정 가능하도록 설계
4. **📊 지속적 모니터링**: Flower, Prometheus 등으로 성능 모니터링
5. **⚡ 실패 격리**: 한 Task 실패가 전체 파이프라인에 영향 주지 않도록

---
