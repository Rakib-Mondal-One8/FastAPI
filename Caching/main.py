import time
from typing import Any

from fastapi import FastAPI


app = FastAPI(title="Caching Demo")


@app.get('/')
async def health_check():
    return {"status":'healthy'}


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


@app.get("/get-cache/{key}")
async def get_cache(key:str):
    return memory_cache.get(key)

@app.post("/set-cache/{key}/{value}/{ttl}")
async def set_cache(key:str,value:Any,ttl:int):
    memory_cache.set(key,value,ttl)

@app.delete("/delte-cache/{key}")
async def delete_cache(key:str):
    memory_cache.delete(key)


@app.delete("/delete-prefix/{prefix}")
async def delete_on_prefix(prefix:str):
    memory_cache.clear_prefix(prefix)
