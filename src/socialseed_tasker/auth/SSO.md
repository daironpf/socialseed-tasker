Single Sign-On (SSO) with Keycloak

> **Retired in the API (issue #597).** The stack never ships Keycloak as a core
> service, and `GET /auth/login` used to hang API-surface probes against the
> unreachable proxy (the only TIMEOUT of the 294-route smoke). The legacy trio
> `GET /auth/login`, `GET /auth/callback` and `POST /auth/logout` now answers
> `410 Gone` (`SSO_KEYCLOAK_RETIRED`) and is hidden from the OpenAPI schema.
> The real login flows are `POST /api/v1/auth/login` (api key/JWT) and
> `GET /api/v1/auth/oauth/{provider}/authorize` (GitHub/Google PKCE).
> The compose file below stays as an optional local-dev tool.

Overview
- Local development SSO using Keycloak and OpenID Connect.
- Keycloak realm import file: auth/keycloak-realm.json
- Keycloak admin UI: http://localhost:8082 (admin: kcadmin / kcadminpass)

How it works
1. Frontend redirects to backend /auth/login.
2. Backend builds Keycloak authorization URL and redirects browser.
3. User authenticates in Keycloak and Keycloak redirects to /auth/callback with code.
4. Backend exchanges code for tokens, creates a server-side session, and sets TASKER_SESSION cookie.
5. API endpoints accept either Authorization: Bearer <token> or TASKER_SESSION cookie.

Environment variables
- TASKER_KEYCLOAK_URL default http://localhost:8082
- TASKER_KEYCLOAK_REALM default tasker-dev
- TASKER_KEYCLOAK_API_CLIENT_SECRET default tasker-api-secret
- TASKER_BASE_URL default http://localhost:8000
- TASKER_SESSION_COOKIE default TASKER_SESSION

Local dev steps
1. Start Keycloak:
   docker compose -f compose/tools/auth.yml up -d
2. Start API and frontend (compose stacks).
3. Open frontend at http://localhost:8080 and click Login.

Security notes
- The realm and client configuration in auth/keycloak-realm.json are for local development only.
- In production, validate ID token signatures using Keycloak JWKS and use HTTPS and secure cookies.
