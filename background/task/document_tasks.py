from background.celery import celery_app
import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from celery import chain, current_task
from celery.exceptions import SoftTimeLimitExceeded
import redis

# Redis 연결 (중간 결과 저장용)
redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    db=2,  # 메인 Celery와 다른 DB 사용
    decode_responses=True
)

# 구조화된 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """문서 처리 상태 관리 클래스"""
    
    @staticmethod
    def save_progress(task_id: str, step: str, data: Dict[Any, Any], progress: int):
        """진행률과 중간 결과 저장"""
        progress_data = {
            "task_id": task_id,
            "current_step": step,
            "progress": progress,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "status": "processing"
        }
        redis_client.setex(f"progress:{task_id}", 3600, json.dumps(progress_data))
        logger.info(f"진행률 저장: {task_id} - {step} ({progress}%)")
    
    @staticmethod
    def get_progress(task_id: str) -> Optional[Dict]:
        """진행률 조회"""
        data = redis_client.get(f"progress:{task_id}")
        return json.loads(data) if data else None
    
    @staticmethod
    def save_intermediate_result(task_id: str, step: str, result: Dict[Any, Any]):
        """중간 결과 저장 (재시작 가능하도록)"""
        key = f"intermediate:{task_id}:{step}"
        redis_client.setex(key, 7200, json.dumps(result))  # 2시간 보관
        logger.info(f"중간 결과 저장: {step} - {task_id}")
    
    @staticmethod
    def get_intermediate_result(task_id: str, step: str) -> Optional[Dict]:
        """중간 결과 조회"""
        key = f"intermediate:{task_id}:{step}"
        data = redis_client.get(key)
        return json.loads(data) if data else None

