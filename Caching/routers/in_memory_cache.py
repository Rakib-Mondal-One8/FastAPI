from fastapi import APIRouter
import time
from typing import Any
from services.cache_service import memory_cache

router = APIRouter(
    tags=['In Memory Cache']
)





@router.get("/get-cache/{key}")
async def get_cache(key:str):
    return memory_cache.get(key)

@router.post("/set-cache/{key}/{value}/{ttl}")
async def set_cache(key:str,value:Any,ttl:int):
    memory_cache.set(key,value,ttl)

@router.delete("/delte-cache/{key}")
async def delete_cache(key:str):
    memory_cache.delete(key)


@router.delete("/delete-prefix/{prefix}")
async def delete_on_prefix(prefix:str):
    memory_cache.clear_prefix(prefix)




