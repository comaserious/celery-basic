from background.celery import celery_app
import time
import logging
import os

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, soft_time_limit=300, time_limit=420)
def process_document(self, file_path: str, operation: str = "analyze"):
    """단일 문서 처리 작업"""
    task_id = self.request.id
    logger.info(f"[{task_id}] 문서 처리 시작: {file_path}, 작업: {operation}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    # 문서 처리 시뮬레이션
    for i in range(10):
        time.sleep(0.3)  # 실제 처리 시뮬레이션
        progress = (i + 1) * 10
        logger.info(f"[{task_id}] 진행률: {progress}%")
    
    result = {
        "file_path": file_path,
        "operation": operation,
        "status": "completed",
        "processed_at": time.time(),
        "task_id": task_id
    }
    
    logger.info(f"[{task_id}] 문서 처리 완료: {file_path}")
    return result

@celery_app.task(bind=True, soft_time_limit=180, time_limit=240)
def process_document_batch(self, file_paths: list):
    """문서 배치 처리 작업"""
    task_id = self.request.id
    logger.info(f"[{task_id}] 문서 배치 처리 시작: {len(file_paths)}개 파일")
    
    if len(file_paths) > 10:
        raise ValueError("배치 크기는 10개 파일을 초과할 수 없습니다")
    
    results = []
    for i, file_path in enumerate(file_paths):
        try:
            # 각 파일 처리 시뮬레이션
            time.sleep(0.2)
            
            if os.path.exists(file_path):
                result = {
                    "file_path": file_path,
                    "status": "success",
                    "processed_at": time.time()
                }
            else:
                result = {
                    "file_path": file_path,
                    "status": "failed",
                    "error": "파일을 찾을 수 없음"
                }
            
            results.append(result)
            progress = ((i + 1) / len(file_paths)) * 100
            logger.info(f"[{task_id}] 진행률: {progress:.1f}% ({i + 1}/{len(file_paths)})")
            
        except Exception as e:
            results.append({
                "file_path": file_path,
                "status": "failed",
                "error": str(e)
            })
    
    successful = sum(1 for r in results if r["status"] == "success")
    logger.info(f"[{task_id}] 문서 배치 처리 완료: {successful}/{len(file_paths)} 성공")
    
    return {
        "total_files": len(file_paths),
        "successful": successful,
        "failed": len(file_paths) - successful,
        "results": results,
        "task_id": task_id
    }

