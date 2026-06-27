### Issue 306 Updated — Add HTTP API with OpenAPI spec, FastAPI server, and integrated frontend board

**Short description**  
Actualizar la Issue 018 para incluir la integración explícita del **frontend board** ubicado en `frontend`, que se instala con `tasker install`. Añadir un servicio `tasker-board` al Docker Compose, un `Dockerfile.frontend`, variables de entorno y CORS en la API, y pasos deterministas para construir, ejecutar y verificar la UI junto con la API, Neo4j y Redis. Todo debe ser explícito y reproducible para que agentes y desarrolladores humanos puedan levantar la pila completa sin ambigüedades.

---

### Objetivo exacto que debe entregar el agente
1. Mantener todos los requisitos originales de Issue 018 (FastAPI, OpenAPI, endpoints, tests, Dockerfile.api, docker-compose.api.yml, documentación) y además:
2. Integrar el frontend board:
   - Añadir `Dockerfile.frontend` en `frontend/`.
   - Añadir servicio `tasker-board` en `docker-compose.api.yml` y en `docker-compose.dev.yml` (si existe).
   - Asegurar que `tasker install` se ejecute durante la etapa de build del contenedor `tasker-board` o que el contenedor `tasker-dev` ejecute `tasker install` y comparta los artefactos con `tasker-board` mediante volumen.
   - Exponer el board en el puerto **8080** en el host.
3. Habilitar CORS en la API para permitir orígenes del board en desarrollo (`http://localhost:8080`) y documentarlo.
4. Proveer variables de entorno y secretos necesarios para que el frontend pueda llamar a la API:
   - `TASKER_API_URL` (ej. `http://api:8000` en compose; `http://localhost:8000` en host)
   - `TASKER_AUTH_TOKEN` (solo en desarrollo; documentar riesgo)
5. Añadir healthcheck para `tasker-board` y pasos de build reproducibles.
6. Actualizar documentación `tasker/api/API.md` y `README.md` con instrucciones para levantar la pila completa y acceder al board.
7. Añadir tests de integración que verifiquen que el board puede cargar la página principal y que la API responde a una petición CORS desde el origen del board.
8. Crear branch `feature/api-fastapi-openapi-board` y abrir PR con el PR body exacto provisto más abajo.

---

### Archivos a añadir o modificar exactos
- `frontend/Dockerfile.frontend` **(nuevo)**
- `docker-compose.api.yml` **(modificar)** — añadir servicio `tasker-board`
- `docker-compose.dev.yml` **(modificar si existe)** — añadir servicio `tasker-board`
- `tasker/api/app.py` **(modificar)** — añadir CORS middleware y variable `TASKER_API_ALLOW_ORIGINS`
- `tasker/api/API.md` **(modificar)** — documentar board y CORS
- `README.md` **(modificar)** — añadir sección Local development con comandos para levantar board
- `tests/integration/test_api_integration.py` **(modificar)** — añadir verificación de board health and CORS
- `Dockerfile.frontend` dentro de `frontend/` **(nuevo)** — build y serve
- `tasker/cli/wiring.py` **(modificar opcional)** — documentar `tasker install` hook
- `examples/board/index.html` **(nuevo opcional)** — ejemplo mínimo si frontend no tiene build

---

### Contenido exacto para Dockerfile.frontend

Cree `frontend/Dockerfile.frontend` con el contenido exacto siguiente:

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Ejecutar tasker install si está disponible en el contexto (opcional)
# Esto permite que tasker install prepare assets si el proyecto lo requiere
RUN if [ -f /app/tasker_install_marker ]; then echo "tasker install marker present"; fi
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g http-server
COPY --from=build /app/dist /app/dist
ENV NODE_ENV=production
EXPOSE 8080
CMD ["http-server", "dist", "-p", "8080", "-c-1"]
```

---

### Modificación exacta para docker-compose.api.yml

En `docker-compose.api.yml` añada el servicio `tasker-board` con el bloque exacto siguiente (insertar bajo servicios):

```yaml
  tasker-board:
    build:
      context: .
      dockerfile: frontend/Dockerfile.frontend
    image: tasker-board:local
    working_dir: /app
    environment:
      TASKER_API_URL: "http://api:8000"
      TASKER_AUTH_TOKEN: "${TASKER_AUTH_TOKEN:-}"
    ports:
      - "8080:8080"
    volumes:
      - ./frontend:/app:cached
    depends_on:
      api:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/ || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 6
