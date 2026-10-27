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

## Status: TODO

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
- [ ] La ruta de arranque y vistas sin diagramas/grafo no importan ELK hasta que la
      funcionalidad correspondiente se utiliza.
- [ ] La descarga de chunks se verifica en build/análisis de bundle, no solo por
      inspección de imports.
- [ ] La funcionalidad de grafos/diagramas sigue funcionando y sus pruebas pasan.
- [ ] El bundle inicial no incorpora ELK y no hay chunks >500 kB minificados sin una
      excepción técnica justificada; no se aumenta el límite para ocultar el warning.
- [ ] La resolución registra medidas de build (minificado y gzip) antes y después.

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
