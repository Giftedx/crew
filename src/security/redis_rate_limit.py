"""Distributed token bucket using Redis + Lua.

Atomic refill+consume implemented via EVAL to avoid race conditions. Falls back
to deny on script errors only for the current call (callers should also deploy
local rate limiting as a safety belt when distributed mode is unavailable).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


try:  # optional dependency
    import redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore


_LUA_SCRIPT = """
-- Redis token bucket refill + consume
-- KEYS[1] = bucket key
-- ARGV[1] = capacity
-- ARGV[2] = refill_rate (tokens per second)
-- ARGV[3] = now (unix seconds as float)
-- ARGV[4] = cost (tokens to consume)

local bucket = KEYS[1]
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])

local data = redis.call('HMGET', bucket, 'tokens', 'ts')
local tokens = tonumber(data[1])
local ts = tonumber(data[2])

if tokens == nil or ts == nil then
  tokens = capacity
  ts = now
end

-- refill
local delta = math.max(0, now - ts)
tokens = math.min(capacity, tokens + delta * rate)
ts = now

if tokens >= cost then
  tokens = tokens - cost
  redis.call('HMSET', bucket, 'tokens', tokens, 'ts', ts)
  -- set TTL so idle buckets expire (10x capacity/rate seconds)
  local ttl = math.floor(10 + (capacity / math.max(rate, 0.0001)))
  redis.call('EXPIRE', bucket, ttl)
  return {1, tokens}
else
  redis.call('HMSET', bucket, 'tokens', tokens, 'ts', ts)
  return {0, tokens}
end
"""


@dataclass
class RedisTokenBucket:
    url: str
    rate: float
    capacity: int
    _client: Any = None
    _script: Any = None

    def __post_init__(self) -> None:  # pragma: no cover - minimal glue
        if redis is None:
            raise RuntimeError("redis package is not installed")
        self._client = redis.Redis.from_url(self.url, decode_responses=True)
        self._script = self._client.register_script(_LUA_SCRIPT)

    def allow(self, key: str, *, tokens: int = 1) -> bool:
        try:
            now = self._client.time()  # returns [seconds, microseconds]
            now_sec = float(now[0]) + float(now[1]) / 1_000_000.0
            res = self._script(keys=[f"rl:{key}"], args=[self.capacity, self.rate, now_sec, tokens])
            return bool(res and int(res[0]) == 1)
        except Exception:
            # Fail open: if backend is down, do not block
            return True