```

Si existe `docker-compose.dev.yml`, aplique el mismo bloque allí, ajustando `TASKER_API_URL` a `http://api:8000` o a `http://host.docker.internal:8000` según el flujo.

---

### Modificación exacta para FastAPI CORS

En `tasker/api/app.py` (al inicio, después de crear `app`) inserte exactamente este bloque para habilitar CORS:

```python
from fastapi.middleware.cors import CORSMiddleware

# Allow origins configurable via env var TASKER_API_ALLOW_ORIGINS (comma separated)
allow_origins_env = os.getenv("TASKER_API_ALLOW_ORIGINS", "http://localhost:8080")
allow_origins = [o.strip() for o in allow_origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Documente en `tasker/api/API.md` que en producción `TASKER_API_ALLOW_ORIGINS` debe contener la URL del board y no usar `*`.

---

### `tasker install` y build del frontend

Dos opciones deterministas documentadas; elija una:

**Opción A Build en la imagen frontend (recomendada)**  
- `tasker install` sigue siendo comando de conveniencia local. El Dockerfile.frontend realiza `npm ci` y `npm run build`. No es necesario ejecutar `tasker install` en el contenedor.

**Opción B Ejecutar tasker install en tasker-dev y compartir artefactos**  
- Añadir en `docker-compose.dev.yml` un paso para ejecutar `tasker install` dentro de `tasker-dev` y montar `frontend/dist` como volumen compartido con `tasker-board`. Ejemplo de comando reproducible:
  ```bash
  docker compose -f docker-compose.dev.yml exec -T tasker-dev bash -lc "python -m pip install -e . && tasker install"
  ```

Documente en README que `tasker install` debe producir `frontend/dist` si el proyecto lo requiere.

---

### Variables de entorno y seguridad

Documente y use las siguientes variables:
- `TASKER_API_URL` — URL que el frontend usa para llamar a la API.
- `TASKER_AUTH_TOKEN` — token de desarrollo para el frontend (no usar en producción).
- `TASKER_API_ALLOW_ORIGINS` — orígenes permitidos por CORS (por defecto `http://localhost:8080`).
- `TASKER_INTEGRATION` — para pruebas de integración.

Advertencia en la documentación: **no** inyectar tokens de producción en el frontend; usar flujo de autenticación seguro en producción.

---

### Tests de integración actualizados

Modificar `tests/integration/test_api_integration.py` para incluir verificación del board. Añadir estas comprobaciones exactas:

```python
# dentro de test_api_create_and_context_end_to_end o en un nuevo test
# Verificar que el board responde
r_board = requests.get("http://localhost:8080/")
assert r_board.status_code in (200, 301, 302)
# Verificar CORS preflight hacia la API desde origen del board
headers = {"Origin": "http://localhost:8080", "Access-Control-Request-Method": "GET"}
r_pre = requests.options(f"{BASE}/api/v1/issues/api-1/context", headers=headers)
assert r_pre.status_code in (200, 204)
```

Marcar el test como `integration` y saltarlo si `TASKER_INTEGRATION` no está seteado.

---

### Documentación exacta a añadir o modificar

**README.md** — añadir sección Local development con el bloque exacto:

