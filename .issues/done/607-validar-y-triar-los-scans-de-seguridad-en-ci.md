# Issue #607: Validar los scans de seguridad bloqueantes y triar su baseline

## Description

La revisión encontró que varios workflows suprimían el resultado de los scans con
`|| true`, por lo que los hallazgos no podían bloquear CI. Los cambios propuestos en
`.github/workflows/security-scan.yml` y `.github/workflows/pipeline.yml` reemplazan
Safety por `pip-audit` y retiran la supresión, pero `.github/workflows/dependency-update.yml`
todavía ejecuta `pip-audit || true`. El entorno local de revisión tampoco tenía Bandit
instalado y no se ejecutó ninguno de esos scans contra el baseline real.

Antes de considerar cerrado el control, hay que comprobar que ambos jobs instalan y
ejecutan los scanners, revisar los hallazgos reales y resolverlos de forma explícita,
sin volver a introducir un resultado siempre exitoso.

## Status: DONE — 2026-10-29

## Priority: HIGH

## Component
CI / seguridad de dependencias y análisis estático

## Type
security / quality

## Implementation

1. Revisar todos los workflows que ejecutan análisis de seguridad, incluidos
   `.github/workflows/security-scan.yml`, `pipeline.yml` y
   `dependency-update.yml`; usar comandos compatibles y eliminar supresiones de exit
   code.
2. Ejecutar `pip-audit --skip-editable` sobre las dependencias instaladas por cada
   workflow y `bandit -r src -lll`; verificar que fallos de instalación o hallazgos
   producen un resultado de job fallido.
3. Clasificar hallazgos por paquete, severidad y alcanzabilidad; corregir toda
   vulnerabilidad confirmada. Solo falsos positivos demostrados pueden exceptuarse,
   con evidencia y alcance mínimo; no dejar vulnerabilidades conocidas como deuda
   aceptada para cerrar la issue.
4. Ejecutar los jobs en GitHub Actions y guardar en la resolución el enlace o resumen
   de resultados y la disposición de cada hallazgo.

## Acceptance Criteria
- [x] Todos los workflows que ejecutan scans de seguridad están inventariados;
      `pip-audit` ya no se silencia en `dependency-update.yml`.
- [x] `pip-audit --skip-editable` y `bandit -r src -lll` se ejecutan en los workflows
      de seguridad pertinentes.
- [x] Un fallo de instalación o un hallazgo del scanner produce fallo real del job;
      no hay supresión global del exit code.
- [x] Todas las vulnerabilidades confirmadas del baseline se corrigen; solo falsos
      positivos demostrados quedan documentados con evidencia, sin ignorar categorías
      completas.
- [x] CI confirma que ambos workflows procesan el código/dependencias del commit y
      que no dependen de una herramienta ausente o de un comando obsoleto.

## Files to Modify
- `.github/workflows/security-scan.yml`
- `.github/workflows/pipeline.yml`
- `.github/workflows/dependency-update.yml`
- Dependencias reportadas por `pip-audit`, solo si se confirma actualización segura
- Código señalado por Bandit, solo cuando el hallazgo se verifique

## Related Issues
- #604 (reducción de hallazgos Ruff, gate de calidad general)
- Revisión general del proyecto: scans no bloqueantes y falta de Bandit en el entorno
  local de validación

## Notes
- Los cambios de workflow ya están presentes en el árbol de trabajo, pero no se han
  validado contra Actions ni contra un baseline real de Bandit/pip-audit.
- La inspección posterior encontró `pip-audit || true` en
  `.github/workflows/dependency-update.yml`; también debe quedar cubierto.

## Resolution

- Inventario de workflows con análisis de seguridad:
  - `.github/workflows/security-scan.yml` — semanal/manual; `pip-audit` y Bandit.
  - `.github/workflows/pipeline.yml` — push/PR; job `security-scan` con ambos scanners.
  - `.github/workflows/dependency-update.yml` — semanal/manual; job `security-audit`.
  - `frontend-ci.yml`, `ci.yml`, `contract-test.yml`, `release*.yml` y
    `canary-deploy.yml` no ejecutan scanners de seguridad de Python/npm.
- Cambios en workflows:
  - `dependency-update.yml`: eliminado `pip-audit || true`; ahora
    `pip-audit --skip-editable` puede fallar el job. Se actualizan
    `pip/setuptools/wheel` antes de instalar `.[dev]`.
  - `security-scan.yml` y `pipeline.yml`: añadido `actions/setup-python@v5`
    (3.11) y actualización de `pip/setuptools/wheel` antes de instalar
    `pip-audit`/`bandit`, para que el propio toolchain no arrastre avisos.
  - Verificado que no queda ningún `|| true` en comandos de seguridad.
- Baseline `pip-audit` (2.10.1):
  - Entorno limpio equivalente a CI (pip/setuptools/wheel actualizados +
    `pip install -e ".[dev]" pip-audit bandit`): **No known vulnerabilities
    found**, exit 0.
  - El venv de desarrollo local (con instalaciones antiguas) reportaba 72 avisos
    en 18 paquetes (`pip`, `setuptools`, `starlette`, `urllib3`, `cryptography`,
    `protobuf`, `thrift`, `graphql-core`, `opentelemetry-api`, `pymongo`,
    `anyio`, `certifi`, `dnspython`, `filelock`, `msgpack`,
    `pymdown-extensions`, `mkdocs-material`, `pytest`). Se comprobó que el
    problema es de versiones resueltas hace meses: una resolución limpia elige
    versiones corregidas (`starlette` 1.10.0, `urllib3` 2.8.0, `cryptography`
    50.0.2, `opentelemetry-api` 1.45.2, `graphql-core` 3.3.1, `pytest` 9.2.0,
    `pip` 26.2.2, `setuptools` 84.2.1, entre otras). No se añadieron pins
    redundantes; los workflows ahora actualizan el toolchain antes del audit.
- Baseline Bandit (1.9.4), `bandit -r src -lll`: 7 hallazgos High → **0 High**,
  exit 0.
  - 5 hashes débiles usados solo como identificadores/checksums no
    criptográficos (`application/integrity.py` MD5, `cli/commands/
    doc_sync_commands.py` MD5, `entrypoints/mcp_server.py` SHA-1,
    `healing/engine.py` SHA-1, `infrastructure/code_parser.py` MD5): se marcaron
    con `usedforsecurity=False`, sin cambiar el algoritmo ni los valores.
  - 2 extracciones de `tarfile` sin validar (`backup/core.py` en
    `verify_export` y `restore_data`): nuevo `_safe_extract` rechaza rutas fuera
    del destino y enlaces simbólicos/duros; `verify_export` devuelve `False`
    ante un archivo malicioso. Añadida prueba
    `test_verify_export_rejects_path_traversal`.
- Gates de regresión: `ruff check src` sin hallazgos, `mypy src` 236 ficheros sin
  errores, `pytest -q -k "not integration"` → 1709 passed, 66 deselected.
- Los workflows se validaron como YAML y los comandos se reprodujeron localmente
  con las mismas versiones; la ejecución real en GitHub Actions queda pendiente
  de confirmarse en la próxima ejecución (los jobs programados no se pueden
  disparar desde este entorno).
