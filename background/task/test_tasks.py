from background.celery import celery_app

import time

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

# self.request 예시를 위한 작업
@celery_app.task(bind=True)
def show_request_info(self, message: str):
    """self.request 객체의 다양한 정보를 보여주는 예시"""
    
    # 📋 self.request 객체에서 사용 가능한 정보들
    request_info = {
        "task_id": self.request.id,                    # 작업 고유 ID (UUID)
        "task_name": self.request.task,                # 작업 함수 이름
        "args": self.request.args,                     # 위치 인수들
        "kwargs": self.request.kwargs,                 # 키워드 인수들
        "retries": self.request.retries,               # 현재 재시도 횟수
        "is_eager": self.request.is_eager,             # 즉시 실행 모드 여부
        "eta": self.request.eta,                       # 예약된 실행 시간
        "expires": self.request.expires,               # 만료 시간
        "group": self.request.group,                   # 그룹 ID (group 작업인 경우)
        "chord": self.request.chord,                   # 코드 ID (chord 작업인 경우)
        "root_id": self.request.root_id,               # 루트 작업 ID
        "parent_id": self.request.parent_id,           # 부모 작업 ID
        "correlation_id": self.request.correlation_id, # 상관관계 ID
        "origin": self.request.origin,                 # 작업이 시작된 워커
        "delivery_info": self.request.delivery_info,   # 메시지 전달 정보
    }
    
    print(f"📨 작업 요청 정보:")
    for key, value in request_info.items():
        print(f"  {key}: {value}")
    
    return {
        "message": f"처리완료: {message}",
        "task_info": request_info
    }
