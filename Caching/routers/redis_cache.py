from fastapi import APIRouter
from services.cache_service import redis
from typing import Any
from schemas.user import User

router = APIRouter(tags=["Redis Cache"],prefix="/redis-cache")



@router.get("/get/{key}")
async def get(key:str):
    response = await redis.get(key)
    return {"response":response}

@router.post("/set/{key}/{value}/{ttl}")
async def set(key:str,value:Any,ttl:int):
    await redis.set(key,value,ttl)

@router.post("/set-user")
async def set_user(user:User):
    key = f"user:{user.id}"
    await redis.set(key,user.model_dump(),1200)


@router.delete("/delete/{key}")
async def delete(key:str):
    await redis.delete(key)