# INDEX — Follow-ups de la revisión general de calidad del proyecto

**Fuente:** informe de revisión general del proyecto y seguimiento de sus
recomendaciones, 2026-10-26.
**Created:** 2026-10-26
**Status:** TODO (7/8) - #604–#605 DONE 2026-10-27; #606 DONE 2026-10-28; #607 DONE 2026-10-29; #608–#610 DONE 2026-10-30
**Numeración:** **#604–#611** (continúa tras **#603**, última issue numerada en
`.issues/done/`)

---

## Contexto

La revisión general encontró deuda estática considerable, una suite de integración
que no tiene sus servicios externos completos en el job de CI y scans de seguridad
cuyo resultado estaba suprimido. También señaló correcciones puntuales que ya se
aplicaron en el árbol de trabajo: imports/errores confirmados de CLI y prueba de
`/auth/me`, carga diferida de Mermaid, métricas del README y retirada de la supresión
de los scans.

Esta tanda registra **solo el trabajo pendiente**, sin duplicar esas correcciones
puntuales:

- Eliminar todos los hallazgos Ruff en `src/` (#604).
- Eliminar todos los errores mypy sin debilitar el perfil estricto (#605).
- Actualizar la base de datos de Browserslist que genera una advertencia en la build
  (#611).

Los conteos de la revisión son históricos; cada issue debe medir su baseline vigente
antes de fijar la reducción final.

## Issue Index

| # | Fichero | Título | Prioridad | Tipo | Status |
|---|---|---|---|---|---|
| #604 | `604-reducir-deuda-ruff-sin-cambios-masivos.md` | Eliminar hallazgos Ruff en `src/` | MEDIUM | quality / backend | DONE |
| #605 | `605-reducir-deuda-mypy-por-paquetes.md` | Eliminar errores mypy en `src/` sin debilitar strict | MEDIUM | quality / backend | DONE |
| #606 | `../done/606-hacer-reproducible-la-suite-de-integracion-en-ci.md` | Hacer reproducible la suite de integración en CI | MEDIUM | test / infra | DONE |
| #607 | `../done/607-validar-y-triar-los-scans-de-seguridad-en-ci.md` | Validar scans bloqueantes y triar su baseline | HIGH | security / quality | DONE |
| #608 | `../done/608-corregir-documentacion-de-analisis-root-cause.md` | Documentar el contrato real del análisis de causa raíz | MEDIUM | docs / API | DONE |
| #609 | `../done/609-eliminar-mutaciones-de-props-en-issue-detail.md` | Eliminar mutaciones de props en IssueDetailView | LOW | bug fix / frontend | DONE |
| #610 | `../done/610-reducir-chunk-elk-frontend.md` | Reducir o diferir la carga del chunk ELK de 1.47 MB | MEDIUM | performance / frontend | DONE |
| #611 | `611-actualizar-base-datos-browserslist.md` | Actualizar caniuse-lite/Browserslist y quitar advertencia obsoleta | LOW | maintenance / frontend | TODO |

## Orden sugerido

1. **#611** — actualizar los datos de compatibilidad y revisar lockfile/build.

## Release Checklist

- [x] #604: baseline Ruff vigente y cero hallazgos en `src/`
- [x] #605: baseline mypy vigente, cero errores globales y modo estricto preservado
- [x] #606: prerrequisitos documentados y job opt-in reproducible; suite live
      configurada pero pendiente de ejecución confirmatoria en Actions
- [x] #607: scanners bloqueantes sin supresión, baseline triajeado y exit codes
      verificados localmente; ejecución confirmatoria pendiente en Actions
- [x] #608: referencias alineadas con OpenAPI y prueba de contrato de ejemplos
- [x] #609: ESLint sin avisos de mutación de props y pruebas del flujo actualizadas
- [x] #610: ELK solo en chunk lazy verificado por manifest; inicial dividido bajo
      500 kB y excepciones lazy documentadas sin elevar el umbral
- [ ] #611: build sin advertencia de base Browserslist desactualizada y lockfile
      actualizado de forma reproducible
- [ ] Cada issue cerrada incluye evidencia de los comandos/gates y pasa a
      `.issues/done/` con `Status: DONE`
- [ ] Commit solo tras un “sí” explícito; mensaje en español y referencia `#NNN`
