"""
FastAPI Caching — Complete Implementation
=========================================
Covers:
  1. In-memory cache (no external deps, great for single-process dev)
  2. Redis cache (production distributed cache)
  3. Cache-aside pattern (most common)
  4. Response caching with HTTP headers
  5. Decorator-based caching
  6. Cache invalidation
  7. Background refresh (prevents thundering herd)

Install deps: 
    pip install fastapi uvicorn redis[asyncio] hiredis
"""

import asyncio
import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable, Optional

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse

app = FastAPI(title="Caching Demo")


# ──────────────────────────────────────────────
# 1. IN-MEMORY CACHE  (single-process / dev)
# ──────────────────────────────────────────────

class InMemoryCache:
    """Simple TTL-aware in-process cache. Not shared across workers."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}  # key → (value, expires_at)

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]   # lazy eviction
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear_prefix(self, prefix: str) -> int:
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)


memory_cache = InMemoryCache()


# ──────────────────────────────────────────────
# 2. REDIS CACHE  (production distributed)
# ──────────────────────────────────────────────

class RedisCache:
    """
    Async Redis wrapper.
    Serialises values to JSON automatically.
    """

    def __init__(self, url: str = "redis://localhost:6379"):
        self._client: Optional[aioredis.Redis] = None
        self._url = url

    async def connect(self):
        self._client = await aioredis.from_url(
            self._url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )

    async def disconnect(self):
        if self._client:
            await self._client.aclose()

    async def get(self, key: str) -> Optional[Any]:
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int = 60) -> None:
        await self._client.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a glob pattern. Use sparingly on large dbs."""
        keys = await self._client.keys(pattern)
        if keys:
            return await self._client.delete(*keys)
        return 0

    async def exists(self, key: str) -> bool:
        return bool(await self._client.exists(key))

    async def ttl(self, key: str) -> int:
        """Remaining TTL in seconds. -1 = no expiry, -2 = key doesn't exist."""
        return await self._client.ttl(key)


redis_cache = RedisCache()


# ──────────────────────────────────────────────
# 3. LIFESPAN — connect/disconnect Redis
# ──────────────────────────────────────────────

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_cache.connect()
    yield
    await redis_cache.disconnect()

app.router.lifespan_context = lifespan


# ──────────────────────────────────────────────
# 4. FAKE DATABASE LAYER
# ──────────────────────────────────────────────

_db: dict[int, dict] = {
    1: {"id": 1, "name": "Alice", "role": "admin"},
    2: {"id": 2, "name": "Bob",   "role": "user"},
    3: {"id": 3, "name": "Carol", "role": "user"},
}

async def db_get_user(user_id: int) -> Optional[dict]:
    """Simulates a slow DB call (~50 ms)."""
    await asyncio.sleep(0.05)
    return _db.get(user_id)

async def db_update_user(user_id: int, data: dict) -> Optional[dict]:
    await asyncio.sleep(0.05)
    if user_id not in _db:
        return None
    _db[user_id].update(data)
    return _db[user_id]

async def db_list_users() -> list[dict]:
    await asyncio.sleep(0.05)
    return list(_db.values())


# ──────────────────────────────────────────────
# 5. CACHE-ASIDE PATTERN (most common)
# ──────────────────────────────────────────────

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    Cache-aside pattern:
      1. Check cache
      2. On hit → return immediately
      3. On miss → query DB, populate cache, return
    """
    cache_key = f"user:{user_id}"

    # Step 1: check cache
    cached = await redis_cache.get(cache_key)
    if cached is not None:
        return {**cached, "_source": "cache"}

    # Step 2: cache miss → hit DB
    user = await db_get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Step 3: populate cache, TTL 5 minutes
    await redis_cache.set(cache_key, user, ttl=300)

    return {**user, "_source": "db"}


# ──────────────────────────────────────────────
# 6. CACHE INVALIDATION ON WRITE
# ──────────────────────────────────────────────

@app.patch("/users/{user_id}")
async def update_user(user_id: int, payload: dict):
    """
    Write-invalidate pattern:
      Update DB → delete cache → next read re-populates.
    """
    updated = await db_update_user(user_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Invalidate this user's cache entry
    await redis_cache.delete(f"user:{user_id}")

    # Also invalidate any list cache that includes this user
    await redis_cache.delete("users:list")

    return updated


# ──────────────────────────────────────────────
# 7. CACHING A LIST WITH COMPOSITE KEYS
# ──────────────────────────────────────────────

@app.get("/users")
async def list_users(role: Optional[str] = None):
    """
    Cache keyed by query parameters.
    Different filters → different cache entries.
    """
    cache_key = f"users:list:{role or 'all'}"

    cached = await redis_cache.get(cache_key)
    if cached is not None:
        return {"users": cached, "_source": "cache"}

    users = await db_list_users()
    if role:
        users = [u for u in users if u["role"] == role]

    await redis_cache.set(cache_key, users, ttl=60)
    return {"users": users, "_source": "db"}


# ──────────────────────────────────────────────
# 8. DECORATOR-BASED CACHING (reusable)
# ──────────────────────────────────────────────

def cached(ttl: int = 60, key_prefix: str = ""):
    """
    Decorator that caches the return value of an async function in Redis.
    Cache key = prefix + sha256 of (function name + args + kwargs).

    Usage:
        @cached(ttl=300, key_prefix="reports:")
        async def expensive_report(year: int, month: int):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build a stable cache key from function name + arguments
            raw = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
            cache_key = f"{key_prefix}{func.__name__}:{digest}"

            cached_value = await redis_cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            await redis_cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


