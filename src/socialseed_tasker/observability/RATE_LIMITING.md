Rate Limiting and Abuse Protection

Overview
- Implements token-bucket rate limiting with Redis adapter and in-memory fallback.
- Middleware enforces per-user and per-IP limits for API requests.
- CLI helper enforces same limits for CLI commands.

Configuration
- TASKER_REDIS_URL: Redis URL for RedisRateLimiter.
- TASKER_RATE_USER_PER_MIN: per-user tokens per minute (default 120).
- TASKER_RATE_IP_PER_MIN: per-IP tokens per minute (default 60).
- TASKER_RATE_BURST: burst capacity (default 20).

Admin endpoints
- GET /api/v1/admin/rate/{key}
- POST /api/v1/admin/rate/{key}/reset
  Require admin permission.

Testing
- Unit tests in tests/infrastructure and tests/api.
- Integration tests require Redis and TASKER_INTEGRATION=1.

Operational notes
- Tune rate limits based on traffic patterns.
- Use Redis adapter in production for multi-instance consistency.
- Monitor rate-limited responses and adjust thresholds.
