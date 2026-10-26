# Issue #598: Cierre de los follow-ups de la auditoría — rebuild de la imagen, verificación en vivo y commit (specs estrictos, envelope de éxito, DELETEs)

## Description

La segunda tanda de hallazgos del informe de la prueba completa de los **296 endpoints**
(2026-10-25; nomenclatura del informe: hallazgos #1–#6, no números de `.issues`) tiene el
código **terminado y con todos los gates en verde**, pero **sin desplegar ni commitear**:

- **Hallazgo #2 — specs de petición estrictos**: `SecretPutRequest.name/value` y
  `DeploymentCreateRequest.commit_sha` ahora son requeridos (`Field(..., min_length=1)`),
  `RegistrySchemaRequest.version` exige semver (`pattern=^\d+\.\d+\.\d+$`) y
  `chat.participant_ids` documenta la regla de 2 participantes (directo: caller + 1).
  Efecto: 422 temprano de Pydantic en vez de errores tardíos/500.
- **Hallazgo #3 — envelope de éxito `{data, error, meta}`**: migrados `whoami`,
  `admin/flags` (×4), `data-quality` (×5), `secrets` (×8), `registry` (×6) y
  `webhooks/subscriptions` (×3). Excluidos por decisión: `POST /webhooks/receive`
  (ingress externo con HMAC) y `GET /auth/me` (consumidor frontend — issue #601).
- **Hallazgo #5 — DELETEs faltantes**: `DELETE /data-quality/rules/{rule_id}`
  (`require_permission admin` + 404 si no existe), `DELETE /registry/schemas/{name}`,
  `DELETE /registry/datasets/{dataset_id}`, `DELETE /deployments/{id}`
  (query `DELETE_DEPLOYMENT`, `DeploymentRepositoryMixin.delete_deployment`,
  `delete_deployment` añadido al protocolo `TaskRepositoryInterface`).
- **Tests**: nuevos `tests/api/test_registry_api.py` (6) y
  `tests/api/test_api_contract_followup.py` (8: DELETE/404/403, 422 de los specs,
  envelope); actualizados `test_admin_permissions`, `test_secrets_audit_routing`,
  `test_flags_api_unit`, integrations de secrets/flags/sso, `test_api`
  (`MockRepository.delete_deployment`).

**Estado verificado (2026-10-26):**

- Gates: pytest **1690 passed / 62 skipped / 0 failed**, mypy **1053** (gate ≤1100),
  ruff **1239** (= baseline), vitest **467/467**, eslint 0 errores (2 warnings
  preexistentes), `npm run build` ✓.
- Trabajo en árbol: **20 ficheros modificados + 2 tests nuevos** sin commitear
  (`git status --short`), rama `main` 1 commit ahead de `origin/main` (`a952a3b`).
- La imagen **no contiene** estos cambios: `docker compose build tasker-api` fue
  abortado en la sesión 2026-10-26 — `tasker-api` corre el estado `a952a3b`.
- El script de verificación en vivo ya existe:
  `C:\Users\Dairon\AppData\Local\Temp\opencode\verify_followup_live.py` —
  **25 checks**: envelope ×6, 422 de specs ×3, roundtrip+404 de cada DELETE ×8,
  Neo4j 5→5, Redis restaurado (solo `rule-593-live`, sin `schema:verify*`).

Sin este cierre: los fixes viven solo en el working tree (riesgo de pérdida), la imagen
sigue sirviendo el contrato viejo y la auditoría queda sin sellar — todos los issues de
esta serie (#599–#603) se medirían contra la imagen anterior.

## Status: DONE (2026-10-26)

## Priority: HIGH

## Component
Backend / API + infra (imagen docker) + proceso de entrega

## Type
infra / quality

## Implementation

1. **Rebuild de la imagen**: `docker compose build tasker-api` y
   `docker compose up -d --remove-orphans` (patrón #555/#596); esperar `healthy`
   (`docker ps`).
2. **Verificación en vivo**: ejecutar `verify_followup_live.py` contra
   `http://127.0.0.1:8888` → **25/25 PASS**:
   - envelope `{data, meta}` en whoami / flags / data-quality/rules /
     secrets/audit / registry/datasets / webhooks/subscriptions;
   - 422 de schema: secret sin `name`, deployment sin `commit_sha`, versión
     `latest` no-semver;
   - DELETE + 404 de regla dq, schema, dataset y deployment (roundtrip completo
     con creación previa y limpieza).
3. **Higiene del entorno**: nodos Neo4j = **5**; Redis `dq:rules` solo
   `rule-593-live`; sin claves `schema:verify*`; `docker logs tasker-api` sin
   ERROR/Traceback (regex `NotImplementedError|unhandled error|500 Internal` —
   **no** buscar "500" a secas, los `request_id` los contienen).
4. **Commit** solo tras confirmación explícita del usuario (question tool):
   mensaje en **español sin tildes** referenciando `#598`, englobando
   specs + envelope + DELETEs; `git status --short` antes y staging solo de los
   ficheros de la tanda. Prohibido `git stash` en paralelo (ya causó colisión).
5. **Cierre de la issue**: sección `### Resolución` con recuentos finales
   (gates + verify) y mover el fichero a `.issues/done/` (patrón #595/#596/#597).

## Acceptance Criteria
- [x] Imagen `tasker-api` reconstruida y `healthy` con la tanda de fixes
- [x] `verify_followup_live.py` → 25/25 PASS
- [x] Neo4j 5 nodos y Redis limpio (solo `rule-593-live`) tras la verificación
- [x] `docker logs tasker-api` sin ERROR/Traceback nuevos
- [x] Commit en `main` (español sin tildes, referencia `#598`); árbol limpio
- [x] Sección `Resolución` escrita; issue movida a `.issues/done/`
- [x] Gates post-commit sin regresión (pytest 1690/62/0, mypy ≤1100, ruff 1239)

## Files to Create
- (ya existe) `C:\Users\Dairon\AppData\Local\Temp\opencode\verify_followup_live.py`
  — considerar copiarlo al repo (`tools/`) para reproducibilidad (ver #603)

## Files to Modify
- Solo esta issue y el historial git (sin cambios de código: ya están hechos)

## Related Issues
- #593/#595/#596/#597 (campaña anterior y sus patrones de verify/cierre),
  hallazgos #2/#3/#5 del informe de 296 endpoints, #599/#600/#601/#602/#603
  (lo que queda después)

## Notes
- El rebuild es **prerrequisito de #603**: el smoke debe correr contra la imagen nueva.
- Reglas de la sesión: PowerShell sin heredocs; scripts Python largos vía fichero en
  `%TEMP%\opencode`; `rg` no disponible (usar grep tool).

## Resolución (2026-10-26)

**Rebuild**: `docker compose build tasker-api` → imagen `tasker-api:local` reconstruida
(19.4s) + `docker compose up -d --remove-orphans` → contenedor recreado, `Up (healthy)`
a los 12s. Los cambios de la tanda (specs/envelope/DELETEs) salen del working tree y
entran en la imagen.

**Verificación en vivo** (`verify_followup_live.py` contra `127.0.0.1:8888`): **25/25
PASS** —
- envelope `{data, error, meta}` en whoami, admin/flags, data-quality/rules,
  secrets/audit, registry/datasets y webhooks/subscriptions (los 6 en 200 con `meta`);
- 422 de specs: secret sin `name`, deployment sin `commit_sha`, registry con versión
  `latest` (no semver) — `commit_sha` además aparece en el mensaje de error;
- roundtrip + 404 de los 4 DELETE: regla dq 200/404, schema 200/404, dataset 200/404,
  deployment 200/404 (los 4 endpoints existen y borran de verdad);
- higiene post-verify: Neo4j **5→5** nodos y 0 deployments con `deployed_by='verify'`;
  Redis `dq:rules` solo `rule-593-live`, sin `schema:verify*` ni `dataset:*verify*`.

**Logs**: 39 líneas desde el arranque del contenedor — **0**
`NotImplementedError|unhandled error|500 Internal|Traceback|ERROR`.

**Gates** (pre-flight 2026-10-26, código idéntico al desplegado): pytest **1690 passed /
62 skipped / 0 failed**, mypy **1053** (gate ≤1100), ruff **1239** (= baseline), vitest
**467/467**, eslint 0 errores (2 warnings preexistentes), `npm run build` ✓.

**Commits**:
- `230e7e8` `docs(issues): crea la serie follow-ups #598-#603 de la auditoria de 296 endpoints`
- `97a801a` `feat: specs estrictos, envelope de exito y DELETEs faltantes (#598)`
- commit de cierre de esta issue (movida a `.issues/done/`).

**Pendiente fuera de esta issue** (ya registrado): hallazgos #4 y #6 → #599/#600;
envelope de `/auth/me` → #601; cableado UI del borrado → #602; re-corrida del smoke →
#603 (que ahora ya puede medir contra la imagen nueva).
