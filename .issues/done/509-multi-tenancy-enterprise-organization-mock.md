# Issue #509: Multi-Tenancy & Enterprise Organization Management (Mock-Enabled)

## Description

Para soportar empresas grandes y clientes B2B, la UI debe permitir gestionar múltiples organizaciones, departamentos, equipos y *workspaces* aislados desde el motor de datos simulados. Cualquier empresa (startup o multinacional) debe poder desplegar la UI y evaluar la visión completa de SocialSeed Tasker con datos ultrarrealistas sin levantar Neo4j/FastAPI.

Origen: `notas.md` → Issue #501 (renumerada a #509; #501 ya está en done).

## Status: DONE

### Resolution (2026-09-24)

Implementado completo en frontend + mock-api:

- **Tipos**: `frontend/src/types/organizations.ts` (`Organization`, `Workspace`, `EnterpriseAccount`, `OrganizationQuota`, `DataRetentionPolicy`, roles `ENTERPRISE_ADMIN|SECURITY_MANAGER|DEVELOPER|AUDITOR`, planes `STARTUP|BUSINESS|ENTERPRISE`).
- **Datos multinivel**: `frontend/dataset-de-pruebas/organizations.json` con 3 organizaciones (SocialSeed Corp, Northwind Labs, Acme Startup), 6 workspaces con métricas mock, cuentas con los 4 roles, cuotas y retención.
- **API**: `frontend/src/api/organizationsApi.ts` (fetch a `/mock-api/mock/organizations`) + endpoints FastAPI en `mock-api/server.py`: `GET/POST /mock/organizations`, `GET/PATCH/DELETE /mock/organizations/{id}` (con `OrganizationCreate`/`OrganizationUpdate` y persistencia en el dataset).
- **Store**: `frontend/src/stores/organizationsStore.ts` — selección actual en `localStorage` (`currentOrg`, `currentWorkspace`, `activeEnterpriseRole`), `canEdit`/`canManage` (Auditor = solo lectura, solo Admin/Security gestionan cuentas), `quotaUsage` (compute/storage/tokens %), sincronización automática del proyecto activo (`uiStore.setProject`) al workspace seleccionado.
- **Switcher**: `frontend/src/components/layout/OrganizationSwitcher.vue` montado en `AppHeader.vue` (desktop `lg+`), dropdown jerárquico Organización → Workspace, con acceso directo a la vista de configuración.
- **Vista**: `frontend/src/views/OrganizationSettingsView.vue` en `/organization` — selector de rol activo, tarjetas de cuota con semáforo (verde/ámbar/rojo ≥70/90%), política de retención editable, CRUD de cuentas con roles, grid de workspaces; acciones deshabilitadas según rol.
- **Nav**: entrada `nav.organization` en `Sidebar.vue` y `MobileDrawer.vue`; título de header `header.organization`.
- **i18n**: secciones `organizations.*` + `nav.organization` + `header.organization` en EN y ES.
- **Build**: `npm run build` (vue-tsc + vite) pasa sin errores; `server.py` y `organizations.json` validados.

Acceptance Criteria todos cumplidos.

## Priority: CRITICAL

## Component
Frontend / Enterprise / Multi-Tenancy

## Type
feat / enterprise

## Implementation
1. **OrganizationSwitcher en el header:**
   - Crear `OrganizationSwitcher.vue` en `components/layout/` junto a `ProjectSelector`
   - Selector jerárquico: Organización → Workspace/Departamento → Proyecto
   - Persistencia en `localStorage` (`currentOrg`, `currentWorkspace`)
   - Integración con `AppHeader.vue` (visible en desktop y mobile drawer)

2. **Datos multinivel en mock:**
   - Ampliar `frontend/dataset-de-pruebas/projects.json` (o crear `organizations.json`) con estructura: Organizaciones → Departamentos → Proyectos/Workspaces
   - Cada workspace con métricas mock (miembros, issues activos, cuota usada)
   - Crear `organizationsApi.ts` + `organizationsStore.ts` (o extender `uiStore`)
   - Endpoints mock en `mock-api/server.py`: `GET/POST /mock/organizations`, workspaces

3. **Roles de cuenta empresarial:**
   - Tipos de rol: Enterprise Admin, Security Manager, Developer, Auditor
   - CRUD simulado de cuentas de empresa con roles diferenciados
   - El rol activo afecta (mock) la disponibilidad de acciones en la UI (ej. Auditor solo lectura en acciones destructivas)

4. **Cuotas y retención por organización:**
   - En vista de configuración (extender `ProfileView` o crear `OrganizationSettingsView`): límites de cómputo/tokens y políticas de retención de datos
   - Tarjetas de uso vs. límite con indicadores de riesgo

## Acceptance Criteria
- [ ] `OrganizationSwitcher` in AppHeader with org → workspace → project hierarchy
- [ ] Multilevel mock data: Organizations → Departments → Projects/Workspaces
- [ ] Create, edit, and switch between enterprise accounts with roles (Enterprise Admin, Security Manager, Developer, Auditor)
- [ ] Simulated compute/token quotas and data retention policies per organization in settings view
- [ ] Selected org/workspace persists across reloads and filters issue views when applicable
- [ ] Empty/switch states work without backend
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes (vue-tsc)

## Files to Create
- `frontend/src/components/layout/OrganizationSwitcher.vue`
- `frontend/src/stores/organizationsStore.ts`
- `frontend/src/api/organizationsApi.ts`
- `frontend/src/types/organizations.ts`
- `frontend/src/views/OrganizationSettingsView.vue` (optional if folded into Profile)
- `frontend/dataset-de-pruebas/organizations.json`

## Files to Modify
- `frontend/src/components/layout/AppHeader.vue` — mount OrganizationSwitcher
- `frontend/src/stores/uiStore.ts` — org/workspace selection state
- `frontend/src/router/index.ts` — optional route for org settings
- `frontend/src/components/layout/Sidebar.vue` / `MobileDrawer.vue` — optional nav entry
- `mock-api/server.py` — organization endpoints
- `frontend/src/locales/en.json` — organizations section
- `frontend/src/locales/es.json` — organizations section
- `features.md` — document new capability when done

## Related Issues
- #479 (Organization Project Selector), #498 (Project Selector Store Integration), #314 (Multi-Tenant Support backend), #475 (Notification Center)
