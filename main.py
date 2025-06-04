from fastapi import FastAPI

app = FastAPI()

from pydantic import BaseModel

class AddRequest(BaseModel):
    x : int
    y: int

from tasks import celery_app, add

from celery import chain, group, chord
from tasks import add, multiply, finalize

@app.post("/add")
async def celery_add(req: AddRequest):
    task = add.delay(req.x, req.y)
    return {"task_id": task.id}



@app.post("/chain")
async def run_chain(req: AddRequest):
    job = chain(
        add.s(req.x, req.y),       # add(2, 3) → 5
        multiply.s(10),            # multiply(5, 10) → 50
        finalize.s()               # finalize(50)
    )
    result = job.apply_async()
    return {"task_id": result.id}

@app.post("/group")
async def run_group(req: AddRequest):
    job = group(
        add.s(req.x, req.y),       # 병렬 1
        multiply.s(req.x, req.y)   # 병렬 2
    )
    result = job.apply_async()
    return {"group_id": result.id}

@app.post("/chord")
async def run_chord(req: AddRequest):
    header = group(
        add.s(req.x, req.y),
        multiply.s(req.x, req.y)
    )
    callback = finalize.s()
    job = chord(header)(callback)
    return {"chord_id": job.id}



@app.get("/result/{task_id}")
async def get_result(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if result.ready():
        return {"status": result.status, "result": result.result}
    return {"status": result.status, "result": None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
