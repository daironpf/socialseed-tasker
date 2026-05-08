# Issue #266: Create Troubleshooting/FAQ Documentation

## Description

Create a comprehensive troubleshooting guide and FAQ that helps developers and agents resolve common issues quickly without needing to ask for help or search through code.

### Current State

There's no dedicated troubleshooting documentation. Developers must search through code, issues, or ask for help when they encounter problems.

### Requirements

#### Create `docs/TROUBLESHOOTING.md`

This document should be the first place to look when something breaks:

```markdown
# Troubleshooting Guide - Tasker v1.0.0

## Quick Diagnostics

Run these commands to check system health:

```bash
# Check Neo4j connection
curl http://localhost:8000/health

# Check API status
curl http://localhost:8000/api/v1/components

# Check logs
docker compose logs tasker-api
```

## Common Issues

### Neo4j Connection Issues

#### "Unable to connect to Neo4j"

**Symptoms:** API returns 500 or connection timeout

**Solutions:**
1. Check Neo4j is running: `docker compose ps`
2. Check credentials in .env:
   ```
   TASKER_NEO4J_URI=bolt://localhost:7687
   TASKER_NEO4J_USER=neo4j
   TASKER_NEO4J_PASSWORD=your_password
   ```
3. Check Neo4j logs: `docker compose logs neo4j`
4. Wait for Neo4j to be ready (can take 10-30 seconds on first start)
5. Try: `docker compose restart neo4j`

#### "Authentication failed"

**Symptoms:** Neo4j authentication error in logs

**Solutions:**
1. Verify password matches what Neo4j expects
2. Reset Neo4j password via Docker:
   ```bash
   docker compose exec neo4j cypher-shell -u neo4j -p old_password 
   # Then run: ALTER CURRENT USER SET PASSWORD FROM 'old' TO 'new'
   ```
3. Or recreate the container: `docker compose down -v && docker compose up -d`

### API Issues

#### "404 Not Found" on all endpoints

**Symptoms:** All API calls return 404

**Solutions:**
1. Check API is running: `docker compose ps`
2. Verify correct base URL: `http://localhost:8000/api/v1/...`
3. Check if running in container vs local
4. Check routing in `src/socialseed_tasker/entrypoints/web_api/routes.py`

#### "401 Unauthorized" on all requests

**Symptoms:** API returns 401 even with valid requests

**Solutions:**
1. If auth is enabled, provide API key:
   ```bash
   curl -H "X-API-Key: your_key" http://localhost:8000/api/v1/components
   ```
2. Check `TASKER_AUTH_ENABLED` environment variable
3. Check `TASKER_API_KEY` matches

#### "422 Unprocessable Entity" on POST requests

**Symptoms:** Validation errors on create/update

**Solutions:**
1. Check request body matches schema in `schemas.py`
2. Required fields: Check the Pydantic model
3. Run with verbose logging to see validation errors

### CLI Issues

#### "command not found: tasker"

**Symptoms:** CLI not available after pip install

**Solutions:**
1. Activate virtual environment: `source .venv/bin/activate`
2. Reinstall: `pip install -e .`
3. Check PATH includes .venv/Scripts (Windows) or .venv/bin (Linux/Mac)
4. Try: `python -m socialseed_tasker --help`

#### "Invalid credentials" when running CLI

**Symptoms:** CLI fails with auth error

**Solutions:**
1. Run `tasker config` to set Neo4j credentials
2. Or set environment variables:
   ```bash
   export TASKER_NEO4J_PASSWORD=your_password
   ```

### Graph Model Issues

#### "Node not found" when querying

**Symptoms:** GET requests return null for existing data

**Solutions:**
1. Check the ID format (UUID vs string)
2. Check case sensitivity in property names
3. Run in Neo4j Browser:
   ```cypher
   MATCH (n) RETURN count(n)
   MATCH (n:YourLabel {id: 'your-id'}) RETURN n
   ```

#### "Relationship not created"

**Symptoms:** Relationship queries return empty

**Solutions:**
1. Use MERGE instead of CREATE for idempotentcy
2. Check both nodes exist before creating relationship
3. Verify relationship type matches exactly (case-sensitive)

