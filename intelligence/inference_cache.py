import hashlib
import json
import logging
from typing import Any, Dict, Optional

import redis

from config import settings

logger = logging.getLogger(__name__)


class ClinicalInferenceCache:
    """
    Phase 11: Scalability & Performance (Distributed)
    Cycle 5 Evolution: Shifting from local LRU to Redis for cluster-wide caching.
    """

    def __init__(self):
        try:
            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True,
            )
            self._redis.ping()
            logger.info(
                f"Performance: Connected to Redis Cache ({settings.REDIS_HOST}:{settings.REDIS_PORT})"
            )
            self._enabled = True
        except Exception as e:
            logger.warning(
                f"Performance: Redis unavailable, falling back to local simulation. Error: {e}"
            )
            self._enabled = False
            self._local_cache = {}  # Emergency local fallback

    def get_prediction(
        self, symptoms: str, interaction_mode: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieves a cached prediction from Redis."""
        cache_key = (
            f"medagent:inference:{self._generate_key(symptoms, interaction_mode)}"
        )

        if self._enabled:
            try:
                cached_data = self._redis.get(cache_key)
                if cached_data:
                    logger.info("Performance: Distributed Redis Cache HIT.")
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        else:
            return self._local_cache.get(cache_key)
        return None

    def set_prediction(
        self,
        symptoms: str,
        interaction_mode: str,
        data: Dict[str, Any],
        ttl: int = 3600,
    ):
        """Caches a clinical inference result with TTL."""
        cache_key = (
            f"medagent:inference:{self._generate_key(symptoms, interaction_mode)}"
        )

        if self._enabled:
            try:
                self._redis.setex(cache_key, ttl, json.dumps(data))
                logger.info(f"Performance: Cached inference in Redis (TTL: {ttl}s).")
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        else:
            self._local_cache[cache_key] = data

    def _generate_key(self, symptoms: str, mode: str) -> str:
        """Generates a stable hash key for a clinical query."""
        payload = f"{symptoms.strip().lower()}:{mode}"
        return hashlib.sha256(payload.encode()).hexdigest()


# Singleton Instance
inference_cache = ClinicalInferenceCache()
