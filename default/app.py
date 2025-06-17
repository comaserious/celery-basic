from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse

import asyncio
from random import randint

default_router = APIRouter(prefix="/default")

@default_router.get("/")
async def root():
    return JSONResponse(content={"message": "Default App Start ㅍㅍㅍ"})

from default.service import (
    add_service
)

@default_router.get("/add")
async def add():
    a = randint(1, 100)
    b = randint(1, 100)

    await add_service(a, b)

    return PlainTextResponse(f"FastAPI : {a=},{ b=} Published to the queue")