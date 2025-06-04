from fastapi import FastAPI

app = FastAPI()

from pydantic import BaseModel

class AddRequest(BaseModel):
    x : int
    y: int

from tasks import celery_app, add

@app.post("/add")
async def celery_add(req: AddRequest):
    task = add.delay(req.x, req.y)
    return {"task_id": task.id}

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if result.ready():
        return {"status": result.status, "result": result.result}
    return {"status": result.status, "result": None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
