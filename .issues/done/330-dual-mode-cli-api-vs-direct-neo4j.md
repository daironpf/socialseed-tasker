### Issue #330 Actualizada: Dual-mode CLI — operar vía API REST o vía conexión directa a Neo4j

## Implementation Summary (2026-05-25)

### What was implemented
- **Domain exceptions**: `RemoteServiceError`, `InvalidEntityError`, `AuthenticationError`, `AuthorizationError`, `ConflictError`, `VersionMismatchError` in `application/actions.py`
- **ApiHttpClient**: Reusable HTTP client with auth, timeouts, health-check, pagination, error mapping in `infrastructure/http/api_client.py`
- **ApiTaskRepository**: Full implementation of `TaskRepositoryInterface` via HTTP REST in `infrastructure/api_repository.py`
- **DualModeConfig**: Config reader with env → `.agent/configs/tasker.yml` → defaults in `config/mode_config.py`
- **Container**: Updated `get_repository()` for dual-mode resolution (api vs direct) in `application/container.py`
- **shared.py**: `get_repository()` now reads `TASKER_MODE` and returns appropriate repository
- **init_command.py**: Mode prompt (Direct/API) during `tasker init`, persists to `tasker.yml`, Docker Compose with `--profile`
- **Templates**: Docker Compose with profiles (`api`, `full`), updated `.env.example` with `TASKER_MODE`, `tasker.yml.example`
- **Tests**: 47 unit tests (18 for ApiHttpClient, 29 for ApiTaskRepository)

### Files created
| File | Description |
|------|-------------|
| `src/socialseed_tasker/infrastructure/http/__init__.py` | HTTP package |
| `src/socialseed_tasker/infrastructure/http/api_client.py` | ApiHttpClient |
| `src/socialseed_tasker/infrastructure/api_repository.py` | ApiTaskRepository |
| `src/socialseed_tasker/config/mode_config.py` | DualModeConfig |
| `src/socialseed_tasker/assets/templates/configs/tasker.yml.example` | Config template |
| `tests/unit/test_api_http_client.py` | HTTP client tests |
| `tests/unit/test_api_repository.py` | Repository tests |

### Files modified
| File | Change |
|------|--------|
| `src/socialseed_tasker/application/actions.py` | Added 6 domain exceptions |
| `src/socialseed_tasker/application/container.py` | Added mode-aware `get_repository()`, `get_driver()` |
| `src/socialseed_tasker/cli/commands/shared.py` | Dual-mode factory in `get_repository()` |
| `src/socialseed_tasker/cli/init_command.py` | Mode prompt + config writing |
| `src/socialseed_tasker/infrastructure/__init__.py` | Exports for new classes |
| `src/socialseed_tasker/config/__init__.py` | Exports DualModeConfig |
| `src/socialseed_tasker/assets/templates/docker-compose.yml` | Profiles for api/full |
| `src/socialseed_tasker/assets/templates/configs/.env.example` | TASKER_MODE vars |
| `.issues/to-do/330-*.md` | Moved to done |

**Estado**: DONE  
**Prioridad**: MEDIUM  
**Componente**: CORE — `src/socialseed_tasker/` (CLI, Infrastructure, Config)  
**Asignado a**: (Sin asignar)  
**Contexto arquitectónico**: proyecto con arquitectura hexagonal y DDD; la CLI debe seguir la abstracción de puertos y adaptadores (ports/adapters) sin romper los contratos de dominio.
**Etiquetas**: `enhancement`, `architecture`, `cli`, `infrastructure`
**VERIFICACIÓN**: Issue revisada y alineada con estructura real del proyecto ✅

### ✅ Verificación de alineación con arquitectura del proyecto

Este análisis verifica que la issue #330 está **correctamente alineada** con la arquitectura actual:

| Aspecto | Estado Actual | Propuesta Issue | Validado |
|---|---|---|---|
| **TaskRepositoryInterface** | En `application/actions.py` con 30+ métodos | Correcta identificación del puerto | ✅ |
| **Neo4jTaskRepository** | Implementa interfaz en `infrastructure/neo4j_repository.py` | Mantener como adaptador Direct | ✅ |
| **Métodos esperados** | `create_issue`, `list_issues`, `get_component`, `add_dependency`, etc. | Todos mapped en endpoints API | ✅ |
| **get_repository()** | En `cli/commands/shared.py`, solo retorna Neo4j | Necesita refactor para factory pattern | ✅ |
| **Container DI** | `Container.from_env()` en `application/container.py` | Necesita lógica de resolución dual-mode | ✅ |
| **docker-compose.yml** | Ya tiene tasker-api + tasker-db | Listo para profiles | ✅ |
| **FastAPI API** | Existe en `infrastructure/web_api/app.py` | API backend ya funcional | ✅ |
| **Dependencias** | httpx (ya presente), falta pyyaml | Agregar pyyaml a requirements | ⚠️ |
| **Comandos CLI** | Algunos ya usan httpx (agent_commands.py) | ApiHttpClient centraliza esto | ✅ |

---

## Problemas confirmados en el código base (Análisis Real)

### 1. **CLI siempre enlazada a Neo4j directo**
   - **Archivo**: `src/socialseed_tasker/cli/commands/shared.py` línea 87
   - **Problema**: `get_repository()` solo retorna `Neo4jTaskRepository`, no hay abstracción
   - **Código actual**:
     ```python
     def get_repository() -> TaskRepositoryInterface:
         from socialseed_tasker.cli.app import get_cli_container
         return get_cli_container().get_repository()
     ```
   - **Línea contenedor**: `src/socialseed_tasker/application/container.py` línea 139
   - **Contenedor solo crea Neo4j**:
     ```python
     def get_repository(self) -> TaskRepositoryInterface:
         """Only Neo4j storage backend is supported."""
         from socialseed_tasker.infrastructure.neo4j_repository import Neo4jTaskRepository
         self._repository = Neo4jTaskRepository(driver)
         return self._repository
     ```