def send_notification(task_id: str, step: str, status: str, message: str, data: Dict = None):
    """알림 시스템 (이메일/슬랙)"""
    notification_data = {
        "task_id": task_id,
        "step": step,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    
    # 실제로는 이메일/슬랙 API 호출
    if status == "error":
        logger.error(f"🚨 알림: {message}")
        # send_slack_alert(notification_data)
        # send_email_alert(notification_data)
    elif status == "success":
        logger.info(f"✅ 알림: {message}")
        # send_slack_notification(notification_data)
    elif status == "warning":
        logger.warning(f"⚠️ 알림: {message}")
    
    # 알림 히스토리 저장
    redis_client.lpush(f"notifications:{task_id}", json.dumps(notification_data))
    redis_client.expire(f"notifications:{task_id}", 86400)  # 24시간 보관

@celery_app.task(
    bind=True,
    soft_time_limit=120,  # 2분 소프트 타임아웃
    time_limit=180,       # 3분 하드 타임아웃
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def extract_text_advanced(self, file_path: str, resume_data: Dict = None):
    """1단계: 고급 텍스트 추출 (타임아웃, 로깅, 재시작 가능)"""
    task_id = self.request.id
    step_name = "텍스트_추출"
    
    try:
        logger.info(f"[{task_id}] {step_name} 시작: {file_path}")
        
        # 진행률 업데이트
        DocumentProcessor.save_progress(task_id, step_name, {"file_path": file_path}, 0)
        
        # 재시작 가능: 이전 결과 확인
        if resume_data:
            logger.info(f"[{task_id}] 재시작 모드: 이전 데이터 사용")
            DocumentProcessor.save_progress(task_id, step_name, resume_data, 100)
            return resume_data
        
        # 이전 중간 결과 확인
        intermediate = DocumentProcessor.get_intermediate_result(task_id, step_name)
        if intermediate:
            logger.info(f"[{task_id}] 중간 결과 발견: 재사용")
            DocumentProcessor.save_progress(task_id, step_name, intermediate, 100)
            return intermediate
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            error_msg = f"파일을 찾을 수 없습니다: {file_path}"
            send_notification(task_id, step_name, "error", error_msg)
            raise FileNotFoundError(error_msg)
        
        # 파일 크기 확인
        file_size = os.path.getsize(file_path)
        logger.info(f"[{task_id}] 파일 크기: {file_size:,} bytes")
        
        # 진행률 업데이트
        DocumentProcessor.save_progress(task_id, step_name, {"file_path": file_path, "file_size": file_size}, 25)
        
        # 실제 텍스트 추출 작업 시뮬레이션
        extracted_text = f"문서 내용 from {os.path.basename(file_path)} (크기: {file_size} bytes)"
        
        # 처리 시간 시뮬레이션 (타임아웃 테스트용)
        for i in range(10):
            time.sleep(0.2)
            progress = 25 + (i + 1) * 7.5
            DocumentProcessor.save_progress(task_id, step_name, {
                "file_path": file_path,
                "file_size": file_size,
                "processing": f"청크 {i+1}/10 처리 중"
            }, int(progress))
        
        result = {
            "file_path": file_path,
            "text": extracted_text,
            "char_count": len(extracted_text),
            "file_size": file_size,
            "extraction_timestamp": datetime.now().isoformat(),
            "step_completed": step_name
        }
        
        # 중간 결과 저장
        DocumentProcessor.save_intermediate_result(task_id, step_name, result)
        DocumentProcessor.save_progress(task_id, step_name, result, 100)
        
        # 성공 알림
        send_notification(task_id, step_name, "success", 
                         f"텍스트 추출 완료: {len(extracted_text)} characters", result)
        
        logger.info(f"[{task_id}] {step_name} 완료: {len(extracted_text)} characters")
        return result
        
    except SoftTimeLimitExceeded:
        error_msg = f"{step_name} 타임아웃 (120초 초과)"
        send_notification(task_id, step_name, "error", error_msg)
        logger.error(f"[{task_id}] {error_msg}")
        raise
    except Exception as e:
        error_msg = f"{step_name} 실패: {str(e)}"
        send_notification(task_id, step_name, "error", error_msg)
        logger.error(f"[{task_id}] {error_msg}")
        raise

@celery_app.task(
    bind=True, # 
    soft_time_limit=90,
    time_limit=120,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30}
)
def split_text_chunks_advanced(self, extract_result: Dict):
    """2단계: 고급 텍스트 청킹"""
    task_id = self.request.id
    step_name = "텍스트_청킹"
    
    try:
        logger.info(f"[{task_id}] {step_name} 시작")
        
        # 이전 단계 결과 검증
        if not extract_result or "text" not in extract_result:
            error_msg = "이전 단계 결과가 유효하지 않습니다"
            send_notification(task_id, step_name, "error", error_msg)
            raise ValueError(error_msg)
        
        # 진행률 초기화
        DocumentProcessor.save_progress(task_id, step_name, extract_result, 0)
        
        # 재시작 가능: 중간 결과 확인
        intermediate = DocumentProcessor.get_intermediate_result(task_id, step_name)
        if intermediate:
            logger.info(f"[{task_id}] 중간 결과 발견: 재사용")
            DocumentProcessor.save_progress(task_id, step_name, intermediate, 100)
            return intermediate
        
        text = extract_result["text"]
        chunk_size = 500
        
        # 청킹 처리
        chunks = []
        total_length = len(text)
        
        for i in range(0, total_length, chunk_size):
            chunk = text[i:i + chunk_size]
            chunk_data = {
                "chunk_id": i // chunk_size,
                "content": chunk,
                "start_pos": i,
                "end_pos": min(i + chunk_size, total_length),
                "char_count": len(chunk)
            }
            chunks.append(chunk_data)
            
            # 진행률 업데이트
            progress = int((i + chunk_size) / total_length * 80) + 10
            DocumentProcessor.save_progress(task_id, step_name, {
                **extract_result,
                "processing": f"청크 {len(chunks)} 생성 중",
                "chunks_created": len(chunks)
            }, min(progress, 90))
            
            time.sleep(0.1)  # 처리 시간 시뮬레이션
        
        result = {
            **extract_result,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "chunking_timestamp": datetime.now().isoformat(),
            "step_completed": step_name
        }
        
        # 중간 결과 저장
        DocumentProcessor.save_intermediate_result(task_id, step_name, result)
        DocumentProcessor.save_progress(task_id, step_name, result, 100)
        
        # 성공 알림
        send_notification(task_id, step_name, "success", 
                         f"텍스트 청킹 완료: {len(chunks)} chunks", 
                         {"chunk_count": len(chunks)})
        
        logger.info(f"[{task_id}] {step_name} 완료: {len(chunks)} chunks")
        return result
        
    except Exception as e:
        error_msg = f"{step_name} 실패: {str(e)}"
        send_notification(task_id, step_name, "error", error_msg)
        logger.error(f"[{task_id}] {error_msg}")
        raise

@celery_app.task(
    bind=True,
    soft_time_limit=300,  # 5분 (임베딩 생성은 시간이 오래 걸림)
    time_limit=420,       # 7분
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 120}
)
def generate_embeddings_advanced(self, chunk_result: Dict):
    """3단계: 고급 임베딩 생성"""
    task_id = self.request.id
    step_name = "임베딩_생성"
    
    try:
        logger.info(f"[{task_id}] {step_name} 시작")
        
        chunks = chunk_result.get("chunks", [])
        if not chunks:
            error_msg = "청크 데이터가 없습니다"
            send_notification(task_id, step_name, "error", error_msg)
            raise ValueError(error_msg)
        
        # 진행률 초기화
        DocumentProcessor.save_progress(task_id, step_name, chunk_result, 0)
        
        # 재시작 가능: 중간 결과 확인
        intermediate = DocumentProcessor.get_intermediate_result(task_id, step_name)
        if intermediate:
            logger.info(f"[{task_id}] 중간 결과 발견: 재사용")
            DocumentProcessor.save_progress(task_id, step_name, intermediate, 100)
            return intermediate
        
        # 임베딩 생성 (청크별)
        total_chunks = len(chunks)
        embedded_chunks = []
        
        for i, chunk in enumerate(chunks):
            # 실제로는 OpenAI API 호출
            # embedding = openai.embeddings.create(...)
            
            chunk_with_embedding = {
                **chunk,
                "embedding": f"embedding_vector_{chunk['chunk_id']}_{task_id[:8]}",
                "embedding_model": "text-embedding-3-small",
                "embedding_timestamp": datetime.now().isoformat()
            }
            embedded_chunks.append(chunk_with_embedding)
            
            # 진행률 업데이트
            progress = int((i + 1) / total_chunks * 80) + 10
            DocumentProcessor.save_progress(task_id, step_name, {
                **chunk_result,
                "processing": f"임베딩 {i+1}/{total_chunks} 생성 중",
                "embeddings_created": len(embedded_chunks)
            }, progress)
            
            time.sleep(0.3)  # API 호출 시뮬레이션
            
            # 경고: 처리 시간이 오래 걸리는 경우
            if i % 10 == 0 and i > 0:
                send_notification(task_id, step_name, "warning", 
                                f"임베딩 생성 진행 중: {i}/{total_chunks}")
        
        result = {
            **chunk_result,
            "chunks": embedded_chunks,
            "embeddings_generated": True,
            "embedding_count": len(embedded_chunks),
            "embedding_timestamp": datetime.now().isoformat(),
            "step_completed": step_name
        }
        
        # 중간 결과 저장
        DocumentProcessor.save_intermediate_result(task_id, step_name, result)
        DocumentProcessor.save_progress(task_id, step_name, result, 100)
        
        # 성공 알림
        send_notification(task_id, step_name, "success", 
                         f"임베딩 생성 완료: {len(embedded_chunks)} embeddings", 
                         {"embedding_count": len(embedded_chunks)})
        
        logger.info(f"[{task_id}] {step_name} 완료: {len(embedded_chunks)} embeddings")
        return result
        
    except SoftTimeLimitExceeded:
        error_msg = f"{step_name} 타임아웃 (300초 초과)"
        send_notification(task_id, step_name, "error", error_msg)
        logger.error(f"[{task_id}] {error_msg}")
        raise
    except Exception as e:
        error_msg = f"{step_name} 실패: {str(e)}"
        send_notification(task_id, step_name, "error", error_msg)
        logger.error(f"[{task_id}] {error_msg}")
        raise

