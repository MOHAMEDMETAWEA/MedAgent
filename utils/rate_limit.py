"""
Rate limiting for MedAgent API.
Supports in-memory (single instance) and Redis (multi-instance production).
"""
import time
import logging
from typing import Optional, Tuple
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

# Optional Redis
_redis = None

def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    try:
        from config import settings
        if settings.REDIS_URL:
            import redis
            _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis.ping()
            return _redis
    except Exception as e:
        logger.warning("Redis not available for rate limiting: %s. Using in-memory.", e)
    return None


class InMemoryRateLimiter:
    """Sliding-window rate limiter per identifier (e.g. IP). Thread-safe."""
    
    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self._timestamps: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()
    
    def _prune(self, key: str, now: float):
        window_start = now - 60.0
        self._timestamps[key] = [t for t in self._timestamps[key] if t > window_start]
    
    def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        """
        Returns (allowed, retry_after_seconds).
        retry_after_seconds is 0 if allowed, else seconds until a slot frees.
        """
        with self._lock:
            now = time.monotonic()
            self._prune(identifier, now)
            timestamps = self._timestamps[identifier]
            if len(timestamps) < self.max_per_minute:
                timestamps.append(now)
                return True, 0
            oldest_in_window = min(timestamps)
            retry_after = int(60 - (now - oldest_in_window)) + 1
            retry_after = max(1, min(retry_after, 60))
            return False, retry_after


def check_rate_limit(identifier: str) -> Tuple[bool, int]:
    """
    Check if the request from identifier is within rate limit.
    Returns (allowed, retry_after_seconds). Uses Redis if REDIS_URL is set, else in-memory.
    """
    from config import settings
    if not settings.RATE_LIMIT_ENABLED:
        return True, 0
    
    max_per_minute = settings.MAX_REQUESTS_PER_MINUTE
    redis_client = _get_redis()
    
    if redis_client:
        # Redis: fixed window per minute (key = ratelimit:{id}:{minute})
        try:
            window = int(time.time() // 60)
            key = f"ratelimit:{identifier}:{window}"
            count = redis_client.incr(key)
            if count == 1:
                redis_client.expire(key, 120)  # 2 min TTL
            if count <= max_per_minute:
                return True, 0
            return False, 60  # retry after next minute
        except Exception as e:
            logger.warning("Redis rate limit check failed: %s. Allowing request.", e)
            return True, 0
    
    # In-memory
    if not hasattr(check_rate_limit, "_limiter"):
        check_rate_limit._limiter = InMemoryRateLimiter(max_per_minute)
    return check_rate_limit._limiter.is_allowed(identifier)


def get_client_identifier(request) -> str:
    """Get client identifier for rate limiting (IP). Respects X-Forwarded-For if behind proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"
