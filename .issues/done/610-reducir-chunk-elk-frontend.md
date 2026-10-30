# Issue #610: Reducir o diferir la carga del chunk ELK del frontend

## Description

La build de producción de frontend termina correctamente, pero continúa mostrando la
advertencia de chunks mayores a 500 kB. Tras convertir Mermaid a carga dinámica, el
build todavía emite `elk-*.js` de **1,471.33 kB minificados (451.17 kB gzip)**. Por
tanto, la recomendación de mejorar el code-splitting queda parcialmente atendida:
Mermaid ya se importa bajo demanda, pero la dependencia ELK sigue siendo un chunk muy
grande.

El objetivo es identificar qué vista/feature trae ELK, impedir que se descargue cuando
el usuario no usa esa funcionalidad y evaluar una partición o sustitución segura si el
chunk sigue superando el umbral. No se debe limitar a elevar `chunkSizeWarningLimit`
para silenciar la advertencia.

## Status: DONE — 2026-10-30

## Priority: MEDIUM

## Component
Frontend / rendimiento y bundling

## Type
performance / frontend

## Implementation

1. Trazar en el bundle graph y en los imports la cadena que incluye ELK; identificar
   si se usa por Mermaid, vis-network u otra dependencia, y qué rutas/componentes la
   activan.
2. Verificar con build/analyzer y pruebas que las rutas que no requieren esa capacidad
   no descargan el chunk ELK durante el arranque.
3. Si la carga ya es condicional, reducir el impacto mediante división más granular,
   configuración de chunks compatible con Vite/Rollup o una alternativa de layout
   más liviana, preservando el comportamiento de diagramas/grafos.
4. Medir bundle inicial, chunk ELK y gzip antes/después; conservar el umbral de
   advertencia vigente y documentar cualquier chunk grande que sea inevitable con su
   motivo.

## Acceptance Criteria
- [x] La ruta de arranque y vistas sin diagramas/grafo no importan ELK hasta que la
      funcionalidad correspondiente se utiliza.
- [x] La descarga de chunks se verifica en build/análisis de bundle, no solo por
      inspección de imports.
- [x] La funcionalidad de grafos/diagramas sigue funcionando y sus pruebas pasan.
- [x] El bundle inicial no incorpora ELK y no hay chunks >500 kB minificados sin una
      excepción técnica justificada; no se aumenta el límite para ocultar el warning.
- [x] La resolución registra medidas de build (minificado y gzip) antes y después.

## Files to Modify
- `frontend/src/` — imports/componentes que cargan la dependencia identificada
- `frontend/vite.config.ts` — solo si se requiere una partición de chunks validada
- Pruebas frontend de las vistas/diagramas que usan el layout

## Related Issues
- Revisión general del proyecto: warning de chunk grande y chunk ELK de ~1.47 MB
- Lazy-load de Mermaid aplicado en `MarkdownRenderer.vue` como cambio previo del árbol

## Notes
- Build actual observado: `elk-*.js` **1,471.33 kB** minificado y **451.17 kB** gzip;
  Vite avisa para chunks mayores de 500 kB.
- Mermaid lazy-loading reduce la carga estática, pero no elimina el chunk ELK ni su
  advertencia de tamaño.

## Resolution

- Cadena verificada en el manifest de Vite: `index.html` → rutas lazy →
  `MarkdownRenderer` → `import('mermaid')` → `mermaid.core` → `import(elk-*.mjs)`.
  ELK es un `isDynamicEntry` y no aparece en el grafo de imports estáticos del entry.
- Se evaluó mover el motor ELK a un worker (`elk-api` + `elk-worker.min.js?url`): el
  build bajaba el chunk a ~34 kB, pero Mermaid pasa funciones no clonables al grafo y
  el worker real falla con `DataCloneError`. Se descartó para no romper los layouts
  ELK; se mantiene el bundle oficial de elkjs dentro de su chunk lazy.
- `vite.config.ts`: el entry inicial se dividió en `vendor-vue` (Vue/Pinia/Router/
  i18n) y `vendor-realtime` (axios/socket.io), y se activó `build.manifest` para el
  análisis. Los chunks lazy de Mermaid/ELK/vis-network conservan su división natural.
- Nuevo `frontend/scripts/check-bundle.mjs` (ejecutado por `postbuild`): falla si ELK
  entra en el grafo estático, si un chunk inicial supera 500 kB o si aparece un chunk
  lazy grande sin justificación. Las excepciones permitidas se imprimen con su motivo.
- `chunkSizeWarningLimit` no se modificó. El aviso de Vite sigue apareciendo solo para
  chunks lazy documentados: ELK (layout opcional de Mermaid), `mermaid.core` y
  `cynefin` (diagramas bajo demanda) y `GraphView` (vis-network de la ruta de grafo).
- Medidas (minificado / gzip):
  - Antes: entry `index` **572.15 / 186.18 kB**; ELK **1,471.33 / 451.17 kB**;
    `mermaid.core` 652.62 / 155.84 kB; `cynefin` 690.86 / 155.11 kB; `GraphView`
    709.70 / 169.96 kB.
  - Después: inicial en 3 chunks — `index` **328.4 / 98.1 kB**, `vendor-vue`
    **164.9 / 60.8 kB**, `vendor-realtime` **79.0 / 27.4 kB** (total 572.3 / 186.3 kB,
    ninguno >500 kB); ELK **1,471.4 / 451.2 kB** (lazy, sin cambios de tamaño);
    `mermaid.core` 652.9 / 155.9 kB; `cynefin` 690.9 / 155.1 kB; `GraphView`
    709.8 / 170.0 kB (todas lazy).
- Evidencia: `npm run build` correcto con `Bundle guard OK`; `npm run lint` sin
  salida; `npx vitest run` 63 archivos / 486 tests.