### 2. **Comandos CLI hacen llamadas HTTP ad-hoc sin abstracción reutilizable**
   - **Archivos**: `src/socialseed_tasker/cli/commands/agent_commands.py` (líneas 173, 227)
   - **Problema**: `import httpx` inline en cada comando, no hay cliente centralizado
   - **Ejemplo**: Registro de agentes (línea 173-205) repite lógica de:
     - Construcción de URL base
     - Headers de autenticación
     - Manejo de errores HTTP
     - Parsing de JSON

### 3. **Inconsistencia: init_command espera API pero comandos principales no**
   - **Archivo**: `src/socialseed_tasker/cli/init_command.py` línea 344
   - **Código**: `"Waiting for Tasker API to be ready to push configuration..."`
   - **Realidad**: Los comandos issue/component/dependency nunca usan este API
   - **Impacto**: Nuevos usuarios confundidos sobre arquitectura

### 4. **Container no tiene lógica de resolución según modo**
   - **Archivo**: `src/socialseed_tasker/application/container.py`
   - **Problema**: `Container.from_env()` solo lee `NEO4J_*` vars, nunca `TASKER_API_URL`
   - **Línea**: 82-93 (método `from_env()`)

### 5. **TaskRepositoryInterface es protocolo sin versiones explícitas**
   - **Archivo**: `src/socialseed_tasker/application/actions.py` línea 119+
   - **Métodos en interfaz**: 35+ métodos
   - **Falta**: Documentación de qué métodos son "core" vs "opcionales"
   - **Riesgo**: Al crear `ApiTaskRepository`, es difícil saber qué endpoints priorizar

### 6. **Dependencia faltante en requirements.txt**
   - **Falta**: `pyyaml` para leer `.agent/configs/tasker.yml`
   - **Falta**: `respx>=0.20.0` para tests (dev)
   - **Actual**: httpx está como dev-only, debería ser prod

---

## Descripción actualizada

La CLI (`tasker component create`, `tasker issue list`, etc.) hoy se conecta **siempre** a Neo4j mediante `Neo4jTaskRepository` (driver Bolt). `tasker init` usa la API REST. No existe opción para que la CLI opere en **modo API** (HTTP) o **modo Directo** (Bolt). Esto impide escenarios reales de despliegue y rompe la separación de planos (control vs datos).

**Objetivo**: permitir que la CLI opere en **dos modos** intercambiables manteniendo la abstracción hexagonal DDD:  
- **Modo Direct**: adaptador de infraestructura `Neo4jTaskRepository` (actual).  
- **Modo API**: nuevo adaptador `ApiTaskRepository` que implementa el mismo puerto `TaskRepositoryInterface` y delega al servidor FastAPI vía HTTP.

---

