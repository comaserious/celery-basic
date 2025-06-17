from fastapi import APIRouter

document_router = APIRouter(prefix="/document", tags=["document 학습 엔드포인트"])

from background.celery import celery_app


