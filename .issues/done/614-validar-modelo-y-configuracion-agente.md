# Issue #614: Validar el modelo y sus parámetros al configurar agentes

## Description

Un perfil puede persistirse aunque el modelo seleccionado no esté permitido o
configurado para la ejecución. Los parámetros tampoco deben aceptarse fuera del
rango compatible con el modelo/proveedor. Un modelo no disponible debe producir
un error claro, no una sustitución silenciosa por otra configuración.

Completar y verificar **AGENT-03** según
`docs/domain-definitions/users/agents_user_definition.md`.

## Status: DONE

## Priority: HIGH

## Component
Backend / usuarios-agente / configuración de inferencia

## Type
feat / backend

## Implementation

1. Validar en el servidor que el modelo pertenezca al catálogo permitido y esté
   configurado para el entorno de ejecución.
2. Validar temperatura y demás parámetros contra las capacidades y rangos
   soportados por el modelo/proveedor.
3. Devolver errores diferenciados para modelo no permitido, no configurado y
   parámetros incompatibles.
4. Verificar que las credenciales se obtengan de configuración segura y no se
   persistan en perfiles, prompts, logs ni respuestas de API.

## Acceptance Criteria
- [x] Modelo ausente, no permitido o no configurado produce un error explícito.
- [x] Los parámetros fuera del rango o no compatibles se rechazan en backend.
- [x] No se sustituye silenciosamente un modelo o parámetro inválido por otro.
- [x] La interfaz muestra el error recibido y no confirma una configuración
      fallida como exitosa.
- [x] Pruebas cubren modelos válidos e inválidos y parámetros en los límites.
- [x] Credenciales del proveedor no aparecen en persistencia, logs ni respuestas.

## Files to Modify
- `src/socialseed_tasker/` — esquema y validación de perfiles/configuración
- Configuración y catálogo de modelos de la ejecución de agentes
- `frontend/src/` — presentación de errores de configuración, si corresponde
- Pruebas del contrato y de la ejecución

## Related Issues
- #564 (CRUD de perfiles de agente)
- #573 (migración de Agent Studio a la API)

## Notes
- Requisito de referencia: **AGENT-03**.
- La validación no debe introducir credenciales dentro del perfil reutilizable.

## Resolution

- Catálogo backend cerrado a los seis modelos ofrecidos por los formularios.
  Cada proveedor exige su variable de configuración en runtime (Anthropic,
  OpenAI, Gemini/Google u Ollama); credenciales ausentes generan `503` sin
  incluir valores secretos en errores.
- Crear requiere un modelo del catálogo; identificadores desconocidos y
  temperatura no finita/fuera del rango del modelo/proveedor (`0..1` para
  Anthropic, `0..2` para el resto) se rechazan con `422`. No se normalizan ni
  reemplazan modelos o parámetros no válidos.
- Actualizar valida el modelo antes de persistir y conserva el `404` para
  perfiles inexistentes. Credenciales no forman parte del esquema ni de la
  respuesta.
- La UI muestra el error recibido; una creación fallida conserva el borrador y
  no agrega el agente ni muestra éxito.
- Pruebas API cubren ausencia, catálogo, configuración del proveedor, límites,
  valores inválidos y ausencia de credenciales en persistencia/respuesta;
  prueba frontend verifica error `503`, sin éxito ni agente añadido.
