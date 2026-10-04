# Issue #545: Componente `SetupWizardView.vue` (asistente de instalación paso a paso)

## Description

Crear la interfaz de usuario interactiva del Asistente de Instalación dividida en pasos visuales (*Wizard*), con credenciales de administrador, datos del proyecto raíz, selección de políticas de gobernanza existentes y creación de políticas personalizadas, culminando en la inicialización y el redireccionamiento al Dashboard.

Contexto real del repo: no existe la ruta `/setup` ni ninguna vista homónima; el patrón de vistas es `<script setup>` + Tailwind + dark mode con i18n obligatorio EN/ES; la inicialización se hace contra `POST /api/v1/setup/initialize` (#543) y, al terminar, la app debe caer en `/board` (la raíz `/` redirige a `/board`).

Origen: `notas.md` → Épica Flow de Onboarding & Setup Wizard Empresarial · Issue #4 (→ #545).

## Status: DONE (2026-10-03)

## Priority: HIGH

## Component
Frontend / UI / Onboarding

## Type
feat / ux

## Implementation
1. **Ruta `/setup`:** nueva entrada en `router/index.ts` → `SetupWizardView.vue`, fuera de los grupos del Sidebar/MobileDrawer (no aparece en la navegación) y sin badge de `pendingFeatures` (es la puerta de entrada, no una vista pendiente); título de cabecera propio.
2. **Paso 1 — Credenciales de administrador:** formulario `admin_user` (default `admin`) y `admin_password` (default `admin`) con opción visual para alternar la visibilidad de la contraseña.
3. **Paso 2 — Datos del proyecto raíz:** inputs requeridos de Nombre y Resumen del proyecto.
4. **Paso 3 — Políticas de gobernanza e IA:**
   * Checkboxes predefinidos: `[x]` Prevenir dependencias circulares en el grafo, `[x]` Exigir resumen de solución y archivos afectados antes de cerrar un issue, `[ ]` Aprobación humana obligatoria para modificaciones en el Core.
   * Lista dinámica de políticas personalizadas: input de texto + botón "Agregar Política" que inserta reglas en un array (eliminar también).
5. **Paso 4 — Confirmación y envío:** resumen de la configuración + botón "Inicializar Tasker" → `POST /api/v1/setup/initialize`, loader animado durante la petición, manejo de errores (403/500 con toast) y redirección al Dashboard principal (`/board`).
6. **UX:** navegación Atrás/Siguiente con validación por paso, indicador de pasos, respeta dark mode y diseño responsive (mismo lenguaje visual que `LoginScreen`/modales existentes).
7. **i18n:** sección `setup` completa EN + ES (ASCII en ES).
8. **Tests:** spec vitest de la vista (montaje con Pinia + i18n, flujo por pasos con defaults, envío y redirección).

## Acceptance Criteria
- [x] El usuario puede completar el formulario usando los valores por defecto (`admin`/`admin`)
- [x] El wizard tiene 4 pasos navegables con validación y muestra el resumen antes de enviar
- [x] Las dos primeras políticas predefinidas vienen tildadas y la tercera no; las personalizadas se agregan/eliminan en la lista
- [x] "Inicializar Tasker" invoca `POST /api/v1/setup/initialize`, muestra loader y redirige exitosamente al tablero (`/board`)
- [x] La ruta `/setup` no aparece en Sidebar/MobileDrawer y no está bloqueada por login
- [x] i18n EN+ES y gates frontend (`lint`/`test`/`build`) sin regresiones

## Verification (2026-10-03)
- **Unit (vitest):** `SetupWizardView.spec.ts` → 5 tests: flujo completo con defaults + payload exacto del POST + flip `isInstalled` + `push('/board')`; add/remove de políticas personalizadas; validación por paso (Next deshabilitado con campos vacíos); error 403 → toast + redirect; error 500 → toast y el wizard permanece. `App.spec.ts` → 1 test: en `/setup` no se montan `Sidebar`/`AppHeader`/`MobileDrawer`/`TeamTicker`/`FloatingChat`/`CommandPalette`/`KeyboardShortcutsHelp`/`LoginScreen` (ni `header`/`aside`/`.animate-marquee` en el DOM) y sí `RouterView` + `ToastContainer`. `npm test` → **248 passed / 33 ficheros** (242 baseline + 6 nuevos); `npm run lint` → **0 errores** (2 warnings preexistentes en `IssueDetailView.vue`); `npm run build` → verde.
- **Shell limpio (revisión del usuario):** `App.vue` ahora bifurca con `isSetupRoute` — la rama `/setup` monta solo el `<main>` con el wizard (código y DOM, no CSS oculto); la entrada `'/setup'` que se había añadido al mapa de títulos de `AppHeader.vue` se retiró (neto nulo, no aparece en el diff). El `<main>` de setup es `flex flex-1 flex-col` y la raíz de la vista tiene `flex-1`, de modo que la card queda centrada horizontal y verticalmente en toda la ventana.
- **Smoke live (Playwright, board en `:19001`, stack fresco):** `/` → redirect `/setup` → `aside:0`, `header:0`, `.animate-marquee:0` → card centrada (desviación <8px en X e Y con viewport 1280×720) → wizard completo con defaults + política custom → `POST /setup/initialize` **200** → URL `/board` con `header`/`aside`/`.animate-marquee` visibles y `setup-steps` ausente → `GET /setup/status` `installed:true`. 1/1.
- **Reset post-smoke:** proyecto `Review545`, sus 3 políticas y `:User admin` `DETACH DELETE`; fila PG `admin` eliminada; `GET /setup/status` → `{"installed": false, "needSetup": true}`; ficheros temporales de Playwright borrados.
- **Nota:** la ruta se registró en #544; esta issue reemplaza el placeholder `SetupWizardView.vue`, añade `postSetupInitialize()` (con `suppressErrorToast` + manejo manual 403/500 vía i18n), el título de cabecera en `AppHeader.vue` y amplía la sección `setup` del i18n.

## Files to Create
- `frontend/src/views/SetupWizardView.vue`
- `frontend/src/views/SetupWizardView.spec.ts`

## Files to Modify
- `frontend/src/router/index.ts` — ruta `/setup`
- `frontend/src/components/layout/AppHeader.vue` — la entrada `'/setup'` del mapa de títulos se añadió y luego se retiró (neto nulo: el header ya no se monta en `/setup`)
- `frontend/src/locales/en.json` / `es.json` — sección `setup`
- `frontend/src/App.vue` — `isSetupRoute`: en `/setup` solo se renderiza el shell del wizard (sin `Sidebar`, `AppHeader`, `MobileDrawer`, `TeamTicker`, `CommandPalette`, `KeyboardShortcutsHelp`, `FloatingChat` ni `LoginScreen`; `ToastContainer` siempre)
- `frontend/src/App.spec.ts` — test del shell limpio en `/setup`

## Related Issues
- #543 (endpoint `initialize`), #544 (guard que exige/atrasa `/setup`), #546 (paso opcional de credenciales IA/MCP), #519 (`LoginScreen` y auth), #542 (URL que enlaza al wizard)