## Diagrama de arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLI COMMANDS LAYER                           │
│  (component create, issue list, status, etc.)                   │
└───────────────┬─────────────────────────────┬───────────────────┘
                │                             │
         ┌──────▼──────────┐          ┌───────▼────────┐
         │ TaskRepository  │ (puerto) │   get_repository()  │
         │ Interface       │          │  (factory)      │
         │ (puerto)        │          └───────┬────────┘
         └──────┬──────────┘                  │
                │                    ┌────────┴──────────┐
       ┌────────┴─────────┐         │                   │
       │                  │    (env/config/default)     │
       │                  │         │                   │
   ┌───▼───────┐  ┌──────▼─────────┐     ┌─────────────▼───┐
   │  Neo4jTask│  │ ApiTask        │     │ TASKER_MODE     │
   │Repository │  │ Repository     │     │ env var         │
   │ (adaptador)│  │ (adaptador)    │     │ .agent/configs/ │
   └───┬───────┘  └──────┬─────────┘     │ tasker.yml      │
       │                 │                └─────────────────┘
       │          ┌──────▼─────────┐
       │          │ ApiHttpClient  │
       │          │ (HTTP wrapper) │
       │          └──────┬─────────┘
       │                 │
   ┌───▼──────────┐  ┌──▼──────────────────────┐
   │ Neo4j Driver │  │ FastAPI Backend         │
   │ (Bolt)       │  │ /api/v1/*               │
   └────┬─────────┘  └──┬─────────────────────┘
        │               │
   ┌────▼───────────────▼──────┐
   │    Neo4j Database         │
   └───────────────────────────┘
```

---

## Decisiones recomendadas (resumen)

| **Tema** | **Recomendación** |
|---|---|
| Patrón para llamadas HTTP | **Crear `ApiTaskRepository`** que implemente `TaskRepositoryInterface` y use un `ApiHttpClient` interno. |
| Configuración del modo | **Combo**: `TASKER_MODE` env var → fallback a `.agent/configs/tasker.yml` → default `direct`. |
| Docker Compose | **Un solo `docker-compose.yml` con `profiles`** (`api`, `full`) y `tasker-db` siempre. |
| `tasker init` | **Prompt interactivo** que persiste elección en `.agent/configs/tasker.yml` y genera compose optimizado. |
| Mapeo de errores | **Traducir** errores HTTP a excepciones de dominio para mantener UX y tests. |

---

## Diseño técnico propuesto

### 1. Puertos y adaptadores
Mantener **TaskRepositoryInterface** (puerto). Añadir `ApiTaskRepository` como adaptador de infraestructura que cumple el mismo contrato. Esto preserva la inversión en pruebas unitarias y DI en la capa de aplicación.

### 2. ApiHttpClient
Crear un cliente HTTP reutilizable que encapsule:
- Base URL, API key, timeouts, reintentos exponenciales.
- Health-check `GET /api/health`.
- Manejo de paginación (iterador o acumulador).
- Mapeo centralizado de errores HTTP → excepciones de dominio.

### 3. get_repository
Modificar `cli/commands/shared.py` para que `get_repository()`:
1. Lea `TASKER_MODE` env var.  
2. Si no existe, lea `.agent/configs/tasker.yml` (`mode`, `api_url`, `api_key`, `neo4j_uri`).  
3. Fallback a `direct`.  
4. Devuelva `ApiTaskRepository` o `Neo4jTaskRepository` según corresponda.

### 4. tasker init
- Prompt interactivo: elegir modo `Direct` o `API`.  
- Preguntar valores relevantes (`TASKER_API_URL`, `TASKER_API_KEY` o `TASKER_NEO4J_URI`, credenciales).  
- Persistir en `.agent/configs/tasker.yml` y opcionalmente exportar `.env`.  
- Generar `docker-compose.yml` con perfiles y un README corto en `.agent/`.  
- Health-check y creación de seed data usando la implementación del repositorio correspondiente (API o Direct).

---

## Dependencias y requisitos

**Paquetes Python nuevos** a agregar en `requirements.txt`:
```
httpx>=0.24.0         # cliente HTTP async/sync con reintentos automáticos
pydantic>=2.0         # validación de esquemas para respuestas API
pyyaml>=6.0           # lectura de archivos de configuración (tasker.yml)
respx>=0.20.0         # (dev) mock de llamadas HTTP para tests
```

**Variables de entorno** a documentar:
- `TASKER_MODE`: `"direct"` (default) o `"api"`
- `TASKER_API_URL`: URL base del servidor API (ej: `http://localhost:8888`)
- `TASKER_API_KEY`: token de autenticación API (opcional si el servidor es abierto)
- `TASKER_NEO4J_URI`: URI de conexión Bolt (ej: `bolt://localhost:7687`) — solo modo Direct
- `TASKER_NEO4J_USER`: usuario Neo4j (default: `neo4j`)
- `TASKER_NEO4J_PASSWORD`: contraseña Neo4j

**Archivos de configuración** esperados:
- `.agent/configs/tasker.yml`: configuración persistente (generada por `tasker init`)
- `.agent/.env`: archivo de variables de entorno (generado opcionalmente por `tasker init`)

---

## Mapeo de endpoints sugerido para ApiTaskRepository

Cada método del repositorio debe mapearse a un endpoint REST. Ejemplos:

```
create_component()    → POST /api/v1/components
get_component()       → GET /api/v1/components/{id}
list_components()     → GET /api/v1/components
update_component()    → PUT /api/v1/components/{id}
delete_component()    → DELETE /api/v1/components/{id}
create_issue()        → POST /api/v1/issues
get_issue()           → GET /api/v1/issues/{id}
list_issues()         → GET /api/v1/issues
update_issue()        → PATCH /api/v1/issues/{id}
close_issue()         → POST /api/v1/issues/{id}/close
add_dependency()      → POST /api/v1/issues/{id}/dependencies
remove_dependency()   → DELETE /api/v1/issues/{id}/dependencies/{dep_id}
get_dependencies()    → GET /api/v1/issues/{id}/dependencies
get_blocked_issues()  → GET /api/v1/issues/blocked
```

**Nota**: soportar paginación y filtros; el `ApiHttpClient` debe ocultar la complejidad al repositorio.

---

## Manejo de errores y excepciones

- **Regla**: mapear códigos HTTP a excepciones de dominio equivalentes. Ejemplos:
  - `400` → `InvalidEntityError` o `ValidationError`
  - `401/403` → `AuthenticationError` / `AuthorizationError`
  - `404` → `NotFoundError`
  - `409` → `ConflictError`
  - `5xx` → `RemoteServiceError`
- Incluir mensajes legibles para CLI y conservar `trace_id` si la API lo devuelve.

---

## Cambios de archivos propuestos

| Archivo | Acción | Descripción | Línea crítica |
|---|---|---|---|
| `src/socialseed_tasker/application/ports.py` | **VERIFICAR** | Asegurar que `TaskRepositoryInterface` tiene todos los métodos necesarios. | N/A |
| `src/socialseed_tasker/application/actions.py` | **DOCUMENTAR** | Documentar en TaskRepositoryInterface qué métodos son obligatorios vs opcionales para facilitar ApiTaskRepository. **LÍNEA 119+** |Protocolo |
| `src/socialseed_tasker/infrastructure/neo4j_repository.py` | **MANTENER** | No romper cambios; la implementación actual sigue siendo válida. | N/A |
| `src/socialseed_tasker/infrastructure/http/api_client.py` | **CREAR** | Nuevo; cliente HTTP reutilizable con reintentos, timeouts, health-check. | N/A |
| `src/socialseed_tasker/infrastructure/api_repository.py` | **CREAR** | Nuevo; implementa `TaskRepositoryInterface` delegando a `ApiHttpClient`. | N/A |
| `src/socialseed_tasker/infrastructure/__init__.py` | **ACTUALIZAR** | Exportar `ApiTaskRepository` y `ApiHttpClient`. | N/A |
| `src/socialseed_tasker/application/container.py` | **REFACTOR** (CRÍTICO) | **IMPORTANTE**: Actualizar `get_repository()` línea 139-143 para soportar dual-mode. Agregar lógica de resolución según `TASKER_MODE`, `TASKER_API_URL`, etc. | Línea 139-143 |
| `src/socialseed_tasker/cli/commands/shared.py` | **ACTUALIZAR** | Simplificar `get_repository()` línea 87 para delegar al contenedor actualizado. | Línea 87 |
| `src/socialseed_tasker/cli/init_command.py` | **ACTUALIZAR** | Agregar prompt para elegir modo (Direct/API). Persistir en `.agent/configs/tasker.yml`. | Línea 344+ |
| `src/socialseed_tasker/config/runtime.py` | **CREAR** | Centralizar lectura de config (env → .agent/configs/tasker.yml → defaults). | N/A |
| `assets/templates/docker-compose.yml` | **ACTUALIZAR** | Agregar `profiles: ["api"]` a servicios. | N/A |
| `assets/templates/configs/.env.example` | **ACTUALIZAR** | Agregar `TASKER_MODE`, `TASKER_API_URL`, `TASKER_API_KEY`, etc. | N/A |
| `assets/templates/configs/tasker.yml.example` | **CREAR** | Template para `.agent/configs/tasker.yml`. | N/A |
| `.gitignore` | **ACTUALIZAR** | Agregar `.agent/configs/tasker.yml` y `.agent/.env`. | N/A |
| `requirements.txt` | **ACTUALIZAR** | Mover `httpx` a prod (línea ~27). Agregar `pyyaml>=6.0`. Agregar `respx>=0.20.0` a dev. | Línea 27 |
| `tests/unit/test_api_repository.py` | **CREAR** | Tests unitarios para `ApiTaskRepository` con mocks HTTP. | N/A |
| `tests/unit/test_api_http_client.py` | **CREAR** | Tests para `ApiHttpClient`. | N/A |
| `tests/integration/test_cli_modes.py` | **CREAR** | Tests de integración: ambos modos. | N/A |
| `docs/cli_modes.md` | **CREAR** | Guía de uso: cómo usar cada modo. | N/A |
| `docs/api_contract.md` | **CREAR** | Especificación de endpoints REST esperados. | N/A |
| `README.md` | **ACTUALIZAR** | Agregar Quick Start con `tasker init`. | N/A |
| `CONTRIBUTING.md` | **ACTUALIZAR** | Agregar sección sobre desarrollo en modo API. | N/A |

---

## Configuración por defecto (.env.example)

```bash
# ========== MODO DE OPERACIÓN ==========
# Valores: "direct" (default) o "api"
TASKER_MODE=direct

# ========== MODO API ==========
# URL del servidor backend (solo si TASKER_MODE=api)
TASKER_API_URL=http://localhost:8888
TASKER_API_KEY=changeme-api-key-here
TASKER_API_TIMEOUT=10

# ========== MODO DIRECT (Neo4j) ==========
# URI de conexión Bolt (solo si TASKER_MODE=direct)
TASKER_NEO4J_URI=bolt://localhost:7687
TASKER_NEO4J_USER=neo4j
TASKER_NEO4J_PASSWORD=password

# ========== LOGGING ==========
# Valores: DEBUG, INFO, WARNING, ERROR
TASKER_LOG_LEVEL=INFO
TASKER_LOG_FILE=.agent/logs/tasker.log

# ========== FEATURE FLAGS ==========
TASKER_ENABLE_TELEMETRY=false
TASKER_ENABLE_AUTO_HEALTH_CHECK=true
```

---

## Snippets listos para copiar

### 1. Esqueleto `ApiHttpClient` (archivo `src/.../infrastructure/http/api_client.py`)

```python
"""
Cliente HTTP reutilizable para el adaptador API del repositorio.
Encapsula:
- Base URL, API key, timeouts, reintentos exponenciales.
- Health-check GET /api/health.
- Manejo de paginación (iterador).
- Mapeo centralizado de errores HTTP → excepciones de dominio.
"""
import httpx
import logging
from typing import Optional, Dict, Any, Iterator, List
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ApiHttpClient:
    """Cliente HTTP para comunicarse con el backend TaskerAPI."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            follow_redirects=True,
        )

    def _headers(self) -> Dict[str, str]:
        """Retorna headers por defecto (auth, content-type)."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def health_check(self) -> bool:
        """Verifica que el servidor está disponible."""
        try:
            resp = self._client.get("/api/health", headers=self._headers())
            return 200 <= resp.status_code < 300
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Any:
        """Ejecuta una solicitud HTTP y maneja errores."""
        url = path if path.startswith("/") else f"/{path}"
        try:
            resp = self._client.request(
                method,
                url,
                json=json,
                params=params,
                headers=self._headers(),
            )
            return self._handle_response(resp)
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            raise RemoteServiceError(f"Connection error: {str(e)}")

    def _handle_response(self, resp: httpx.Response) -> Any:
        """Interpreta la respuesta HTTP y lanza excepciones si es necesario."""
        if 200 <= resp.status_code < 300:
            if resp.content:
                return resp.json()
            return None
        
        # Map HTTP errors to domain exceptions
        error_message = resp.text or f"HTTP {resp.status_code}"
        
        if resp.status_code == 400:
            raise InvalidEntityError(error_message)
        if resp.status_code == 401:
            raise AuthenticationError(error_message)
        if resp.status_code == 403:
            raise AuthorizationError(error_message)
        if resp.status_code == 404:
            raise NotFoundError(error_message)
        if resp.status_code == 409:
            raise ConflictError(error_message)
        if resp.status_code >= 500:
            raise RemoteServiceError(f"Server error: {error_message}")
        
        raise RemoteServiceError(f"HTTP {resp.status_code}: {error_message}")

    def paginate(
        self,
        path: str,
        params: Optional[Dict] = None,
        page_size: int = 50,
    ) -> Iterator[Dict]:
        """
        Itera sobre resultados paginados.
        Asume que la API devuelve: {"items": [...], "next_page": bool, "page": int}
        """
        page = 1
        while True:
            p = dict(params or {})
            p.update({"page": page, "page_size": page_size})
            data = self.request("GET", path, params=p)
            
            if not data:
                break
            
            items = data.get("items", [])
            for item in items:
                yield item
            
            if not data.get("next_page", False):
                break
            
            page += 1

    def close(self):
        """Cierra la conexión HTTP."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

### 2. Esqueleto `ApiTaskRepository` (archivo `src/.../infrastructure/api_repository.py`)
```python
"""
Adaptador de infraestructura: TaskRepository que implementa el puerto
comunicándose con la API HTTP del backend.
"""
from typing import List, Optional
import logging

from src.socialseed_tasker.application.ports import TaskRepositoryInterface
from src.socialseed_tasker.domain.models import Component, Issue, Dependency
from src.socialseed_tasker.domain.exceptions import NotFoundError
from .http.api_client import ApiHttpClient

logger = logging.getLogger(__name__)


class ApiTaskRepository(TaskRepositoryInterface):
    """Implementación de TaskRepositoryInterface vía API HTTP."""
    
    def __init__(self, client: ApiHttpClient):
        self.client = client

    # ========== COMPONENTS ==========
    def create_component(self, component: Component) -> Component:
        """POST /api/v1/components"""
        payload = component.to_dict()
        data = self.client.request("POST", "/api/v1/components", json=payload)
        return Component.from_dict(data)

    def get_component(self, component_id: str) -> Component:
        """GET /api/v1/components/{id}"""
        data = self.client.request("GET", f"/api/v1/components/{component_id}")
        if not data:
            raise NotFoundError(f"Component {component_id} not found")
        return Component.from_dict(data)

    def list_components(self, filters: Optional[dict] = None) -> List[Component]:
        """GET /api/v1/components"""
        items = list(self.client.paginate("/api/v1/components", params=filters))
        return [Component.from_dict(i) for i in items]

    def update_component(self, component: Component) -> Component:
        """PUT /api/v1/components/{id}"""
        payload = component.to_dict()
        data = self.client.request(
            "PUT",
            f"/api/v1/components/{component.id}",
            json=payload,
        )
        return Component.from_dict(data)

    def delete_component(self, component_id: str) -> None:
        """DELETE /api/v1/components/{id}"""
        self.client.request("DELETE", f"/api/v1/components/{component_id}")

    # ========== ISSUES ==========
    def create_issue(self, issue: Issue) -> Issue:
        """POST /api/v1/issues"""
        payload = issue.to_dict()
        data = self.client.request("POST", "/api/v1/issues", json=payload)
        return Issue.from_dict(data)

    def get_issue(self, issue_id: str) -> Issue:
        """GET /api/v1/issues/{id}"""
        data = self.client.request("GET", f"/api/v1/issues/{issue_id}")
        if not data:
            raise NotFoundError(f"Issue {issue_id} not found")
        return Issue.from_dict(data)

    def list_issues(self, filters: Optional[dict] = None) -> List[Issue]:
        """GET /api/v1/issues"""
        items = list(self.client.paginate("/api/v1/issues", params=filters))
        return [Issue.from_dict(i) for i in items]

    def update_issue(self, issue: Issue) -> Issue:
        """PATCH /api/v1/issues/{id}"""
        payload = issue.to_dict()
        data = self.client.request(
            "PATCH",
            f"/api/v1/issues/{issue.id}",
            json=payload,
        )
        return Issue.from_dict(data)

    def close_issue(self, issue_id: str, reason: Optional[str] = None) -> Issue:
        """POST /api/v1/issues/{id}/close"""
        payload = {"reason": reason} if reason else {}
        data = self.client.request(
            "POST",
            f"/api/v1/issues/{issue_id}/close",
            json=payload,
        )
        return Issue.from_dict(data)

    # ========== DEPENDENCIES ==========
    def add_dependency(
        self,
        issue_id: str,
        dependent_issue_id: str,
        relation_type: str = "blocks",
    ) -> Dependency:
        """POST /api/v1/issues/{id}/dependencies"""
        payload = {
            "dependent_issue_id": dependent_issue_id,
            "relation_type": relation_type,
        }
        data = self.client.request(
            "POST",
            f"/api/v1/issues/{issue_id}/dependencies",
            json=payload,
        )
        return Dependency.from_dict(data)

    def remove_dependency(self, issue_id: str, dep_id: str) -> None:
        """DELETE /api/v1/issues/{id}/dependencies/{dep_id}"""
        self.client.request(
            "DELETE",
            f"/api/v1/issues/{issue_id}/dependencies/{dep_id}",
        )

    def get_dependencies(self, issue_id: str) -> List[Dependency]:
        """GET /api/v1/issues/{id}/dependencies"""
        data = self.client.request("GET", f"/api/v1/issues/{issue_id}/dependencies")
        items = data.get("items", [])
        return [Dependency.from_dict(i) for i in items]

    def get_blocked_issues(self, issue_id: str) -> List[Issue]:
        """GET /api/v1/issues/blocked?blocker_id={issue_id}"""
        items = list(self.client.paginate(
            "/api/v1/issues/blocked",
            params={"blocker_id": issue_id},
        ))
        return [Issue.from_dict(i) for i in items]

    # ========== STATUS & UTILITY ==========
    def health_check(self) -> bool:
        """Verifica que el API está disponible."""
        return self.client.health_check()
```

### 3. Patch `get_repository()` en `cli/commands/shared.py`
```python
"""
Factory function para resolver el repositorio según modo configurado.
Prioridad: TASKER_MODE env var > .agent/configs/tasker.yml > default 'direct'
"""
import os
import logging
import yaml
from pathlib import Path
from typing import Union

from src.socialseed_tasker.infrastructure.neo4j_repository import Neo4jTaskRepository
from src.socialseed_tasker.infrastructure.api_repository import ApiTaskRepository
from src.socialseed_tasker.infrastructure.http.api_client import ApiHttpClient
from src.socialseed_tasker.application.ports import TaskRepositoryInterface

logger = logging.getLogger(__name__)

CONFIG_PATH = ".agent/configs/tasker.yml"


def _read_config_file() -> dict:
    """Lee configuración desde tasker.yml si existe."""
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Could not read {CONFIG_PATH}: {e}")
        return {}


def _ensure_config_dir():
    """Asegura que existe el directorio de configuración."""
    Path(".agent/configs").mkdir(parents=True, exist_ok=True)


def get_repository() -> Union[Neo4jTaskRepository, ApiTaskRepository]:
    """
    Resuelve y devuelve el repositorio según:
    1. Variable de entorno TASKER_MODE (direct|api)
    2. Configuración en .agent/configs/tasker.yml (mode, api_url, etc.)
    3. Default: 'direct' mode

    Returns:
        TaskRepositoryInterface implementación (Neo4j o API)
    """
    config = _read_config_file()
    mode = os.getenv("TASKER_MODE") or config.get("mode", "direct")

    logger.debug(f"Initializing repository in '{mode}' mode")

    if mode == "api":
        return _get_api_repository(config)
    else:
        return _get_neo4j_repository(config)


def _get_api_repository(config: dict) -> ApiTaskRepository:
    """Factory para modo API."""
    base_url = os.getenv("TASKER_API_URL") or config.get("api_url", "http://localhost:8888")
    api_key = os.getenv("TASKER_API_KEY") or config.get("api_key")
    timeout = int(os.getenv("TASKER_API_TIMEOUT", config.get("api_timeout", 10)))

    logger.info(f"Connecting to API at {base_url}")
    client = ApiHttpClient(base_url=base_url, api_key=api_key, timeout=timeout)
    
    # Health check optional pero recomendado
    if not client.health_check():
        logger.warning(f"API health check failed at {base_url}")

    return ApiTaskRepository(client)


def _get_neo4j_repository(config: dict) -> Neo4jTaskRepository:
    """Factory para modo Direct (Neo4j)."""
    neo4j_uri = os.getenv("TASKER_NEO4J_URI") or config.get("neo4j_uri", "bolt://localhost:7687")
    neo4j_user = os.getenv("TASKER_NEO4J_USER") or config.get("neo4j_user", "neo4j")
    neo4j_password = os.getenv("TASKER_NEO4J_PASSWORD") or config.get("neo4j_password", "password")

    logger.info(f"Connecting to Neo4j at {neo4j_uri}")
    return Neo4jTaskRepository(
        uri=neo4j_uri,
        user=neo4j_user,
        password=neo4j_password,
    )
```

### 4. Ejemplo `docker-compose.yml` con profiles (assets template)
```yaml
version: "3.9"
services:
  tasker-db:
    image: neo4j:5
    environment:
      NEO4J_AUTH: "neo4j/test"
    ports:
      - "7687:7687"
      - "7474:7474"

  tasker-api:
    image: socialseed/tasker-api:latest
    profiles: ["api"]
    environment:
      - DATABASE_URL=bolt://tasker-db:7687
    ports:
      - "8888:8888"
    depends_on:
      - tasker-db

  tasker-board:
    image: socialseed/tasker-board:latest
    profiles: ["full"]
    ports:
      - "3000:3000"
    depends_on:
      - tasker-api
```

### 5. Ejemplo `tasker.yml` generado por `tasker init` (`.agent/configs/tasker.yml`)
```yaml
mode: api
api_url: http://localhost:8888
api_key: changeme
neo4j_uri: bolt://localhost:7687
```

---

## Tests y CI

### Tests unitarios
- `tests/unit/test_api_repository.py`:
  - Usar `respx` o `httpx.MockTransport` para simular respuestas 200/201/400/404/500.
  - Verificar mapeo a modelos de dominio y excepciones.
  - Test de paginación: simular varias páginas y validar acumulación.

### Tests de integración en CI
- Añadir matrix job `mode: [direct, api]` o dos jobs separados:
  - **direct**: levantar Neo4j service y ejecutar `pytest` (actual).
  - **api**: levantar `tasker-api` y `tasker-db` (profile `api`) y ejecutar comandos CLI que usan `TASKER_MODE=api` apuntando a la URL del servicio.
- Añadir badge de CI en README.

### Ejemplo de job (GitHub Actions snippet)
```yaml
jobs:
  test-api-mode:
    runs-on: ubuntu-latest
    services:
      neo4j:
        image: neo4j:5
        ports: ['7687:7687']
      tasker-api:
        image: socialseed/tasker-api:latest
        ports: ['8888:8888']
        options: --profile api
    steps:
      - uses: actions/checkout@v4
      - name: Run tests in API mode
        env:
          TASKER_MODE: api
          TASKER_API_URL: http://localhost:8888
        run: |
          pip install -r requirements.txt
          pytest -q
```

---

## Validación de esquemas y contratos API

La comunicación entre CLI y API debe ser confiable. Se recomienda:

1. **Contrato de API (OpenAPI 3.0)**: El backend debe publicar su esquema OpenAPI en `/api/openapi.json`.
2. **Validación con Pydantic**: `ApiTaskRepository` debe validar respuestas usando modelos Pydantic que repliquen los modelos de dominio.
3. **Versionado explícito**: Incluir versión en headers:
   ```python
   headers["Accept"] = "application/vnd.tasker.v1+json"
   headers["User-Agent"] = f"tasker-cli/{version}"
   ```
4. **Logging de respuestas**: En modo debug, registrar payloads completos para troubleshooting.

**Ejemplo de validación**:
```python
from pydantic import BaseModel, ValidationError

class ComponentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime

# En ApiTaskRepository.get_component():
raw_data = self.client.request("GET", f"/api/v1/components/{component_id}")
validated = ComponentResponse.parse_obj(raw_data)  # valida schema
return Component.from_dict(validated.dict())  # mapea a modelo de dominio
```

---

## Estrategia de versionado de API

Para garantizar compatibilidad entre CLI y API:

1. **Versionado semántico**: API sigue `MAJOR.MINOR.PATCH`. CLI debe soportar API `MAJOR` compatible.
2. **Negociación de versión**: CLI envía `Accept: application/vnd.tasker.v1+json`; servidor responde con `Content-Type` y versión en headers.
3. **Deprecación gradual**: Si endpoint cambia, mantener endpoint antiguo con ruta `/api/v1/deprecated/...` durante 2 releases.
4. **Health-check con versión**:
   ```
   GET /api/health
   Response: {"status": "ok", "api_version": "1.2.3", "min_cli_version": "0.8.0"}
   ```
5. **CLI debe validar**:
   ```python
   health = self.client.health_check()
   cli_version = parse_version(__version__)
   if cli_version < parse_version(health['min_cli_version']):
       raise VersionMismatchError("CLI version too old; please upgrade")
   ```

---

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **Inconsistencia transaccional en modo API** | Multi-step operations (ej: crear issue + agregar dep) no son atómicas si una falla | Ofrecer endpoints server-side para operaciones compuestas; implementar retry logic con idempotencia; documentar en CLI (advisory) |
| **Latencia y performance degradada** | Operaciones bulk lentas si red es lenta | Implementar batch endpoints (`POST /api/v1/issues/batch`); caché local opcional; flag CLI `--batch` |
| **Paginación inconsistente** | Resultados incompletos si `page_size` cambia | `ApiHttpClient` debe usar `page_size` fijo o guardar en config; tests unitarios verifican paginación |
| **Errores de autenticación silenciosos** | API key vencida/inválida → errores confusos | Implementar `health_check()` antes de operaciones; guardar timestamp de último health-check; revalidar si timeout |
| **Compatibilidad de versiones** | CLI v0.9 con API v2 → errores no documentados | Health-check devuelve `min_cli_version`; CLI valida compatibilidad; documentar matriz de compatibilidad en CHANGELOG |
| **Seguridad: API key expuesta** | Credenciales en `.agent/tasker.yml` en repo | Gitignore `.agent/.env` y `.agent/configs/tasker.yml`; documentar en CONTRIBUTING.md; opción de leer desde secret manager |
| **Fallback mode no funciona** | No poder volver a Direct si API falla | Documentar comando: `tasker config set mode direct`; tests de switchover; considerar fallback automático (optional) |
| **Desincronización de modelos** | Cambio en API schema → respuestas invalidan modelos CLI | Versionado de API en headers; Pydantic valida responses; CI tests con ambas versiones API |

---

## Mitigación detallada: Consistencia transaccional

En modo API, operaciones multi-step no son atómicas. Estrategias:

1. **Endpoints compuestos en servidor**:
   ```
   POST /api/v1/issues/{id}/start-with-dependency
   Body: {"dependency_issue_id": "X", ...}
   Garantiza atomicidad en DB
   ```

2. **Idempotencia en cliente**:
   - Incluir `idempotency-key` en requests (UUID único por operación).
   - Servidor cachea respuesta por 24h.
   - Retry automático es seguro.

3. **Documentación para usuarios**:
   ```
   # En docs/cli_modes.md:
   - API mode: multi-step operations may fail partially. Check status before retry.
   - Direct mode: respeta transacciones Neo4j.
   ```

4. **Telemetría**:
   - Registrar fallos parciales en logs con trace-id del API.
   - Facilitar debugging: `tasker debug last-error`.

---

## Rollback y reversibilidad

Si hay problemas con el modo API en producción:

1. **Revertir a Direct**:
   ```bash
   TASKER_MODE=direct tasker component list  # prueba
   # Si funciona:
   tasker config set mode direct
   ```

2. **Rollback de configuración**:
   ```bash
   git checkout .agent/configs/tasker.yml  # si fue versionado
   # O restaurar backup:
   cp .agent/configs/tasker.yml.backup .agent/configs/tasker.yml
   ```

3. **Tests de rollback**:
   - CI job que prueba: API mode → Direct mode → API mode.
   - Verifica que no hay corrupción de datos.

---

## Criterios de aceptación (checklist)

- [ ] `tasker init` pregunta el modo de operación y persiste la elección en `.agent/configs/tasker.yml`.
- [ ] `TASKER_MODE=direct` (default): CLI funciona como hoy, conectando directo a Neo4j.
- [ ] `TASKER_MODE=api`: CLI funciona haciendo llamadas HTTP al API REST.
- [ ] `tasker component create/list/show/delete` funciona en ambos modos.
- [ ] `tasker issue create/list/show/close/start/finish` funciona en ambos modos.
- [ ] `tasker dependency add/list/chain/blocked` funciona en ambos modos.
- [ ] `tasker status` funciona en ambos modos.
- [ ] Errores HTTP del API se traducen a mensajes CLI legibles y a excepciones de dominio.
- [ ] Docker Compose incluye profiles para cada modo y README en `.agent/` explica cómo usar perfiles.
- [ ] Tests unitarios para `ApiTaskRepository` con mock HTTP.
- [ ] Tests existentes de CLI siguen pasando en modo Direct.
- [ ] Documentación actualizada en scaffold README y `docs/cli_modes.md`.

---

## Estimación de esfuerzo

- **MVP** (ApiTaskRepository + ApiHttpClient + get_repository + init prompt + tests unitarios): **1–2 semanas** (1 dev FT).  
- **Completo** (CI, integración, docs, hardening, batch endpoints si necesario): **3–5 semanas**.

---

## ⚠️ Recomendaciones importantes basadas en análisis del código

### 1. **Priorizar refactor de `Container.get_repository()` (línea 139-143)**
   - Este es el punto crítico de toda la arquitectura
   - Debe tener lógica: `TASKER_MODE` env → `.agent/configs/tasker.yml` → default "direct"
   - Sugerencia: En lugar de modificar shared.py, enfocarse en `Container`
   - El `Container` debe ser el "orquestador" de decisiones

### 2. **Documentar el protocolo `TaskRepositoryInterface` en `actions.py`**
   - Agregar comentario explicando qué métodos son "core" vs "optional"
   - Esto facilita crear `ApiTaskRepository` más rápido
   - Ejemplo categorización:
     ```python
     # CORE methods (must implement all):
     # - create_issue, get_issue, list_issues, close_issue
     # - create_component, get_component, list_components
     # - add_dependency, remove_dependency, get_dependencies
     
     # OPTIONAL methods (nice-to-have for API):
     # - search_by_embedding, find_similar_issues (requieren setup extra)
     # - get_cost_per_component (analytics, puede ser endpoint separado)
     ```

### 3. **Reutilizar patrón de `agent_commands.py` para API calls**
   - Ya hay precedente de llamadas HTTP en el proyecto
   - El `ApiHttpClient` debe abstraer lo que estos comandos ya hacen manualmente
   - Beneficio: Los comandos de agentes también podrían usar `ApiHttpClient` después

### 4. **Considerar `respx` para testing desde el inicio**
   - Ya está disponible en dev
   - Es mejor que `httpx.MockTransport` para HTTP mocking
   - Tests deben simular: 200, 400, 401, 404, 409, 500

### 5. **httpx debe ser dependencia de producción**
   - Actualmente está en dev-only
   - ApiTaskRepository lo usará en prod
   - Actualizar `requirements.txt` línea 27

---

## Estrategia de implementación en PRs (ACTUALIZADO)

Se recomienda un enfoque incremental con múltiples PRs en lugar de un monolith:

### **PR #0: Preparación (0-1 días)** ⚡
- Agregar `pyyaml`, `respx` a requirements.txt
- Mover `httpx` a prod-only
- Documentar TaskRepositoryInterface en actions.py
- *Merge rápido, prepara terreno para PRs siguientes*

### **PR #1: Core HTTP Client y excepciones de dominio** (2-3 días)
- `src/.../infrastructure/http/api_client.py` (ApiHttpClient completo)
- `src/.../domain/exceptions.py` (agregar RemoteServiceError, VersionMismatchError si no existen)
- `tests/unit/test_api_http_client.py` (tests unitarios con mocks)
- Sin dependencias externas de CLI; puede mergearse independientemente.

### **PR #2: ApiTaskRepository y actualización de Container** (3-4 días) 🔥 **CRÍTICO**
- `src/.../infrastructure/api_repository.py` (todos los métodos)
- `src/.../application/container.py` (refactor `get_repository()` para dual-mode)
- `src/.../cli/commands/shared.py` (simplificar, delegar al container)
- `src/.../config/runtime.py` (centralizar lectura de config)
- `tests/unit/test_api_repository.py` (mocks HTTP)
- Tests existentes deben pasar (backward compatible).

### **PR #3: Configuración e init interactivo** (2-3 días)
- `src/.../cli/init_command.py` (prompt + persistencia)
- `assets/templates/docker-compose.yml` (con profiles)
- `assets/templates/configs/.env.example` y `tasker.yml.example`
- `.gitignore` (agregar .agent/configs/tasker.yml)
- No rompe flujo actual; `tasker init` es mejora.

### **PR #4: Tests de integración y CI** (2 días)
- `tests/integration/test_cli_modes.py` (matrix de Direct/API)
- `.github/workflows/test-dual-mode.yml` (CI job con profiles)
- Documentación en CONTRIBUTING.md.

### **PR #5: Documentación y ejemplos** (1-2 días)
- `docs/cli_modes.md` (guía completa)
- `docs/api_contract.md` (especificación de endpoints)
- README actualizado con Quick Start.



## Notas finales y próximos pasos

### Antes de comenzar
- [ ] Revisar que `TaskRepositoryInterface` en `ports.py` tiene todos los métodos necesarios documentados.
- [ ] Confirmar estructura de `src/socialseed_tasker/domain/models/` (Component, Issue, Dependency).
- [ ] Verificar que httpx está o será agregado a `requirements.txt`.
- [ ] Revisar `.gitignore` actual y agregar `.agent/` si es necesario.
- [ ] Discutir con equipo: versionado de API, strategy de backward compatibility.

### Durante implementación
1. **Merge incremental**: abrir PR pequeño con `ApiHttpClient` + `ApiTaskRepository` primero.
2. **Pruebas tempranas**: tests unitarios antes de cambiar `tasker init` para evitar regresiones.
3. **Documentación paralela**: escribir docs simultáneamente a la implementación (no al final).
4. **Code review**: verificar en reviews que se respetan patrones hexagonales (puertos/adaptadores).

### Post-merge
1. **Observabilidad**: instrumentar llamadas HTTP desde CLI (opcional en MVP, recomendado en v2).
2. **Monitoreo**: agregar health-check automático en background (opcional).
3. **Feedback de usuarios**: recolectar datos sobre uso de ambos modos.
4. **Optimizaciones**: basadas en telemetría (ej: caché local, batch endpoints).

### Consideraciones futuras (v2+)
- **Caché local** de respuestas API (TTL configurable).
- **Endpoints batch** en el servidor para operaciones bulk.
- **Sincronización bidireccional** si hay desconexión temporal.
- **GraphQL** como alternativa a REST (si el backend lo soporta).
- **Observabilidad**: OpenTelemetry, Prometheus metrics.

---

## Resumen ejecutivo (para CTO/PM)

**Problema**: CLI hoy solo se conecta directo a Neo4j; impide despliegues seguros con separación de planos (control vs datos).

**Solución**: Dual-mode CLI:
- `TASKER_MODE=direct`: actual (Bolt directo).
- `TASKER_MODE=api`: nuevo (HTTP al backend).

**Beneficios**:
✅ Arquitectura limpia (puertos/adaptadores sin cambios).
✅ Escenarios de producción: usuarios con DB managed pueden usar solo API.
✅ Testing más fácil (mock HTTP vs real DB).
✅ Migración segura: Direct → API sin parar usuarios.

**Riesgos mitigados**:
- Transacciones: endpoints compuestos en servidor, idempotencia en cliente.
- Seguridad: API key no en repo, secretos en env vars.
- Compatibilidad: versionado explícito en headers.

**Esfuerzo**: MVP (2 semanas FT) → Production-ready (4-5 semanas).

**Impacto esperado**:
- Reducir time-to-market para nuevos clientes (no instalar Neo4j).
- Mejorar UX en ambientes cloud (managed DB).
- Base sólida para futuros modes (GraphQL, gRPC).

---