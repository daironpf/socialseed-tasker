# Issue #553: Detalle inline de notificaciones al hacer clic

## Description

Al hacer clic en una notificación no se mostraban sus detalles: el mensaje completo nunca se podía leer.

Diagnóstico (3 constataciones):

1. **No existe vista de detalle en ningún sitio.** `NotificationItem` (panel de la campana) muestra `title` + `message` con `truncate` a 1 línea; el clic solo marcaba como leída y hacía `router.push(linkTo)` — para el par de onboarding (#552) saltaba a `/users` sin enseñar el texto, y si ya estabas en `/users` "no pasaba nada" visible.
2. **El feed del board ni siquiera tenía clic.** `NotificationsFeed.vue` renderiza las 4 últimas notificaciones en `<li>` sin handler alguno → el clic era mudo.
3. **Solo HITL tenía modal** (`HITLQuickActionModal`, aprobación) — no es un detalle de mensaje.

Decisión de producto: **opción B** — expansión inline del mensaje al hacer clic (sin modal), en panel Y feed.

Origen: reporte del usuario tras probar el flujo de onboarding #552.

## Status: DONE (2026-10-06)

## Priority: MEDIUM

## Component
Frontend / Notification Center + Dashboard Feed

## Type
feat / UX (detalle de notificaciones)

## Implementation
1. **`NotificationItem.vue`:** props `expanded?: boolean` + emit `toggle`. `handleClick`: si `hitlRequestId` → marca leída y abre `HITLQuickActionModal` (comportamiento intacto, `return`); si no → `emit('toggle')` y `markRead` si estaba sin leer — **ya no navega solo**. El `<p>` del mensaje usa clase condicional: colapsado `truncate`, expandido `whitespace-pre-wrap break-words`. Bloque expandido (`v-if="expanded"`) con `fullDate` (`toLocaleString()`) + botón **Open/Abrir** (`notifItem.open`) si hay `linkTo`, con `@click.stop` → `router?.push(linkTo)`. `aria-expanded` en la raíz.
2. **`NotificationCenter.vue`:** `expandedId = ref<string|null>` — clic en el mismo id colapsa, en otro lo expande (**una sola fila abierta**); se resetea al cerrar el panel (`watch(open)`) y al hacer dismiss de la fila expandida; se pasa `:expanded`/`@toggle` al item.
3. **`NotificationsFeed.vue`:** filas con `cursor-pointer` + `@click="toggle(n)"` (primer handler de clic del feed) → alterna `expandedId` propio y `notificationsStore.markAsRead(n.id)`; mensaje con las mismas clases condicionales; bloque expandido con fecha completa + botón "Abrir" (`@click.stop="openLink(n)"` vía `useRouter`).
4. **i18n:** nueva clave raíz `notifItem.open` = `Abrir`(es) / `Open`(en), insertada junto a `notifPanel`.

## Acceptance Criteria
- [x] Clic en fila no-HITL del panel alterna la expansión: mensaje completo con wrap, sin `truncate`
- [x] Expandir marca la notificación como leída (store + `PATCH .../read` en modo real vía `markAsRead`)
- [x] El clic **no navega solo**: la navegación a `linkTo` es el botón "Abrir" del bloque expandido
- [x] Solo una fila expandida a la vez en el panel; colapsa al cerrar el panel o al dismiss
- [x] Clic en HITL sigue abriendo `HITLQuickActionModal` sin expandir
- [x] El feed del board expande al clic, marca leída y ofrece "Abrir"; colapsa al segundo clic
- [x] Gates: `npm run lint` 0 errors/2 warnings preexistentes, `npm test` **296 passed (42 files)** (baseline 291/41, +5 tests/+1 spec), `npm run build` OK (vue-tsc limpio), i18n EN/ES **1684/1684**
- [x] Sin cambios de backend

## Files to Create
- `frontend/src/components/dashboard/NotificationsFeed.spec.ts` — 2 tests del feed (expand+read+open, single/collapse)

## Files to Modify
- `frontend/src/components/ui/NotificationItem.vue` — expanded/toggle/mensaje condicional/botón Abrir
- `frontend/src/components/ui/NotificationCenter.vue` — `expandedId` único + reset al cerrar/dismiss
- `frontend/src/components/ui/NotificationCenter.spec.ts` — de 1 a 4 tests (expand/collapse sin navegar, single-expanded, HITL intacto)
- `frontend/src/components/dashboard/NotificationsFeed.vue` — clic + expansión + Abrir
- `frontend/src/locales/es.json` / `en.json` — `notifItem.open`
- `features.md` — §57
- `.issues/to-do/INDEX-notas-v6-notifications-mongodb.md` — fila + follow-up #553

## Notes
- **Por qué no modal:** elegido explícitamente (opción B del plan) — el texto queda en contexto y no interrumpe con un overlay; el modal de HITL se conserva porque su contenido es una decisión de aprobación, no un mensaje.
- **Locales de test:** la suite corre con locale `en` por defecto (`localStorage.locale` vacío) → los specs esperan `Open`, no `Abrir`.
- **`truncate` es solo visual:** las aserciones de expansión verifican clases (`whitespace-pre-wrap`/`truncate`) y `aria-expanded`, no la ausencia del texto (que sigue en el DOM colapsado).
- **Sin auto-navegación:** para las notificaciones de onboarding #552 la ruta `/users` se alcanza con el botón "Abrir" del detalle.
- **Locales JSON intactos:** la primera pasada de edición con PowerShell rompió UTF-8/BOM (mojibake) y se revirtió con `git checkout`; la edición final fue con el editor nativo (+3 líneas por fichero).

## Related Issues
- #551 (store real), #552 (par de onboarding cuyo clic motivó el reporte), #516 (panel de notificaciones original), #545 (patrón de modal/`linkTo`)
