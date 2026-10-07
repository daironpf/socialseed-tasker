# Issue #557: Login en vista limpia (sin el proyecto visible detrás)

## Description

Reportado por el usuario tras #554/#556: al entrar sin sesión, el LoginScreen aparece como
**ventana flotante** (`fixed inset-0 z-50 bg-black/50`) pero **detrás se ve todo el proyecto**
montado (sidebar, header y el board con sus datos). No es así:

- Sin sesión → debe mostrarse **solo** el login, en una vista totalmente limpia.
- Si el inicio es satisfactorio → entonces pasas al board.

Diagnóstico:

1. `App.vue` renderizaba `<LoginScreen v-if="showLogin">` **encima** del shell completo — era un
   overlay modal, no una pantalla.
2. El guard de rutas (`router/index.ts`) no redirige a los no autenticados: `rolesAllowed(undefined)
   → true` deja navegar a `/board`, así que el `RouterView` monta el board (y pide datos en
   background) mientras el login tapa solo el centro de la pantalla.

## Status: DONE (2026-10-06)

## Priority: HIGH

## Component
Frontend (App shell + LoginScreen)

## Type
UX / bug fix

## Implementation
1. **`frontend/src/App.vue`** — el login ahora se renderiza **en lugar del** shell:
   `LoginScreen v-if="showLogin"` → `v-else` con Sidebar, header, `RouterView`, drawer, ticker,
   palette y chat. Sin sesión: la raíz queda limpia y **el `RouterView` no se monta** (bonus: sin
   peticiones ni sockets en background). Con sesión — o cuando `auth:unauthorized` cierra la
   sesión — el shell aparece tal cual como hasta ahora. La rama `/setup` (wizard bare) no cambia.
2. **`frontend/src/components/auth/LoginScreen.vue`** — backdrop sólido
   `bg-white dark:bg-gray-900` en vez de `bg-black/50`: ya no tapa nada, así que la vista queda
   totalmente limpia (respetando el dark mode).
3. El flujo posterior no cambia: `onLoggedIn` → `window.location.reload()` →
   `initSession` restaura la sesión → el shell con la ruta actual (el board) se pinta.

## Acceptance Criteria
- [x] Navegando sin sesión a `/board`: solo se renderiza `LoginScreen`; Sidebar, header,
      `RouterView` y los widgets (drawer/ticker/palette/chat) **no** existen en el DOM
- [x] Backdrop del login sólido (blanco/gris-900 según tema), sin transparencia ni contenido detrás
- [x] Con sesión (modo mock demo o sesión real restaurada): shell completo, sin LoginScreen
- [x] `/setup` intacto (wizard bare, sin login ni shell) y `ToastContainer`/skip-link presentes
      siempre
- [x] Gates: `npm run lint` 0 errors/2 warnings, `npm test` **306 passed (44 files)** (+2 tests),
      `npm run build` OK; sin cambios de backend ni i18n

## Files to Create
- `.issues/done/557-login-vista-limpia.md` — este fichero

## Files to Modify
- `frontend/src/App.vue` — login en lugar del shell (v-if/v-else)
- `frontend/src/components/auth/LoginScreen.vue` — backdrop sólido
- `frontend/src/App.spec.ts` — ruta mockeable + 2 tests nuevos (sin/con sesión en /board)
- `features.md` — filas §64 y tablas de referencia
- `.issues/to-do/INDEX-notas-v6-notifications-mongodb.md` — fila + follow-up #557

## Notes
- **Arquitectura de overlay conservada**: sigue siendo `showLogin = !isAuthenticated` dentro de
  App (no hay ruta `/login`); lo que cambia es que el shell no se pinta mientras `showLogin`.
  Si la sesión expira en caliente (`auth:unauthorized`), el shell se desmonta y el login ocupa la
  vista — misma UX que al entrar.
- El skip-link (`a[href="#main-content"]`) apunta a un `#main-content` que no existe mientras se
  muestra el login; es `sr-only` y solo aparece al hacer focus — se dejó tal cual (menor).
- Patrón de test: `let currentPath` mutable dentro del factory de `vi.mock('vue-router', …)`
  (el factory solo cierra sobre la variable; el acceso ocurre en el mount, ya inicializada) y
  `setApiMode('real'|'mock')` de `@/api/client` para forzar `isAuthenticated` sin tocar el store.

## Related Issues
- #554 (LoginScreen credentials), #552 (login obligatorio tras wizard), #519 (auth/RBAC original),
  #155/#162 (overlay de login histórico)
