# Issue #609: Eliminar mutaciones de `props.issue` en `IssueDetailView`

## Description

La revisión de frontend encontró dos advertencias ESLint en
`frontend/src/views/IssueDetailView.vue`:

- `onGithubSyncUpdated` aplica `Object.assign(props.issue, issue)`.
- `refreshIssueFromServer` aplica `Object.assign(props.issue, fresh)`.

Ambas mutan una prop recibida del padre y violan `vue/no-mutating-props`. Aunque
ESLint no reporta errores y el build actual pasa, la vista no debe cambiar
silenciosamente el objeto de entrada para reflejar eventos de sincronización.

## Status: DONE — 2026-10-30

## Priority: LOW

## Component
Frontend / vista de detalle de issue

## Type
bug fix / frontend

## Implementation

1. Revisar el estado de `IssueDetailView` y su padre para elegir un flujo unidireccional:
   actualizar un estado local derivado o emitir al padre una solicitud de actualización
   para refrescar el issue desde su store.
2. Mantener el comportamiento de `connectGithubSyncStream`: al recibir el evento,
   actualizar el issue visible con los datos frescos sin mutar directamente la prop.
3. Auditar el cierre del stream y los cambios de `issue.id` para evitar actualizaciones
   sobre una vista que ya representa otro issue.
4. Añadir o ampliar pruebas para la actualización por evento y la respuesta fresca del
   API, y ejecutar ESLint, pruebas enfocadas y build.

## Acceptance Criteria
- [x] `IssueDetailView.vue` no muta `props.issue` ni ningún objeto prop anidado.
- [x] Un evento SSE de sincronización refleja datos recientes en la vista.
- [x] Cambiar el issue activo cierra la suscripción anterior y evita aplicar su
      respuesta tardía al issue nuevo.
- [x] ESLint termina sin advertencias `vue/no-mutating-props` para esta vista.
- [x] Las pruebas enfocadas y `npm run build` pasan.

## Files to Modify
- `frontend/src/views/IssueDetailView.vue`
- Vista padre/store que controla el issue, si se requiere emitir/actualizar el estado
- Spec(s) de `IssueDetailView` o de la integración de GitHub Sync

## Related Issues
- Informe general del proyecto: 2 advertencias ESLint restantes
- #603 (smoke API reproducible; sin dependencia funcional)

## Notes
- Las dos ubicaciones detectadas en la revisión eran aproximadamente las líneas 629 y
  649; volver a localizar las advertencias antes de editar porque el archivo puede
  haber cambiado.

## Resolution

- `IssueDetailView` mantiene una copia local (`syncedIssue`) y expone un computed
  `issue` que prefiere el dato sincronizado cuando pertenece al issue activo y su
  `updated_at` no es anterior al prop. Ningún flujo hace `Object.assign` sobre
  `props.issue`.
- Ambos caminos (`sync:updated` de `GitHubSyncCard` y refresco por evento SSE `sync`)
  pasan por `applySyncedIssue`, que valida el `id` esperado antes de actualizar.
- `issuesStore.updateIssueFromSync` reemplaza el issue en el store cuando ya existe,
  de modo que las vistas que derivan el seleccionado del store también ven el dato
  fresco; GraphView (que usa un ref local) lo ve mediante el computed de la vista.
- Al cambiar `props.issue.id` se limpia la copia local, se cierra el stream anterior
  y se abre el del nuevo issue. El refresco captura el `id` de origen y descarta
  respuestas tardías de otro issue.
- Pruebas nuevas en `frontend/src/views/IssueDetailView.spec.ts`: evento
  `sync:updated` sin mutar el prop, refresco por SSE y cambio de issue con respuesta
  tardía ignorada.
- Evidencia: `npm run lint` sin salida (0 warnings), `npx vitest run` 63 archivos /
  486 tests, `npm run build` correcto (persiste el aviso de chunk ELK de #610).
