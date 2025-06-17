from fastapi import FastAPI, Query, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List, Optional
import json

app = FastAPI(title="Celery Test Harder", description="분산 작업 처리 시스템")

from routers.sample_app import sample_router
from default.app import default_router

routers = [sample_router, default_router]

for router in routers:
    app.include_router(router)


@app.get("/")
async def root():
    return JSONResponse(content={"message": "Celery Test Harder Start reload"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