@celery_app.task(
    bind=True,
    soft_time_limit=60,
    time_limit=90,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30}
)
def save_to_database_advanced(self, embedding_result: Dict):
    """4단계: 고급 데이터베이스 저장"""
    task_id = self.request.id
    step_name = "데이터베이스_저장"
    
    try:
        logger.info(f"[{task_id}] {step_name} 시작")
        
        chunks = embedding_result.get("chunks", [])
        if not chunks:
            error_msg = "임베딩 데이터가 없습니다"
            send_notification(task_id, step_name, "error", error_msg)
            raise ValueError(error_msg)
        
        # 진행률 초기화
        DocumentProcessor.save_progress(task_id, step_name, embedding_result, 0)
        
        # 데이터베이스 저장
        saved_ids = []
        total_chunks = len(chunks)
        
        for i, chunk in enumerate(chunks):
            # 실제 벡터 DB 저장 로직
            doc_id = f"doc_{chunk['chunk_id']}_{task_id[:8]}_{int(time.time())}"
            
            # 실제로는 Pinecone, Weaviate, ChromaDB 등에 저장
            # vector_db.insert(doc_id, chunk['embedding'], chunk['content'])
            
            saved_ids.append(doc_id)
            
            # 진행률 업데이트
            progress = int((i + 1) / total_chunks * 80) + 10
            DocumentProcessor.save_progress(task_id, step_name, {
                **embedding_result,
                "processing": f"저장 {i+1}/{total_chunks}",
                "saved_count": len(saved_ids)
            }, progress)
            
            time.sleep(0.1)  # DB 저장 시뮬레이션
        
        # 최종 결과
        final_result = {
            "task_id": task_id,
            "file_path": embedding_result["file_path"],
            "status": "completed",
            "total_chunks": embedding_result["total_chunks"],
            "saved_document_ids": saved_ids,
            "processing_summary": {
                "char_count": embedding_result["char_count"],
                "chunk_count": embedding_result["total_chunks"],
                "embedding_count": embedding_result["embedding_count"],
                "saved_count": len(saved_ids)
            },
            "completion_timestamp": datetime.now().isoformat(),
            "step_completed": step_name,
            "pipeline_completed": True
        }
        
        # 최종 진행률 업데이트
        DocumentProcessor.save_progress(task_id, "완료", final_result, 100)
        
        # 최종 성공 알림
        send_notification(task_id, "파이프라인_완료", "success", 
                         f"전체 파이프라인 완료! 문서 {len(saved_ids)}개 저장", 
                         final_result["processing_summary"])
        
        logger.info(f"[{task_id}] 전체 파이프라인 완료: {len(saved_ids)} documents")
        return final_result
        
    except Exception as e:
        error_msg = f"{step_name} 실패: {str(e)}"
        send_notification(task_id, step_name, "error", error_msg)
        logger.error(f"[{task_id}] {error_msg}")
        raise

