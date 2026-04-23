# Issue #108: Implement Rate Limiting for Public Endpoints

## Description

The API lacks rate limiting, allowing unlimited requests per client. This can lead to abuse, DoS attacks, and resource exhaustion. Rate limiting should be implemented to protect the API.

## Requirements

- Implement rate limiting using a simple in-memory or Redis-based approach
- Add configurable rate limits (e.g., 100 requests/minute per IP)
- Add rate limit headers to responses (X-RateLimit-Limit, X-RateLimit-Remaining)
- Add proper 429 Too Many Requests response when limit exceeded
- Make rate limits configurable via environment variables

## Technical Details

### Configuration
```python
# Environment variables
TASKER_RATE_LIMIT_ENABLED=true/false
TASKER_RATE_LIMIT_PER_MINUTE=100
TASKER_RATE_LIMIT_PER_HOUR=1000
```

### Implementation Options

**Option 1: In-memory (simple, single instance)**
- Use a simple dictionary to track requests per IP
- Good for single-instance deployments
- Limitations: Doesn't work with multiple API instances

**Option 2: Redis-based (recommended for production)**
- Use Redis to track rate limits
- Works across multiple API instances
- Better for production

### Expected Response Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

### Rate Limit Exceeded Response
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again later.",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset": 1609459200
    }
  }
}
```

## Business Value

- Prevents API abuse and DoS attacks
- Ensures fair usage among clients
- Protects Neo4j from query overload
- Better reliability

## Status: COMPLETED