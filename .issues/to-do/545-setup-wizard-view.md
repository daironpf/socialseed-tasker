# Issue #545: Componente `SetupWizardView.vue` (asistente de instalación paso a paso)

## Description

Crear la interfaz de usuario interactiva del Asistente de Instalación dividida en pasos visuales (*Wizard*), con credenciales de administrador, datos del proyecto raíz, selección de políticas de gobernanza existentes y creación de políticas personalizadas, culminando en la inicialización y el redireccionamiento al Dashboard.

Contexto real del repo: no existe la ruta `/setup` ni ninguna vista homónima; el patrón de vistas es `<script setup>` + Tailwind + dark mode con i18n obligatorio EN/ES; la inicialización se hace contra `POST /api/v1/setup/initialize` (#543) y, al terminar, la app debe caer en `/board` (la raíz `/` redirige a `/board`).

Origen: `notas.md` → Épica Flow de Onboarding & Setup Wizard Empresarial · Issue #4 (→ #545).

## Status: TODO

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
- [ ] El usuario puede completar el formulario usando los valores por defecto (`admin`/`admin`)
- [ ] El wizard tiene 4 pasos navegables con validación y muestra el resumen antes de enviar
- [ ] Las dos primeras políticas predefinidas vienen tildadas y la tercera no; las personalizadas se agregan/eliminan en la lista
- [ ] "Inicializar Tasker" invoca `POST /api/v1/setup/initialize`, muestra loader y redirige exitosamente al tablero (`/board`)
- [ ] La ruta `/setup` no aparece en Sidebar/MobileDrawer y no está bloqueada por login
- [ ] i18n EN+ES y gates frontend (`lint`/`test`/`build`) sin regresiones

## Files to Create
- `frontend/src/views/SetupWizardView.vue`
- `frontend/src/views/SetupWizardView.spec.ts`

## Files to Modify
- `frontend/src/router/index.ts` — ruta `/setup`
- `frontend/src/components/layout/AppHeader.vue` — título de página para `/setup`
- `frontend/src/locales/en.json` / `es.json` — sección `setup`

## Related Issues
- #543 (endpoint `initialize`), #544 (guard que exige/atrasa `/setup`), #546 (paso opcional de credenciales IA/MCP), #519 (`LoginScreen` y auth), #542 (URL que enlaza al wizard)
