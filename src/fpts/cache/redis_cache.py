from __future__ import annotations

import json
from datetime import date, datetime
from typing import Callable, Generic, Optional, TypeVar

import redis

K = TypeVar("K")
V = TypeVar("V")


class RedisTTLCache(Generic[V]):
    """
    Redis-backed TTL cache with pluggable (de)serialization.

    - Keys are stored as strings
    - Values are stored as JSON strings
    - TTL enforced by Redis via SETEX
    """

    def __init__(
        self,
        *,
        redis_url: str,
        ttl_seconds: int,
        dumps: Callable[[V], object],
        loads: Callable[[object], V],
        key_prefix: str = "",
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._dumps = dumps
        self._loads = loads
        self._prefix = key_prefix
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Optional[V]:
        raw = self._client.get(self._k(key))
        if raw is None:
            return None
        payload = json.loads(raw)
        return self._loads(payload)

    def set(self, key: str, value: V) -> None:
        payload_obj = self._dumps(value)
        raw = json.dumps(payload_obj, separators=(",", ":"))
        self._client.setex(self._k(key), self._ttl_seconds, raw)
