Storage adapters and caching utilities

Adapters
- RedisStorage (socialseed_tasker/infrastructure/redis_storage.py)
  - Uses redis-py client.
  - Methods: put(key, bytes, ttl_seconds), get(key) -> Optional[bytes], delete(key).
  - Raises StorageError on connection or operation failures.
  - Configure via TASKER_REDIS_URL (default redis://localhost:6379/0).

- MemoryStorage (socialseed_tasker/infrastructure/memory_storage.py)
  - In-memory TTL-capable store for local dev and tests.
  - Thread-safe.

Caching utilities
- get_or_set(storage, key, factory, ttl_seconds)
  - Retrieves bytes or calls factory() to produce bytes and stores them.

- memoize(ttl_seconds)
  - Decorator for functions that accept a 'storage' kwarg and return JSON-serializable results.
  - Stores serialized JSON bytes under deterministic key derived from function name and args.

Examples
- Using MemoryStorage:
  from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
  s = MemoryStorage()
  s.put("k", b"v", ttl_seconds=60)
  v = s.get("k")

- Using get_or_set:
  val = get_or_set(s, "k", lambda: b"computed", ttl_seconds=30)

Integration tests
- Use docker-compose.redis.yml to start Redis:
  docker compose -f docker-compose.redis.yml up -d
- Set TASKER_REDIS_URL if Redis is not on default host/port.