### Code-as-Graph Issues

#### "No symbols found"

**Symptoms:** code-graph scan returns empty

**Solutions:**
1. Check path exists: `ls your/path`
2. Verify file extensions are supported (.py, .js, .ts, .java)
3. Check file is not empty
4. Try incremental: `tasker code-graph scan . --incremental`

#### "RAG search returns no results"

**Symptoms:** Semantic search returns empty

**Solutions:**
1. Check embeddings exist: `tasker rag stats`
2. Re-index content: `tasker rag index --type issue --id X --content "..."`
3. Adjust threshold: `tasker rag search "query" --threshold 0.3`
4. Check embedding service is available

### Testing Issues

#### "pytest not found"

**Symptoms:** Test command fails

**Solutions:**
1. Install test dependencies: `pip install -e ".[test]"`
2. Or: `pip install pytest pytest-asyncio`

#### "Tests pass locally but fail in CI"

**Symptoms:** Inconsistent test results

**Solutions:**
1. Check environment variables are set in CI
2. Check Neo4j version matches
3. Check Docker is available in CI
4. Add: `--capture=no` to see print output

### Performance Issues

#### "Slow queries"

**Symptoms:** API responses take > 1 second

**Solutions:**
1. Check indexes exist:
   ```cypher
   SHOW INDEXES
   ```
2. Add missing indexes in `queries.py`
3. Use `EXPLAIN` on slow queries
4. Reduce result limits

#### "Memory issues"

**Symptoms:** Out of memory errors

**Solutions:**
1. Reduce batch sizes in repository
2. Add pagination to large queries
3. Clear old data: `tasker code-graph clear`

## FAQ

### General

**Q: What versions of Python/Neo4j are supported?**
A: Python 3.11+, Neo4j 5.x

**Q: Can I use Tasker without Neo4j?**
A: No, Neo4j is the only storage backend in v1.0.0

**Q: How do I reset all data?**
A: Use the admin reset endpoint or `tasker reset --all`

**Q: Where is data stored?**
A: In Neo4j database (not local files)

### Development

**Q: How do I add a new feature?**
A: See `docs/IMPLEMENTATION_GUIDE.md`

**Q: How do I run the API locally?**
A: `python -m socialseed_tasker.entrypoints.web_api` or `tasker api`

**Q: How do I add a test?**
A: Add tests in `tests/unit/` or `tests/integration/`

**Q: How do I debug?**
A: Set `LOG_LEVEL=DEBUG` and check logs

### Integration

**Q: How do external agents interact with Tasker?**
A: Via REST API using the endpoints in `docs/API_REFERENCE.md`

**Q: Can I use Webhooks?**
A: Yes, see webhook endpoints in API reference

**Q: How does GitHub sync work?**
A: See `docs/GITHUB_INTEGRATION.md` (if exists)

### Deployment

**Q: How do I deploy to production?**
A: Use Docker Compose or Kubernetes (docs/DEPLOYMENT.md)

**Q: How do I backup data?**
A: Use Neo4j backup: `docker compose exec neo4j neo4j-admin database dump`

**Q: How do I monitor?**
A: Check `/health` endpoint, see `docs/MONITORING.md`

## Getting Help

If your issue isn't listed here:

1. Check GitHub issues: github.com/socialseed/tasker/issues
2. Check the ROADMAP.md for known issues
3. Create a new issue with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Logs

## Debug Commands

```bash
# Health check
curl http://localhost:8000/health

# Component count
curl http://localhost:8000/api/v1/components | jq '.meta.total'

# Issue count by status
curl http://localhost:8000/api/v1/issues?status=OPEN | jq '.meta.total'

# Graph stats
curl http://localhost:8000/api/v1/code-graph/stats

# Neo4j queries
docker compose exec neo4j cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n)"
```
```

### Business Value

1. **Faster problem resolution** - Developers find solutions quickly
2. **Reduced support burden** - Less "how do I..." questions
3. **Better developer experience** - Confidence in troubleshooting
4. **Agent autonomy** - AI agents can resolve issues without human help

## Status: PENDING

## Priority: MEDIUM