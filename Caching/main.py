from fastapi import FastAPI
from fastapi import routing
from routers import in_memory_cache,redis_cache
from contextlib import asynccontextmanager
from services.cache_service import redis
app = FastAPI(title="Caching Demo")




@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis.connect()
    yield
    await redis.disconnect()

app.router.lifespan_context = lifespan


@app.get('/')
async def health_check():
    return {"status":'healthy'}

app.include_router(in_memory_cache.router)
app.include_router(redis_cache.router)


