Board Integration

- The frontend board is served at http://localhost:8080 when docker compose is used.
- The board expects TASKER_API_URL to point to the API (default http://api:8000 in compose).
- Configure CORS via TASKER_API_ALLOW_ORIGINS (comma separated). Default: http://localhost:8080
- For development only: set TASKER_AUTH_TOKEN to a development token and inject it into the frontend environment.
- Do not expose production tokens to client-side code.
