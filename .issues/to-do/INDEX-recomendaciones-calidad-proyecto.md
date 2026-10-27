# INDEX — Follow-ups de la revisión general de calidad del proyecto

**Fuente:** informe de revisión general del proyecto y seguimiento de sus
recomendaciones, 2026-10-26.
**Created:** 2026-10-26
**Status:** TODO (1/8) - #604 DONE 2026-10-27
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
- Hacer reproducibles los grupos de pruebas de integración y sus servicios (#606).
- Ejecutar los nuevos scans bloqueantes y triar sus hallazgos reales (#607).
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
| #605 | `605-reducir-deuda-mypy-por-paquetes.md` | Eliminar errores mypy en `src/` sin debilitar strict | MEDIUM | quality / backend | TODO |
| #606 | `606-hacer-reproducible-la-suite-de-integracion-en-ci.md` | Hacer reproducible la suite de integración en CI | MEDIUM | test / infra | TODO |
| #607 | `607-validar-y-triar-los-scans-de-seguridad-en-ci.md` | Validar scans bloqueantes y triar su baseline | HIGH | security / quality | TODO |
| #608 | `608-corregir-documentacion-de-analisis-root-cause.md` | Documentar el contrato real del análisis de causa raíz | MEDIUM | docs / API | TODO |
| #609 | `609-eliminar-mutaciones-de-props-en-issue-detail.md` | Eliminar mutaciones de props en IssueDetailView | LOW | bug fix / frontend | TODO |
| #610 | `610-reducir-chunk-elk-frontend.md` | Reducir o diferir la carga del chunk ELK de 1.47 MB | MEDIUM | performance / frontend | TODO |
| #611 | `611-actualizar-base-datos-browserslist.md` | Actualizar caniuse-lite/Browserslist y quitar advertencia obsoleta | LOW | maintenance / frontend | TODO |

## Orden sugerido

1. **#607** — comprobar los controles de seguridad ya modificados y conocer el
   baseline real antes de tomar decisiones sobre hallazgos.
2. **#604 y #605** — eliminar completamente la deuda estática por lotes independientes,
   manteniendo activos los gates.
3. **#608** — corregir el contrato documentado y mantenerlo alineado con OpenAPI.
4. **#609 y #610** — corregir los avisos frontend y volver a medir la build.
5. **#606** — definir grupos y servicios reproducibles y pasar la suite completa antes
   de ampliar el gate de integración.
6. **#611** — actualizar los datos de compatibilidad y revisar lockfile/build.

## Release Checklist

- [x] #604: baseline Ruff vigente y cero hallazgos en `src/`
- [ ] #605: baseline mypy vigente, cero errores globales y modo estricto preservado
- [ ] #606: prerrequisitos documentados y jobs opt-in de integración reproducibles
- [ ] #607: ambos scanners validados en Actions, hallazgos triajeados y exit codes
      efectivos
- [ ] #608: documentación y schema OpenAPI verificados contra la implementación
- [ ] #609: ESLint sin avisos de mutación de props y pruebas del flujo actualizadas
- [ ] #610: build sin carga ELK innecesaria; tamaño medido sin elevar el umbral para
      silenciar la alerta
- [ ] #611: build sin advertencia de base Browserslist desactualizada y lockfile
      actualizado de forma reproducible
- [ ] Cada issue cerrada incluye evidencia de los comandos/gates y pasa a
      `.issues/done/` con `Status: DONE`
- [ ] Commit solo tras un “sí” explícito; mensaje en español y referencia `#NNN`
