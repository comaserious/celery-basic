from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

import os, aiofiles
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

document_router = APIRouter(prefix="/document")

from document_tasks import (
    split_document, 
    process_document_pipeline_advanced, 
    get_pipeline_progress,
    get_notification_history
)
from tasks import celery_app

@document_router.post("/learn_file")
async def learn_file(
    user_id : str = Form(...),
    file : UploadFile = File(...),
):
    try:
        logger.info(f"파일 업로드 시작 - user_id: {user_id}, filename: {file.filename}")
        
        upload_dir = f"data/uploads/{user_id}"
        logger.info(f"업로드 디렉토리: {upload_dir}")
        
        # 디렉토리 생성
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"디렉토리 생성 완료: {upload_dir}")

        file_path = os.path.join(upload_dir, file.filename)
        logger.info(f"파일 저장 경로: {file_path}")
        
        # 파일 내용 읽기
        content = await file.read()
        logger.info(f"파일 크기: {len(content)} bytes")
        
        # 파일 저장
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # 파일 저장 확인
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            logger.info(f"파일 저장 성공! 크기: {file_size} bytes")
        else:
            logger.error(f"파일 저장 실패! 경로: {file_path}")
            return JSONResponse(content={"error": "파일 저장 실패"}, status_code=500)

        # Celery 작업 시작
        result = split_document.delay(file_path)
        logger.info(f"Celery 작업 시작 - task_id: {result.id}")

        return JSONResponse(content={
            "message": "File uploaded successfully", 
            "task_id": result.id,
            "file_path": file_path,
            "file_size": len(content)
        }, status_code=200)
        
    except Exception as e:
        logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@document_router.get("/get_result/{task_id}")
async def get_result(task_id : str):
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "type": "single",
            "status": result.status,
            "result": result.result if result.ready() else None,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else False,
            "failed": result.failed() if result.ready() else False
        }
    except Exception as e:
        raise e

@document_router.post("/process_pipeline")
async def process_document_with_pipeline(
    user_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Chain을 사용한 전체 문서 처리 파이프라인"""
    try:
        logger.info(f"파이프라인 처리 시작 - user_id: {user_id}, filename: {file.filename}")
        
        upload_dir = f"data/uploads/{user_id}"
        logger.info(f"업로드 디렉토리: {upload_dir}")
        
        # 디렉토리 생성
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"디렉토리 생성 완료: {upload_dir}")

        file_path = os.path.join(upload_dir, file.filename)
        logger.info(f"파일 저장 경로: {file_path}")
        
        # 파일 내용 읽기
        content = await file.read()
        logger.info(f"파일 크기: {len(content)} bytes")
        
        # 파일 저장
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # 파일 저장 확인
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            logger.info(f"파일 저장 성공! 크기: {file_size} bytes")
        else:
            logger.error(f"파일 저장 실패! 경로: {file_path}")
            return JSONResponse(content={"error": "파일 저장 실패"}, status_code=500)

        # Chain 파이프라인 시작
        pipeline_result = process_document_pipeline_advanced(file_path)
        logger.info(f"파이프라인 시작 - chain_id: {pipeline_result.id}")

        return JSONResponse(content={
            "message": "Document processing pipeline started successfully", 
            "chain_id": pipeline_result.id,
            "file_path": file_path,
            "file_size": len(content),
            "pipeline_steps": [
                "1. 텍스트 추출",
                "2. 텍스트 청킹", 
                "3. 임베딩 생성",
                "4. 데이터베이스 저장"
            ]
        }, status_code=200)
        
    except Exception as e:
        logger.error(f"파이프라인 처리 중 오류 발생: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@document_router.post("/process_advanced")
async def process_document_advanced(
    user_id: str = Form(...),
    file: UploadFile = File(...),
):
    """고급 문서 처리 파이프라인 - 타임아웃, 로깅, 재시작, 진행률, 알림 모두 포함"""
    try:
        logger.info(f"고급 파이프라인 처리 시작 - user_id: {user_id}, filename: {file.filename}")
        
        upload_dir = f"data/uploads/{user_id}"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        
        # 파일 저장
        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # 파일 저장 확인
        if not os.path.exists(file_path):
            return JSONResponse(content={"error": "파일 저장 실패"}, status_code=500)

        # 고급 파이프라인 시작
        pipeline_result = process_document_pipeline_advanced(file_path)
        logger.info(f"고급 파이프라인 시작 - chain_id: {pipeline_result.id}")

        return JSONResponse(content={
            "message": "Advanced document processing pipeline started", 
            "chain_id": pipeline_result.id,
            "file_path": file_path,
            "file_size": len(content),
            "features": [
                "단계별 타임아웃 설정",
                "구조화된 로깅",
                "중간 결과 저장 (재시작 가능)",
                "실시간 진행률 추적",
                "알림 시스템 연동"
            ],
            "endpoints": {
                "progress": f"/document/progress/{pipeline_result.id}",
                "notifications": f"/document/notifications/{pipeline_result.id}",
                "result": f"/chain-result/{pipeline_result.id}"
            }
        }, status_code=200)
        
    except Exception as e:
        logger.error(f"고급 파이프라인 처리 중 오류 발생: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@document_router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """실시간 진행률 추적"""
    try:
        progress_data = get_pipeline_progress(task_id)
        return JSONResponse(content=progress_data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@document_router.get("/notifications/{task_id}")
async def get_notifications(task_id: str):
    """알림 히스토리 조회"""
    try:
        notifications = get_notification_history(task_id)
        return JSONResponse(content={
            "task_id": task_id,
            "notification_count": len(notifications),
            "notifications": notifications
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@document_router.get("/status/{task_id}")
async def get_comprehensive_status(task_id: str):
    """종합 상태 조회 (진행률 + 알림 + 결과)"""
    try:
        # 진행률 정보
        progress_data = get_pipeline_progress(task_id)
        
        # 알림 히스토리
        notifications = get_notification_history(task_id)
        
        # Celery 작업 상태
        celery_result = celery_app.AsyncResult(task_id)
        
        return JSONResponse(content={
            "task_id": task_id,
            "comprehensive_status": {
                "progress": progress_data,
                "celery_status": {
                    "status": celery_result.status,
                    "ready": celery_result.ready(),
                    "successful": celery_result.successful() if celery_result.ready() else False,
                    "result": celery_result.result if celery_result.ready() else None
                },
                "notifications": {
                    "count": len(notifications),
                    "latest": notifications[0] if notifications else None,
                    "history": notifications[:5]  # 최근 5개만
                }
            }
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
