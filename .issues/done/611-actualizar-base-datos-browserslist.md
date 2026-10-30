# Issue #611: Actualizar la base de datos de Browserslist del frontend

## Description

Las ejecuciones recientes de Vitest y la build del frontend reportan que los datos de
Browserslist (`caniuse-lite`) están desactualizados aproximadamente siete meses y
sugieren actualizarlos. La build termina, pero el mensaje se repite y la información
de compatibilidad usada por las herramientas frontend deja de reflejar las versiones
actuales de browsers.

Esta issue actualiza únicamente la base correspondiente y su lockfile, evitando una
actualización indiscriminada de dependencias del frontend.

## Status: DONE — 2026-10-30

## Priority: LOW

## Component
Frontend / dependencias de desarrollo y build

## Type
maintenance / frontend

## Implementation

1. Actualizar `caniuse-lite`/Browserslist con la herramienta recomendada por npm
   (`npx update-browserslist-db@latest`) o el procedimiento vigente compatible con
   este proyecto.
2. Revisar el diff del lockfile y limitar los cambios a las dependencias transitivas
   necesarias para actualizar la base; no actualizar paquetes de runtime ajenos.
3. Ejecutar lint, Vitest y build, y confirmar que ya no aparece el aviso de datos
   Browserslist desactualizados.
4. Verificar que el lockfile siga siendo reproducible mediante `npm ci`.

## Acceptance Criteria
- [x] La versión de `caniuse-lite` queda actualizada mediante un procedimiento
      reproducible y reflejado en el lockfile.
- [x] `npm ci` termina correctamente.
- [x] ESLint, Vitest y `npm run build` pasan.
- [x] La salida de build/test deja de mostrar el warning de base Browserslist
      desactualizada.
- [x] El diff no incluye actualizaciones no relacionadas de dependencias.

## Files to Modify
- `frontend/package-lock.json` o el lockfile vigente del proyecto

## Related Issues
- Revisión de validación frontend: aviso de `caniuse-lite` desactualizado durante
  Vitest y build
- #610 (revisión del bundle y warnings de build)

## Notes
- La observación de revisión fue: “Browserslist: browsers data (caniuse-lite) is
  7 months old”.
- No elevar el warning a error ni suprimirlo para cerrar la issue.

## Resolution

- Actualizado con `npx update-browserslist-db@latest`: `caniuse-lite`
  **1.0.30001785 → 1.0.30001820** y, como dependencia transitiva necesaria de
  Browserslist, `baseline-browser-mapping` **2.10.15 → 2.11.34**. La herramienta
  reportó “No target browser changes”.
- Solo cambió `frontend/package-lock.json` (6 líneas agregadas / 6 eliminadas); no se
  modificaron `frontend/package.json` ni dependencias de runtime.
- `npm ci` reproducible: 581 paquetes instalados correctamente.
- Gates: `npm run lint` sin hallazgos; `npx vitest run` 63 archivos / 486 tests;
  `npm run build` correcto con `Bundle guard OK`.
- La salida de lint, Vitest y build ya no contiene ningún aviso de Browserslist /
  `caniuse-lite` desactualizado. El único warning restante de la build es el de los
  chunks lazy justificados de #610, ajeno a esta issue.