@cached(ttl=120, key_prefix="stats:")
async def compute_user_stats() -> dict:
    """Expensive computation, cached for 2 minutes."""
    await asyncio.sleep(0.2)  # simulates heavy work
    users = list(_db.values())
    return {
        "total": len(users),
        "admins": sum(1 for u in users if u["role"] == "admin"),
    }

@app.get("/stats")
async def get_stats():
    return await compute_user_stats()


# ──────────────────────────────────────────────
# 9. HTTP RESPONSE CACHING (Cache-Control headers)
# ──────────────────────────────────────────────

@app.get("/public/config")
async def public_config(response: Response):
    """
    Static / rarely changing data.
    Tell browsers and CDNs to cache for 1 hour.
    """
    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=60"
    return {"theme": "dark", "version": "2.1.0", "features": ["search", "export"]}


@app.get("/private/profile/{user_id}")
async def private_profile(user_id: int, response: Response):
    """
    User-specific data — must NOT be cached by shared caches (CDNs).
    Browser can cache briefly.
    """
    response.headers["Cache-Control"] = "private, max-age=30, no-store"
    user = await db_get_user(user_id)
    if not user:
        raise HTTPException(status_code=404)
    return user


# ──────────────────────────────────────────────
# 10. BACKGROUND REFRESH (prevents thundering herd)
# ──────────────────────────────────────────────

_refresh_locks: dict[str, asyncio.Lock] = {}

async def get_with_background_refresh(
    cache_key: str,
    fetch_fn: Callable,
    ttl: int = 60,
    refresh_before: int = 10,      # start refresh this many seconds before expiry
) -> Any:
    """
    Probabilistic early refresh:
      - Returns cached value immediately
      - If TTL is nearly expired, refreshes in the background
      - Only one background refresh per key (lock prevents thundering herd)
    """
    cached = await redis_cache.get(cache_key)
    remaining = await redis_cache.ttl(cache_key)

    if cached is not None:
        if remaining <= refresh_before:
            # Refresh in background — don't block the request
            asyncio.create_task(_background_refresh(cache_key, fetch_fn, ttl))
        return cached

    # Cold miss — fetch synchronously (only first request pays the cost)
    lock = _refresh_locks.setdefault(cache_key, asyncio.Lock())
    async with lock:
        # Double-check after acquiring lock (another request may have already fetched)
        cached = await redis_cache.get(cache_key)
        if cached is not None:
            return cached
        result = await fetch_fn()
        await redis_cache.set(cache_key, result, ttl=ttl)
        return result

async def _background_refresh(cache_key: str, fetch_fn: Callable, ttl: int):
    lock = _refresh_locks.setdefault(cache_key, asyncio.Lock())
    if lock.locked():
        return   # another refresh is already running
    async with lock:
        result = await fetch_fn()
        await redis_cache.set(cache_key, result, ttl=ttl)


@app.get("/leaderboard")
async def get_leaderboard():
    """High-traffic endpoint using background refresh to stay fresh without spikes."""
    async def fetch():
        await asyncio.sleep(0.1)   # simulate expensive aggregation
        return [{"rank": i, "user": f"user_{i}", "score": 1000 - i * 10} for i in range(1, 11)]

    data = await get_with_background_refresh("leaderboard", fetch, ttl=30, refresh_before=5)
    return {"leaderboard": data}


# ──────────────────────────────────────────────
# 11. CACHE HEALTH & DIAGNOSTICS
# ──────────────────────────────────────────────

@app.get("/cache/info")
async def cache_info():
    """Expose cache key metadata for a given pattern (dev/ops tool)."""
    info = await redis_cache._client.info("stats")
    return {
        "keyspace_hits":   info.get("keyspace_hits", 0),
        "keyspace_misses": info.get("keyspace_misses", 0),
        "hit_rate": round(
            info.get("keyspace_hits", 0) /
            max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
            2
        ),
        "used_memory_human": info.get("used_memory_human", "n/a"),
    }

@app.delete("/cache/flush")
async def flush_user_cache():
    """Invalidate all user-related cache keys. Use with care in production."""
    deleted = await redis_cache.delete_pattern("user:*")
    deleted += await redis_cache.delete_pattern("users:*")
    return {"deleted_keys": deleted}


# ──────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_caching:app", host="0.0.0.0", port=8000, reload=True)
