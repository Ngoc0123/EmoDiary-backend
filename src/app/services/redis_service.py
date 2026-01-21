from typing import Any
import redis.asyncio as redis
from app.utils.config import settings

class RedisService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )

    async def set_value(self, key: str, value: Any, expire_seconds: int | None = None) -> None:
        await self.redis_client.set(key, value, ex=expire_seconds)

    async def get_value(self, key: str) -> str | None:
        return await self.redis_client.get(key)

    async def delete_value(self, key: str) -> None:
        await self.redis_client.delete(key)
        
    async def close(self):
        await self.redis_client.close()
