import os
from typing import Optional, Any
from diskcache import Cache
from loguru import logger

class CacheManager:
    _instance: Optional['CacheManager'] = None
    
    def __init__(self, cache_dir: str = ".linker_cache", ttl: int = 3600):
        self.cache = Cache(cache_dir)
        self.ttl = ttl
        logger.debug(f"Cache initialized at {cache_dir} with TTL {ttl}s")

    @classmethod
    def get_instance(cls, cache_dir: str = ".linker_cache", ttl: int = 3600) -> 'CacheManager':
        if cls._instance is None:
            cls._instance = CacheManager(cache_dir, ttl)
        return cls._instance

    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    def set(self, key: str, value: Any):
        self.cache.set(key, value, expire=self.ttl)

    def close(self):
        self.cache.close()
