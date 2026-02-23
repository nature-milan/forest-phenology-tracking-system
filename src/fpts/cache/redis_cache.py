from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Generic, Optional, TypeVar

import redis

K = TypeVar("K")
V = TypeVar("V")


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

    # Pydantic v2 models
    if hasattr(obj, "model_dump"):
        return obj.model_dump()

    # Dataclasses / other objects: last resort
    if hasattr(obj, "__dict__"):
        return obj.__dict__

    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class RedisTTLCache(Generic[K, V]):
    """
    Minimal Redis-backed TTL cache.

    - Stores values as JSON strings
    - Uses SETEX for TTL
    """

    def __init__(self, *, redis_url: str, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        # decode_responses=True => we read/write strings instead of bytes
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def get(self, key: K) -> Optional[V]:
        raw = self._client.get(str(key))
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: K, value: V) -> None:
        payload = json.dumps(value, default=_json_default, separators=(",", ":"))
        self._client.setex(str(key), self._ttl_seconds, payload)
