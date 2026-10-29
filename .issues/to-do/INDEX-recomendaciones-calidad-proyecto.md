# INDEX — Follow-ups de la revisión general de calidad del proyecto

**Fuente:** informe de revisión general del proyecto y seguimiento de sus
recomendaciones, 2026-10-26.
**Created:** 2026-10-26
**Status:** TODO (4/8) - #604–#605 DONE 2026-10-27; #606 DONE 2026-10-28; #607 DONE 2026-10-29
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
- Corregir el contrato documentado del análisis de causa raíz (#608).
- Resolver las mutaciones de `props.issue` avisadas por ESLint (#609).
- Evitar que el bundle siga emitiendo un chunk ELK de 1.47 MB (#610).
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
| #608 | `608-corregir-documentacion-de-analisis-root-cause.md` | Documentar el contrato real del análisis de causa raíz | MEDIUM | docs / API | TODO |
| #609 | `609-eliminar-mutaciones-de-props-en-issue-detail.md` | Eliminar mutaciones de props en IssueDetailView | LOW | bug fix / frontend | TODO |
| #610 | `610-reducir-chunk-elk-frontend.md` | Reducir o diferir la carga del chunk ELK de 1.47 MB | MEDIUM | performance / frontend | TODO |
| #611 | `611-actualizar-base-datos-browserslist.md` | Actualizar caniuse-lite/Browserslist y quitar advertencia obsoleta | LOW | maintenance / frontend | TODO |

## Orden sugerido

1. **#608** — corregir el contrato documentado y mantenerlo alineado con OpenAPI.
2. **#609 y #610** — corregir los avisos frontend y volver a medir la build.
3. **#611** — actualizar los datos de compatibilidad y revisar lockfile/build.

## Release Checklist

- [x] #604: baseline Ruff vigente y cero hallazgos en `src/`
- [x] #605: baseline mypy vigente, cero errores globales y modo estricto preservado
- [x] #606: prerrequisitos documentados y job opt-in reproducible; suite live
      configurada pero pendiente de ejecución confirmatoria en Actions
- [x] #607: scanners bloqueantes sin supresión, baseline triajeado y exit codes
      verificados localmente; ejecución confirmatoria pendiente en Actions
- [ ] #608: documentación y schema OpenAPI verificados contra la implementación
- [ ] #609: ESLint sin avisos de mutación de props y pruebas del flujo actualizadas
- [ ] #610: build sin carga ELK innecesaria; tamaño medido sin elevar el umbral para
      silenciar la alerta
- [ ] #611: build sin advertencia de base Browserslist desactualizada y lockfile
      actualizado de forma reproducible
- [ ] Cada issue cerrada incluye evidencia de los comandos/gates y pasa a
      `.issues/done/` con `Status: DONE`
- [ ] Commit solo tras un “sí” explícito; mensaje en español y referencia `#NNN`
