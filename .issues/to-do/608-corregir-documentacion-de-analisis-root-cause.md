# Issue #608: Corregir la documentación del contrato de análisis de causa raíz

## Description

El informe [report.md](../../report.md) registró un desajuste entre el ejemplo de
`API_REFERENCE.md` y el contrato real. La documentación envía:

```json
{
  "test_failure": "test_login_special_chars fails",
  "component_id": "<uuid>"
}
```

Sin embargo, `POST /api/v1/analyze/root-cause` recibe `TestFailureRequest`, cuyos
campos son `test_id`, `test_name`, `error_message`, `stack_trace`, `component` y
`labels`; `component_id` y `test_failure` no forman parte del schema. Además, el
handler está marcado deprecated y la documentación debe distinguirlo de
`POST /api/v1/analyze/link-test`, que ofrece el contrato actual.

## Status: TODO

## Priority: MEDIUM

## Component
Documentación API / análisis

## Type
docs / API

## Implementation

1. Actualizar los ejemplos y la descripción de `API_REFERENCE.md` para usar un body
   válido conforme a `TestFailureRequest`, con `component` en vez de `component_id`.
2. Documentar explícitamente que `/analyze/root-cause` está deprecated y dirigir a
   `/analyze/link-test` como endpoint recomendado; indicar si ambos comparten schema.
3. Revisar `docs/API_REFERENCE.md` y cualquier otra copia de la referencia para que
   no queden ejemplos contradictorios.
4. Contrastar la documentación con el OpenAPI generado y añadir una validación de
   documentación/API si el repositorio ya ofrece un patrón apropiado.

## Acceptance Criteria
- [ ] Los ejemplos de request de root-cause/link-test validan contra el schema
      publicado en OpenAPI.
- [ ] El ejemplo no usa `test_failure` ni `component_id` como campos del body.
- [ ] La deprecación de `/analyze/root-cause` y el endpoint recomendado quedan claros
      en las referencias mantenidas.
- [ ] No quedan ejemplos duplicados desactualizados en `API_REFERENCE.md` ni
      `docs/API_REFERENCE.md`.

## Files to Modify
- `API_REFERENCE.md`
- `docs/API_REFERENCE.md`
- Tests de contrato/documentación existentes, si corresponde

## Related Issues
- Revisión general del proyecto: FIND-001 de `report.md`
- #595 (contratos requestBody en OpenAPI)

## Notes
- La implementación actual de `TestFailureRequest` declara `test_id`, `test_name`,
  `error_message`, `stack_trace`, `component` y `labels`.
- El endpoint `/analyze/root-cause` aparece como deprecated en el router de análisis.
