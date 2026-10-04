# Issue #549: Notificación de bienvenida del sistema al instalar/iniciar

## Description

Conectar el flujo de instalación y primer arranque (*Setup Wizard* / post-install) con el motor de notificaciones en MongoDB para generar la primera notificación de bienvenida del administrador.

Contexto real del repo: `routers/setup.py` (#543) sanitiza el admin (`normalize_username`), lo crea en PostgreSQL (bcrypt) + nodo `:User`, crea el `:Project` y las políticas, y **wipea** Neo4j + tablas públicas de PostgreSQL + colecciones Mongo del chat + Redis antes de crear — hoy esa lista de colecciones Mongo **no incluye `notifications`**, por lo que hay que ampliarla para que cada instalación deje exactamente una bienvenida (AC). El destino es el propio `admin_user` creado en el initialize. El wizard (#545/#546) ya dispara `POST /api/v1/setup/initialize`; no requiere cambios de UI.

Origen: `notas.md` → Sistema de Notificaciones Real en MongoDB · Issue #3 (→ #549).

## Status: TODO

## Priority: MEDIUM

## Component
Backend / Onboarding / Setup

## Type
feat / integration

## Implementation
1. **Inserción post-alta:** al final del `setup_initialize` (#543), tras crear el admin, insertar la notificación vía el repo de #547 con los datos exactos de `notas.md`:
   * `type`: `WELCOME`, `severity`: `INFO`, `channel`: `system`, `user_id`: admin creado.
   * `title`: "¡Bienvenido a SocialSeed Tasker!"
   * `message`: "El sistema ha sido instalado correctamente. Te recomendamos crear tus primeros agentes de IA y registrar usuarios en la plataforma."
   * `requires_action`: `True`, `link_to`: `"/users"`.
2. **Wipe ampliado:** añadir la colección `notifications` al wipe de MongoDB del initialize (junto a las colecciones del chat) para que las reinstalaciones (`confirm_wipe=true`, guard de #546) también dejen exactamente una bienvenida.
3. **Degradación segura:** si `TASKER_MONGO_URL` no está configurado o Mongo falla, el initialize **no falla** (log + continuar), igual que el resto de operaciones Mongo del repo.
4. **Idempotencia:** decisión explícita — no duplicar la bienvenida si ya existe una `WELCOME` para ese usuario (guard por `(user_id, type)`), documentada en el código.
5. **Tests:** ampliar `test_setup_endpoints.py` (hoy 20 tests): bienvenida insertada con el payload exacto, colección limpia + 1 documento tras un segundo initialize con `confirm_wipe`, y degradación sin Mongo.

## Acceptance Criteria
- [ ] Tras completar la instalación vía `/setup`, la colección `notifications` contiene exactamente la notificación de bienvenida (payload literal de `notas.md`)
- [ ] Al iniciar sesión por primera vez con la cuenta creada, el payload de notificaciones (#548) incluye este mensaje inicial
- [ ] Una reinstalación con `confirm_wipe=true` deja exactamente 1 bienvenida (wipe incluye `notifications`)
- [ ] Mongo no configurado/caído no rompe `POST /setup/initialize`
- [ ] Gates backend sin regresiones

## Files to Create
- (ninguno nuevo)

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/setup.py` — inserción de la bienvenida + wipe de `notifications`
- `tests/api/test_setup_endpoints.py` — nuevos tests del flujo de bienvenida

## Related Issues
- #543 (initialize que engancha), #545/#546 (wizard + guard `confirm_wipe`), #547 (modelo/repo), #548 (lectura en el primer login), #551 (visualización en el NotificationCenter)
