# Live API smoke

`smoke_full.py` reads the deployed OpenAPI document, builds request bodies from
its JSON schemas, authenticates with an admin JWT, and exercises each supported
operation. The run is throttled below the API's 60 requests/minute limit;
individual HTTP requests time out after 7.5 seconds.

The script skips only explicitly destructive, resource-intensive, externally
mutating, or not-safely-cleanable operations listed in `SKIP`. Other writes use
a unique run prefix and the final phase deletes tagged test records. Review the
archived cleanup report after every run; if the process is interrupted, inspect
the API for records carrying its
`TASKER-SMOKE-<id>` prefix and remove only those records. The harness tags its
requests with that prefix and revokes its JWT session after the cleanup phase.
Cleanup follows the list endpoints' OpenAPI pagination parameters and verifies
that tagged records are absent after deletion. The reasoning-log write is
skipped because its API has no scoped delete for the `Agent` node it creates.
The cleanup also connects to Redis (default `redis://127.0.0.1:6379/0`) to
remove data-quality reports for issue IDs created by the run and any auth
session whose `user_agent` exactly matches that run ID. Set
`TASKER_SMOKE_REDIS_URL` when Redis is exposed elsewhere; Redis cleanup failure
makes the run fail rather than report a clean result. The harness also requires
`TASKER_SMOKE_DATABASE_URL` and removes only the PostgreSQL auth-audit rows whose
`user_agent` exactly matches the run ID; this restores test-generated logout
events without touching other audit records.

## Run

Set `TASKER_SMOKE_LOGIN_KEY` to the admin login key and `TASKER_API_KEY` to the
API middleware key. Optionally set `TASKER_SMOKE_BASE_URL` (defaults to
`http://127.0.0.1:8888`), `TASKER_SMOKE_REDIS_URL` (defaults to
`redis://127.0.0.1:6379/0`) and `TASKER_SMOKE_INTERVAL_SECONDS` (defaults to
`1.05`). Set `TASKER_SMOKE_DATABASE_URL` to a PostgreSQL connection URL as well.
The smoke runner must be able to reach the API, Redis, and PostgreSQL instances
used by the stack. Then run:

```powershell
python tools/smoke/smoke_full.py
```

Result files under `artifacts/smoke/` contain route templates, status codes,
timings, classifications, and cleanup counts. Response bodies and credentials
are deliberately not archived. The exit code is non-zero when any operation
is classified `ERR` or `TIMEOUT`, or when cleanup fails; review `4XX` results
individually.
