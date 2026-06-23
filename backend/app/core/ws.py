"""WebSocket connection manager with Redis pub/sub for real-time alert broadcasting."""

import json

import structlog
from fastapi import WebSocket

from app.core.config import settings

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections and broadcasts alerts via Redis pub/sub."""

    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._redis = None
        self._pubsub = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def _get_redis(self):
        if self._redis is None and aioredis is not None:
            try:
                self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                self._pubsub = self._redis.pubsub()
                await self._pubsub.subscribe("alerts")
            except Exception as e:
                logger.warning("redis_not_available", exc=str(e))
                self._redis = None
                self._pubsub = None
        return self._redis

    async def start_listener(self):
        redis = await self._get_redis()
        if redis is None:
            return
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    dead = set()
                    for ws in self._connections:
                        try:
                            await ws.send_text(data)
                        except Exception:
                            dead.add(ws)
                    for ws in dead:
                        self._connections.discard(ws)
        except Exception as e:
            logger.error("ws_listener_stopped", exc=str(e))

    async def publish_alert(self, alert_data: dict) -> None:
        redis = await self._get_redis()
        if redis is None:
            return
        try:
            await redis.publish("alerts", json.dumps(alert_data, default=str))
        except Exception as e:
            logger.warning("publish_alert_failed", exc=str(e))

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._pubsub = None


manager = ConnectionManager()
