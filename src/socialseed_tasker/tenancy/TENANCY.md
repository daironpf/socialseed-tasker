Multi-Tenancy Guide

Resolution order
1. X-Tenant-ID header
2. Host subdomain (<tenant>.host)
3. Token map via container.tenancy_token_map

Storage namespacing
- Use tenant_scoped_storage(tenant_id) to obtain a NamespacedStorage that prefixes keys with tenant:{tenant_id}:

Migrations
- Call ensure_tenant_schema(tenant_id) after creating a tenant.
- Use run_migrations to run tenant-specific migration functions.

Admin operations
- Create tenant: POST /api/v1/admin/tenants { "id": "tenant1", "config": {...} }
- List tenants: GET /api/v1/admin/tenants
- Delete tenant: DELETE /api/v1/admin/tenants/{tenant_id}

Security
- Admin endpoints require admin RBAC permission.
- Tenant resolution from host is convenient for dev; in production prefer header or token mapping.

Testing
- Set TASKER_INTEGRATION=1 to run integration tests that exercise tenant isolation.