# 진행률 추적 전용 함수
def get_pipeline_progress(task_id: str) -> Dict:
    """파이프라인 전체 진행률 조회"""
    progress_data = DocumentProcessor.get_progress(task_id)
    if not progress_data:
        return {"error": "진행률 정보를 찾을 수 없습니다"}
    
    return {
        "task_id": task_id,
        "current_step": progress_data.get("current_step"),
        "overall_progress": progress_data.get("progress", 0),
        "status": progress_data.get("status"),
        "last_updated": progress_data.get("timestamp"),
        "details": progress_data.get("data", {})
    }

# 알림 히스토리 조회
def get_notification_history(task_id: str) -> list:
    """작업의 알림 히스토리 조회"""
    notifications = redis_client.lrange(f"notifications:{task_id}", 0, -1)
    return [json.loads(notif) for notif in notifications]

# 고급 파이프라인 (모든 기능 포함)
def process_document_pipeline_advanced(file_path: str):
    """고급 문서 처리 파이프라인 - 타임아웃, 로깅, 재시작, 진행률, 알림 모두 포함"""
    pipeline = chain(
        extract_text_advanced.s(file_path),
        split_text_chunks_advanced.s(),
        generate_embeddings_advanced.s(),
        save_to_database_advanced.s()
    )
    
    result = pipeline.apply_async()
    
    # 초기 진행률 설정
    DocumentProcessor.save_progress(result.id, "파이프라인_시작", {
        "file_path": file_path,
        "pipeline_id": result.id,
        "steps": ["텍스트_추출", "텍스트_청킹", "임베딩_생성", "데이터베이스_저장"]
    }, 0)
    
    # 시작 알림
    send_notification(result.id, "파이프라인_시작", "success", 
                     f"문서 처리 파이프라인 시작: {os.path.basename(file_path)}")
    
    return result

# 기존 호환성 유지
@celery_app.task
def split_document(file_path: str):
    """기존 API 호환성을 위한 단순 작업"""
    try:
        logger.info(f"단순 문서 분할 작업: {file_path}")
        time.sleep(2)
        return f"문서 분할 완료: {os.path.basename(file_path)}"
    except Exception as e:
        raise e