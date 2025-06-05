from fastapi import FastAPI, Query
from typing import List, Optional

app = FastAPI()

from sample_app import sample_router
routers = [sample_router]

for router in routers:
    app.include_router(router)

from pydantic import BaseModel

class AddRequest(BaseModel):
    x : int
    y: int

from background.celery import celery_app
from background.task.test_tasks import add, multiply, finalize, show_request_info
from celery import chain, group, chord
from celery.result import GroupResult

@app.post("/add")
async def celery_add(req: AddRequest):
    task = add.delay(req.x, req.y)
    return {"task_id": task.id, "type": "single"}

@app.post("/chain")
async def run_chain(req: AddRequest):
    job = chain(
        add.s(req.x, req.y),       # add(2, 3) → 5
        multiply.s(10),            # multiply(5, 10) → 50
        finalize.s()               # finalize(50)
    )
    result = job.apply_async()
    return {"task_id": result.id, "type": "chain"}

@app.post("/group")
async def run_group(req: AddRequest):
    job = group(
        add.s(req.x, req.y),       # 병렬 1
        multiply.s(req.x, req.y)   # 병렬 2
    )
    result = job.apply_async()
    
    # 개별 작업 ID들을 추출
    task_ids = [task.id for task in result.results]
    
    return {
        "group_id": result.id, 
        "type": "group",
        "task_ids": task_ids  # 개별 작업 ID들 포함
    }

@app.post("/chord")
async def run_chord(req: AddRequest):
    header = group(
        add.s(req.x, req.y),
        multiply.s(req.x, req.y)
    )
    callback = finalize.s()
    job = chord(header)(callback)
    return {"chord_id": job.id, "type": "chord"}


@app.get("/result/{task_id}")
async def get_single_result(task_id: str):
    """단일 작업 결과 조회"""
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


@app.get("/chain-result/{task_id}")
async def get_chain_result(task_id: str):
    """Chain 작업 결과 조회"""
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "type": "chain",
        "status": result.status,
        "result": result.result if result.ready() else None,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else False,
        "failed": result.failed() if result.ready() else False,
        "info": "Chain의 최종 결과입니다"
    }


@app.get("/group-result/{group_id}")
async def get_group_result(group_id: str, task_ids: Optional[str] = Query(None, description="Comma-separated task IDs")):
    """Group 전용 결과 조회 엔드포인트"""
    try:
        # task_ids가 제공된 경우 직접 조회
        if task_ids:
            task_id_list = task_ids.split(",")
            results = []
            all_completed = True
            successful_count = 0
            
            for task_id in task_id_list:
                task_result = celery_app.AsyncResult(task_id)
                result_data = {
                    "task_id": task_id,
                    "status": task_result.status,
                    "result": task_result.result if task_result.ready() else None,
                    "ready": task_result.ready()
                }
                results.append(result_data)
                
                if not task_result.ready():
                    all_completed = False
                elif task_result.successful():
                    successful_count += 1
            
            return {
                "group_id": group_id,
                "type": "group",
                "all_completed": all_completed,
                "successful": successful_count == len(task_id_list) and all_completed,
                "failed": any(r["status"] == "FAILURE" for r in results),
                "total_tasks": len(task_id_list),
                "completed_tasks": sum(1 for r in results if r["ready"]),
                "results": results,
                "method": "direct_task_query"
            }
        
        # 먼저 GroupResult로 시도
        try:
            group_result = GroupResult.restore(group_id, app=celery_app)
            if group_result is not None and hasattr(group_result, 'results'):
                results = []
                for task_result in group_result.results:
                    results.append({
                        "task_id": task_result.id,
                        "status": task_result.status,
                        "result": task_result.result if task_result.ready() else None,
                        "ready": task_result.ready()
                    })
                
                return {
                    "group_id": group_id,
                    "type": "group",
                    "all_completed": group_result.ready(),
                    "successful": group_result.successful() if group_result.ready() else False,
                    "failed": group_result.failed() if group_result.ready() else False,
                    "total_tasks": len(results),
                    "completed_tasks": sum(1 for r in results if r["ready"]),
                    "results": results,
                    "method": "group_result_restore"
                }
        except Exception as e:
            print(f"GroupResult.restore failed: {e}")
        
        # GroupResult가 작동하지 않으면 AsyncResult로 시도
        async_result = celery_app.AsyncResult(group_id)
        
        if async_result.ready() and isinstance(async_result.result, list):
            # Group 결과가 준비되었고 결과가 리스트인 경우
            results = []
            for i, result_value in enumerate(async_result.result):
                results.append({
                    "task_id": f"{group_id}_task_{i}",
                    "status": "SUCCESS",
                    "result": result_value,
                    "ready": True
                })
            
            return {
                "group_id": group_id,
                "type": "group",
                "all_completed": True,
                "successful": True,
                "failed": False,
                "total_tasks": len(results),
                "completed_tasks": len(results),
                "results": results,
                "method": "async_result_list"
            }
        else:
            # 아직 완료되지 않은 경우
            return {
                "group_id": group_id,
                "type": "group",
                "status": async_result.status,
                "all_completed": False,
                "successful": False,
                "failed": False,
                "total_tasks": 0,
                "completed_tasks": 0,
                "results": [],
                "info": "Group 작업이 아직 완료되지 않았습니다.",
                "method": "async_result_fallback"
            }
        
    except Exception as e:
        return {"error": f"Failed to get group result: {str(e)}"}


@app.get("/chord-result/{chord_id}")
async def get_chord_result(chord_id: str):
    """Chord 작업 결과 조회"""
    try:
        # Chord는 콜백 결과를 AsyncResult로 조회
        result = celery_app.AsyncResult(chord_id)
        
        return {
            "chord_id": chord_id,
            "type": "chord",
            "status": result.status,
            "result": result.result if result.ready() else None,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else False,
            "failed": result.failed() if result.ready() else False,
            "info": "Chord의 콜백 결과입니다 (그룹 작업들이 모두 완료된 후의 최종 결과)"
        }
        
    except Exception as e:
        return {"error": f"Failed to get chord result: {str(e)}"}


@app.post("/test-request-info")
async def test_request_info(message: str = "Hello World"):
    """self.request 정보 테스트용 엔드포인트"""
    task = show_request_info.delay(message)
    return {
        "message": "Request info test started",
        "task_id": task.id,
        "check_result": f"/result/{task.id}"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
