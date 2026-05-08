# Troubleshooting Guide - Tasker v1.0.0

This is the first place to look when something breaks.

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

---

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
5. Try: `docker compose restart tasker-db`

#### "Authentication failed"

**Symptoms:** Neo4j authentication error in logs

**Solutions:**
1. Verify password matches what Neo4j expects
2. Reset Neo4j password via Docker:
   ```bash
   docker compose exec tasker-db cypher-shell -u neo4j -p old_password 
   # Then run: ALTER CURRENT USER SET PASSWORD FROM 'old' TO 'new'
   ```
3. Or recreate the container: `docker compose down -v && docker compose up -d`

**Note:** Neo4j 5.x requires the password to be different from the username. Use a non-default password like `neoSocial`.

---

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

---

### CLI Issues

#### "command not found: tasker"

**Symptoms:** CLI not available after pip install

**Solutions:**
1. Activate virtual environment: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
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

---

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
1. Use MERGE instead of CREATE for idempotency
2. Check both nodes exist before creating relationship
3. Verify relationship type matches exactly (case-sensitive)

---

### Code-as-Graph Issues

#### "No symbols found"

**Symptoms:** code-graph scan returns empty

**Solutions:**
1. Check path exists: `ls your/path`
2. Verify file extensions are supported (.py, .js, .ts, .java, .cpp)
3. Check file is not empty
4. Try incremental: `tasker code-graph scan . --incremental`

#### "RAG search returns no results"

**Symptoms:** Semantic search returns empty

**Solutions:**
1. Check embeddings exist: `tasker rag stats`
2. Re-index content: `tasker rag index --type issue --id X --content "..."`
3. Adjust threshold: `tasker rag search "query" --threshold 0.3`
4. Check embedding service is available (requires OPENAI_API_KEY for real embeddings)

---

### Agent Integration Issues

#### "Agent not found" when linking

**Symptoms:** Agent specialist or assignment operations fail

**Solutions:**
1. Register agent first: `tasker agent register --id "agent-001" --name "Agent"`
2. Check agent exists in Neo4j:
   ```cypher
   MATCH (a:Agent) RETURN a.id, a.name
   ```
3. Verify component exists:
   ```cypher
   MATCH (c:Component) RETURN c.id, c.name
   ```

#### "Agent heartbeat timeout"

**Symptoms:** Agent marked as stalled

**Solutions:**
1. Ensure agents send heartbeat periodically
2. Check `/api/v1/agents/{id}/status` endpoint
3. Increase heartbeat timeout if needed

---

### Testing Issues

#### "pytest not found"

**Symptoms:** Test command fails

**Solutions:**
1. Install test dependencies: `pip install -e ".[test]"` or `pip install pytest pytest-asyncio`
2. Run with: `pytest tests/`

#### "Tests pass locally but fail in CI"

**Symptoms:** Inconsistent test results

**Solutions:**
1. Check environment variables are set in CI
2. Check Neo4j version matches
3. Check Docker is available in CI
4. Add: `--capture=no` to see print output

---

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

---

## FAQ

### General

**Q: What versions of Python/Neo4j are supported?**
A: Python 3.10+, Neo4j 5.x

**Q: Can I use Tasker without Neo4j?**
A: No, Neo4j is the only storage backend in v1.0.0

**Q: How do I reset all data?**
A: Use the admin reset endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/admin/reset \
  -H "Content-Type: application/json" \
  -d '{"scope": "all"}'
```

**Q: Where is data stored?**
A: In Neo4j database (not local files)

---

### Development

**Q: How do I add a new feature?**
A: See [Implementation Guide](IMPLEMENTATION_GUIDE.md)

**Q: How do I run the API locally?**
A: `python -m socialseed_tasker.entrypoints.web_api.app` or `tasker api`

**Q: How do I add a test?**
A: Add tests in `tests/unit/` or `tests/integration/`

**Q: How do I debug?**
A: Set environment variable `LOG_LEVEL=DEBUG` and check logs

---

### Integration

**Q: How do external agents interact with Tasker?**
A: Via REST API using the endpoints in [API Reference](API_REFERENCE.md)

**Q: Can I use Webhooks?**
A: Yes, see webhook endpoints in API reference:
```bash
curl http://localhost:8000/api/v1/webhooks
```

**Q: How does GitHub sync work?**
A: Configure with environment variables `GITHUB_TOKEN` and `GITHUB_REPO`

---

### Deployment

**Q: How do I deploy to production?**
A: Use Docker Compose as defined in the project

**Q: How do I backup data?**
A: Use Neo4j backup:
```bash
docker compose exec tasker-db neo4j-admin database dump neo4j --to-path=/backup
```

**Q: How do I monitor?**
A: Check `/health` endpoint for status

---

## Getting Help

If your issue isn't listed here:

1. Check GitHub issues: github.com/daironpf/socialseed-tasker/issues
2. Check the ROADMAP.md for known issues
3. Create a new issue with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Logs

---

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

# Agent list
curl http://localhost:8000/api/v1/agents

# Neo4j queries
docker compose exec tasker-db cypher-shell -u neo4j -p neoSocial "MATCH (n) RETURN count(n)"
```