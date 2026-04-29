# Security Policy

This document outlines the security measures implemented in SocialSeed Tasker and the dependency upgrade policy.

## Security Checklist

All items below are implemented and verified:

- [x] **No hardcoded secrets** - All credentials loaded from environment variables or `.env` files
- [x] **API key validation** - `api_key_auth_middleware` validates `X-API-Key` or `Authorization: Bearer` headers
- [x] **Input sanitization** - `sanitize_issue_title`, `sanitize_issue_description` prevent XSS/injection
- [x] **Neo4j injection prevention** - All Cypher queries use parameterized queries
- [x] **XSS prevention** - Rich text is escaped via `sanitize_text` in validation module
- [x] **Webhook signature validation** - `WebhookSignatureValidator` verifies GitHub webhook authenticity
- [x] **Rate limiting** - `rate_limit_middleware` limits requests per IP per minute/hour
- [x] **HTTPS enforcement** - Neo4j Aura URIs auto-detected for encryption (`bolt+s://`, `neo4j+s://`)

## Dependency Upgrade Policy

### Schedule
- **Weekly**: Automated dependency update via GitHub Actions (Sundays at midnight)
- **As needed**: Security patches for critical vulnerabilities

### Process
1. GitHub Actions runs `pip-compile --upgrade` weekly
2. Creates PR with updated dependencies
3. Automated tests must pass before merge
4. Security audit (`pip-audit`) runs on all PRs

### Version Constraints
We use semantic version constraints to balance stability and freshness:

| Category | Constraint | Examples |
|----------|-------------|----------|
| Runtime | `>=min` | `fastapi>=0.109.0` |
| Dev | `>=min` | `pytest>=7.4.0` |

### Breaking Changes
If a dependency update introduces breaking changes:
1. Pin to last known good version
2. Document in release notes
3. Plan migration for next minor release

## Environment Variables for Security

```bash
# Authentication (optional but recommended for production)
TASKER_AUTH_ENABLED=true
TASKER_API_KEY=your-secret-key

# Neo4j credentials
TASKER_NEO4J_URI=bolt://localhost:7687
TASKER_NEO4J_USERNAME=neo4j
TASKER_NEO4J_PASSWORD=your-password

# Rate limiting (production)
TASKER_RATE_LIMIT_ENABLED=true
TASKER_RATE_LIMIT_PER_MINUTE=100
TASKER_RATE_LIMIT_PER_HOUR=1000
```

## Docker Security

Base images are kept minimal and updated regularly:

- **Python API**: `python:3.10-slim` (multi-stage build)
- **Frontend**: `node:20-alpine` → `nginx:alpine`

To update base images, run:
```bash
# Check for vulnerabilities in Docker images
docker scan socialseed-tasker:latest
```

## Reporting Security Issues

If you discover a security vulnerability, please report it via:
- GitHub Security Advisories
- Email: dairon.perezfrias@gmail.com

Response timeline:
- **Critical**: 24-48 hours
- **High**: 1 week
- **Medium**: 2 weeks
- **Low**: Next release cycle