```markdown
Local development

Start API, Neo4j, Redis and Board:
docker compose -f docker-compose.api.yml up -d

Build frontend and install (if needed):
# Option A: frontend image builds itself
# Option B: run tasker install inside tasker-dev
docker compose -f docker-compose.api.yml exec -T tasker-dev bash -lc "python -m pip install -e . && tasker install"

Open the board:
http://localhost:8080

Open API docs:
http://localhost:8000/docs
```

**tasker/api/API.md** — añadir sección Board Integration con el contenido exacto:

```
Board Integration

- The frontend board is served at http://localhost:8080 when docker compose is used.
- The board expects TASKER_API_URL to point to the API (default http://api:8000 in compose).
- Configure CORS via TASKER_API_ALLOW_ORIGINS (comma separated). Default: http://localhost:8080
- For development only: set TASKER_AUTH_TOKEN to a development token and inject it into the frontend environment.
- Do not expose production tokens to client-side code.
```

---

### Comandos exactos para ejecutar y verificar

```bash
git checkout -b feature/api-fastapi-openapi-board
# crear/editar archivos según lo especificado
python -m pip install -e .
# construir y levantar la pila
docker compose -f docker-compose.api.yml up -d --build
# opcional: ejecutar tasker install dentro de tasker-dev si eliges la opción B
docker compose -f docker-compose.api.yml exec -T tasker-dev bash -lc "python -m pip install -e . && tasker install"
# esperar salud de servicios (Neo4j, api, board)
# verificar API y board
curl -sSf http://localhost:8000/docs >/dev/null
curl -sSf http://localhost:8080/ >/dev/null
# ejecutar tests de integración marcados
export TASKER_INTEGRATION=1
pytest tests/integration/test_api_integration.py -q -m integration
# commit y push
git add frontend/Dockerfile.frontend docker-compose.api.yml tasker/api/app.py tasker/api/API.md README.md tests/integration/test_api_integration.py
git commit -m "feat(api): integrate frontend board into docker-compose, enable CORS and add frontend Dockerfile"
git push origin feature/api-fastapi-openapi-board
```

---

### PR body exacto a pegar

```
Summary:
- Extended Issue 018 to integrate the frontend board located in frontend/.
- Added frontend Dockerfile frontend/Dockerfile.frontend and tasker-board service to docker-compose.api.yml.
- Enabled CORS in tasker/api/app.py configurable via TASKER_API_ALLOW_ORIGINS.
- Documented board integration in tasker/api/API.md and README.md.
- Updated integration tests to verify board health and CORS preflight.
- Provided deterministic build and run commands and guidance for tasker install usage.

Verification steps executed by this agent:
1. Built images and started services: docker compose -f docker-compose.api.yml up -d --build.
2. Verified API docs reachable at http://localhost:8000/docs.
3. Verified board reachable at http://localhost:8080.
4. Ran integration tests with TASKER_INTEGRATION=1 (passed when environment available).

Files changed:
- frontend/Dockerfile.frontend
- docker-compose.api.yml
- tasker/api/app.py
- tasker/api/API.md
- README.md
- tests/integration/test_api_integration.py

Notes:
- Two integration flows supported: build frontend inside its image (recommended) or run tasker install inside tasker-dev and share artifacts.
- Do not inject production tokens into the frontend. Use secure auth flows in production.
```

---

### Acceptance criteria actualizadas
- `frontend/Dockerfile.frontend` existe y permite construir y servir el board en `:8080`.
- `docker-compose.api.yml` incluye el servicio `tasker-board` con healthcheck y `TASKER_API_URL` apuntando a `api`.
- `tasker/api/app.py` habilita CORS configurable por `TASKER_API_ALLOW_ORIGINS`.
- `README.md` y `tasker/api/API.md` documentan cómo levantar la pila y acceder al board.
- Tests de integración verifican que el board responde y que la API acepta preflight CORS desde `http://localhost:8080`.
- Branch `feature/api-fastapi-openapi-board` creado y PR abierto con el PR body exacto arriba.

---