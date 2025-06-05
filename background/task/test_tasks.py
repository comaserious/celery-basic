from background.celery import celery_app
import time
import logging

logger = logging.getLogger(__name__)

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

# 실무 적정 크기 Task 예시들
@celery_app.task(bind=True, soft_time_limit=180, time_limit=240)
def process_user_batch(self, user_ids: list[int]):
    """✅ 적정 크기: 100명 사용자 배치 처리 (2-3분 소요)"""
    task_id = self.request.id
    
    if len(user_ids) > 100:
        raise ValueError("배치 크기가 100을 초과할 수 없습니다")
    
    logger.info(f"[{task_id}] 사용자 배치 처리 시작: {len(user_ids)}명")
    
    processed_count = 0
    results = []
    
    for i, user_id in enumerate(user_ids):
        # 사용자별 처리 (0.5-2초 소요)
        time.sleep(0.1)  # 실제 처리 시뮬레이션
        
        result = {
            "user_id": user_id,
            "processed_at": time.time(),
            "status": "success"
        }
        results.append(result)
        processed_count += 1
        
        # 진행률 로깅 (20%마다)
        if (i + 1) % 20 == 0:
            progress = ((i + 1) / len(user_ids)) * 100
            logger.info(f"[{task_id}] 진행률: {progress:.1f}% ({i + 1}/{len(user_ids)})")
    
    logger.info(f"[{task_id}] 사용자 배치 처리 완료: {processed_count}명")
    return {
        "processed_count": processed_count,
        "results": results,
        "task_id": task_id
    }

@celery_app.task(bind=True, soft_time_limit=300, time_limit=420)
def send_email_campaign(self, email_list: list[str], template_id: str):
    """✅ 적정 크기: 이메일 캠페인 발송 (3-5분 소요)"""
    task_id = self.request.id
    max_batch_size = 200
    
    if len(email_list) > max_batch_size:
        raise ValueError(f"이메일 배치 크기가 {max_batch_size}을 초과할 수 없습니다")
    
    logger.info(f"[{task_id}] 이메일 캠페인 시작: {len(email_list)}개 주소")
    
    sent_count = 0
    failed_count = 0
    results = []
    
    for i, email in enumerate(email_list):
        try:
            # 이메일 발송 시뮬레이션 (0.5-1초 소요)
            time.sleep(0.05)
            
            # 90% 성공률 시뮬레이션
            success = (i % 10) != 0
            
            if success:
                sent_count += 1
                status = "sent"
            else:
                failed_count += 1
                status = "failed"
                
            results.append({
                "email": email,
                "status": status,
                "sent_at": time.time()
            })
            
            # 진행률 로깅 (50개마다)
            if (i + 1) % 50 == 0:
                progress = ((i + 1) / len(email_list)) * 100
                logger.info(f"[{task_id}] 이메일 발송 진행률: {progress:.1f}% (성공: {sent_count}, 실패: {failed_count})")
                
        except Exception as e:
            failed_count += 1
            logger.error(f"[{task_id}] 이메일 발송 실패 {email}: {str(e)}")
    
    success_rate = (sent_count / len(email_list)) * 100
    logger.info(f"[{task_id}] 이메일 캠페인 완료 - 성공: {sent_count}, 실패: {failed_count}, 성공률: {success_rate:.1f}%")
    
    return {
        "total_emails": len(email_list),
        "sent_count": sent_count,
        "failed_count": failed_count,
        "success_rate": success_rate,
        "template_id": template_id,
        "results": results,
        "task_id": task_id
    }

@celery_app.task(bind=True, soft_time_limit=240, time_limit=300) 
def generate_report_chunk(self, date_range: dict, chunk_id: int):
    """✅ 적정 크기: 리포트 청크 생성 (3-4분 소요)"""
    task_id = self.request.id
    
    logger.info(f"[{task_id}] 리포트 청크 {chunk_id} 생성 시작")
    
    # 데이터 조회 시뮬레이션 (30초)
    logger.info(f"[{task_id}] 데이터 조회 중...")
    time.sleep(0.3)
    
    # 데이터 처리 시뮬레이션 (2분)
    logger.info(f"[{task_id}] 데이터 처리 중...")
    for i in range(20):
        time.sleep(0.1)  # 실제로는 데이터 가공
        if (i + 1) % 5 == 0:
            progress = ((i + 1) / 20) * 100
            logger.info(f"[{task_id}] 데이터 처리 진행률: {progress:.0f}%")
    
    # 리포트 생성 시뮬레이션 (1분)
    logger.info(f"[{task_id}] 리포트 생성 중...")
    time.sleep(0.2)
    
    report_data = {
        "chunk_id": chunk_id,
        "date_range": date_range,
        "record_count": 1000,  # 시뮬레이션
        "generated_at": time.time(),
        "file_size": "2.5MB",
        "task_id": task_id
    }
    
    logger.info(f"[{task_id}] 리포트 청크 {chunk_id} 생성 완료")
    return report_data

# 큰 작업을 적절히 분할하는 예시
def start_large_user_processing(all_user_ids: list[int]):
    """큰 작업을 적절한 크기로 분할하여 실행"""
    batch_size = 100  # 적정 배치 크기
    task_ids = []
    
    for i in range(0, len(all_user_ids), batch_size):
        batch = all_user_ids[i:i + batch_size]
        task = process_user_batch.delay(batch)
        task_ids.append(task.id)
        logger.info(f"사용자 배치 {i//batch_size + 1} 시작: {len(batch)}명 (Task ID: {task.id})")
    
    return task_ids

def start_bulk_email_campaign(all_emails: list[str], template_id: str):
    """대규모 이메일을 적절한 크기로 분할하여 발송"""
    batch_size = 200  # 적정 배치 크기
    task_ids = []
    
    for i in range(0, len(all_emails), batch_size):
        batch = all_emails[i:i + batch_size]
        task = send_email_campaign.delay(batch, template_id)
        task_ids.append(task.id)
        logger.info(f"이메일 배치 {i//batch_size + 1} 시작: {len(batch)}개 (Task ID: {task.id})")
    
    return task_ids
