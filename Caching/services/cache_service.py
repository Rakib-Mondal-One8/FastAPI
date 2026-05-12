import time
import json
from typing import Any, Optional

import redis.asyncio as aioredis

# ──────────────────────────────────────────────────────
# In-Memory Caching
# ──────────────────────────────────────────────────────

class InMemoryChache:

    def __init__(self):
        self._store : dict[str,tuple[Any,float]] = {}

    
    def get(self,key:str):
        entry = self._store.get(key)
        if(entry is None):
            return None
        
        val,exp = entry
        if(exp < time.monotonic()):
            del self._store[key]
            return None
        
        return entry
    
    def set(self,key:str,value:Any,ttl:int = 60):
        self._store[key] = (value,ttl+time.monotonic())
        return
    
    def delete(self,key:str):
        return self._store.pop(key,None)
    
    def clear_prefix(self,prefix:str):
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            self._store.pop(k,None)
        return len(keys)
    

memory_cache = InMemoryChache()





# ──────────────────────────────────────────────
# 2. REDIS CACHE  (production distributed)
# ──────────────────────────────────────────────


class RedisCache:
    def __init__(self,url = "redis://localhost:6379"):
        self._client : Optional[aioredis.Redis] = None
        self._url = url

    async def connect(self):
        self._client = await aioredis.from_url(
            self._url,
            encoding='UTF-8',
            decode_responses=True,
            max_connections=20,
        )

    async def disconnect(self):
        if(self._client):
            await self._client.aclose()

    async def get(self,key:str):
        raw = await self._client.get(key)
        if(raw is None):
            return None
        return json.loads(raw)
    
    async def set(self,key:str,value:Any,ttl:float):
        await self._client.setex(key,ttl,json.dumps(value))

    async def delete(self,key:str):
        await self._client.delete(key)

    async def delete_pattern(self,pattern:str):
        keys = await self._client.keys(pattern)
        if keys:
            await self._client.delete(*keys)
        return 0
    
    async def exists(self,key):
        return bool(await self._client.exists(key))
    
    async def ttl(self,key:str):
        return await self._client.ttl(key)
    

redis = RedisCache()
