from background.celery import celery_app
import time
import logging
import os

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, soft_time_limit=300, time_limit=420)
def process_document(self, file_path: str, operation: str = "analyze"):
    """기본 문서 처리 Task (3-5분 소요)"""
    task_id = self.request.id
    
    logger.info(f"[{task_id}] 문서 처리 시작: {file_path}")
    
    # 파일 존재 확인
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    # 파일 크기 체크
    file_size = os.path.getsize(file_path)
    logger.info(f"[{task_id}] 파일 크기: {file_size} bytes")
    
    # 처리 시뮬레이션
    steps = ["파일 읽기", "텍스트 추출", "분석", "결과 생성"]
    results = {}
    
    for i, step in enumerate(steps):
        logger.info(f"[{task_id}] {step} 중...")
        time.sleep(1)  # 실제 처리 시뮬레이션
        
        results[step] = f"{step} 완료"
        progress = ((i + 1) / len(steps)) * 100
        logger.info(f"[{task_id}] 진행률: {progress:.0f}%")
    
    logger.info(f"[{task_id}] 문서 처리 완료")
    
    return {
        "file_path": file_path,
        "operation": operation,
        "file_size": file_size,
        "results": results,
        "task_id": task_id,
        "status": "completed"
    }

@celery_app.task(bind=True, soft_time_limit=180, time_limit=240)
def process_document_batch(self, file_paths: list[str]):
    """문서 배치 처리 (최대 10개 파일, 2-3분 소요)"""
    task_id = self.request.id
    
    if len(file_paths) > 10:
        raise ValueError("배치 크기는 10개 파일을 초과할 수 없습니다")
    
    logger.info(f"[{task_id}] 문서 배치 처리 시작: {len(file_paths)}개 파일")
    
    processed_files = []
    failed_files = []
    
    for i, file_path in enumerate(file_paths):
        try:
            # 개별 파일 처리 (간단 버전)
            logger.info(f"[{task_id}] 파일 처리 중: {file_path}")
            time.sleep(0.5)  # 처리 시뮬레이션
            
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                processed_files.append({
                    "file_path": file_path,
                    "file_size": file_size,
                    "status": "success"
                })
            else:
                failed_files.append({
                    "file_path": file_path,
                    "error": "파일이 존재하지 않습니다"
                })
            
            # 진행률 로깅
            progress = ((i + 1) / len(file_paths)) * 100
            logger.info(f"[{task_id}] 배치 진행률: {progress:.0f}% ({i + 1}/{len(file_paths)})")
            
        except Exception as e:
            logger.error(f"[{task_id}] 파일 처리 실패 {file_path}: {str(e)}")
            failed_files.append({
                "file_path": file_path,
                "error": str(e)
            })
    
    success_rate = (len(processed_files) / len(file_paths)) * 100
    logger.info(f"[{task_id}] 배치 처리 완료 - 성공: {len(processed_files)}, 실패: {len(failed_files)}, 성공률: {success_rate:.1f}%")
    
    return {
        "total_files": len(file_paths),
        "processed_files": processed_files,
        "failed_files": failed_files,
        "success_count": len(processed_files),
        "failed_count": len(failed_files),
        "success_rate": success_rate,
        "task_id": task_id
    }

