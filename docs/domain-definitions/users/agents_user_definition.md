# Definición de usuario agente

Este documento define qué significa crear y configurar un usuario de tipo
agente en SocialSeed Tasker. Es la referencia funcional para el formulario,
el perfil persistido y las políticas que el sistema debe aplicar al ejecutar
un agente.

## Propósito y alcance

Un **usuario agente** es una identidad no humana que representa una
configuración reutilizable de agente dentro de Tasker. Su perfil declara para
qué sirve, qué modelo y capacidades puede usar, en qué alcance puede operar y
bajo qué límites y aprobaciones.

El perfil no es, por sí solo, una sesión de ejecución, una credencial, un rol
RBAC ni una autorización para ignorar las políticas del proyecto. La
orquestación decide cuándo y sobre qué tarea se ejecuta; la autorización se
valida en el servidor cada vez que el agente intenta realizar una acción.

Este documento cubre la definición del agente y su creación. No define el
posicionamiento comercial, la monetización ni el roadmap general del producto.
Debe usarse como fuente funcional al crear issues para cambios del perfil,
su interfaz, API, persistencia o ejecución.

Los términos **DEBE**, **NO DEBE** y **PUEDE** expresan requisitos normativos.
Los identificadores `AGENT-*` de la sección de requisitos son referencias
estables para issues y pruebas; no son identificadores de issues de GitHub.

## Estado de implementación

Los estados distinguen persistir una configuración de hacerla cumplir durante
la ejecución:

- **Implementado como dato:** existe en el contrato/perfil; no implica que
  controle acciones en tiempo de ejecución.
- **Parcial:** hay soporte en algunas capas, pero no se garantiza el
  comportamiento completo descrito en este documento.
- **Pendiente:** falta implementar o verificar el requisito.

| Capacidad | Estado conocido | Alcance |
|---|---|---|
| Identidad de agente y CRUD de perfiles | Implementado como dato | Perfil independiente; sin credenciales ni rol RBAC humano |
| Modelo, especialización, temperatura e instrucciones | Implementado como dato | Se almacenan en el perfil; la disponibilidad del modelo depende de la configuración de ejecución |
| Skills y herramientas | Parcial | El perfil las referencia y las herramientas se validan contra catálogo; esto no demuestra autorización efectiva al invocarlas |
| Alcance de escritura | Parcial | Existe `write_access`; el perfil no expresa por separado el alcance de lectura ni demuestra enforcement para cada acción |
| Límites | Parcial | Existe el campo `limits`; el formato y enforcement de cada límite deben especificarse y verificarse |
| Aprobaciones, políticas heredadas y escalado | Pendiente de confirmar | No asumir enforcement completo por la presencia de datos o controles de interfaz |
| Auditoría de acciones y aprobación | Pendiente de confirmar | Verificar cobertura de ejecución, cambios de permisos y resultados |

Antes de cerrar un issue, actualizar esta tabla con la evidencia verificable
(código, pruebas y rutas de ejecución) y ajustar el estado. No marcar una
capacidad como implementada solo porque exista un campo en el perfil.

## Principios obligatorios

1. **Mínimo privilegio:** un agente recibe solo las capacidades y el alcance
   que necesita. La ausencia de una concesión explícita no concede acceso.
2. **Política superior prevalece:** las políticas de organización y proyecto
   limitan el perfil. El agente no puede ampliar esos permisos.
3. **Denegar por defecto:** capacidades desconocidas, recursos no declarados o
   políticas que no puedan evaluarse no autorizan la acción.
4. **Separar propósito de autoridad:** especializaciones como `QA` o
   `Frontend` describen el trabajo; nunca otorgan permisos implícitos.
5. **Aplicar controles fuera del prompt:** el prompt orienta el comportamiento,
   pero no es un mecanismo de autorización ni una frontera de seguridad.
6. **Trazabilidad:** las ejecuciones y decisiones relevantes deben poder
   atribuirse al agente y a la persona o proceso que las inició o aprobó.

## Datos del perfil

### Identidad y estado

- **Nombre de usuario:** identificador legible y único para el perfil.
- **Correo y avatar:** datos opcionales de presentación; no son credenciales
  ni prueban identidad humana.
- **Estado:** habilitado o deshabilitado. Un agente deshabilitado no puede
  iniciar nuevas ejecuciones. La política de cancelación de ejecuciones activas
  debe ser explícita en el sistema de ejecución.
- **Identificador persistente:** lo genera el backend; no lo elige el cliente.
- **Fechas de creación y último uso:** metadatos de ciclo de vida, no
  configuración editable por el usuario salvo que una operación del sistema
  registre el último uso.

Los perfiles de agente no reciben contraseña, token de inicio de sesión ni rol
RBAC humano. Su identidad no debe permitir autenticar una sesión interactiva
como si fuera una persona.

### Propósito

- **Especialización:** área principal de trabajo, por ejemplo `QA`,
  `documentación` o `frontend`.
- **Descripción/instrucciones de rol:** resultado esperado, contexto pertinente
  y forma de comunicar. Debe ser breve, clara y no contener secretos.
- **Skills y workflows:** referencias a capacidades reutilizables disponibles
  para el agente. Deben validarse contra catálogos conocidos; asignar una skill
  no debe ampliar permisos por sí mismo.

La especialización, la descripción y las instrucciones no sustituyen las
políticas de acceso.

### Modelo e inferencia

- **Modelo:** modelo disponible y permitido por la configuración del proyecto.
- **Temperatura y parámetros compatibles:** solo se ofrecen parámetros que el
  proveedor/modelo admita. Los valores deben validarse en el backend contra el
  rango soportado.
- **Credenciales del proveedor:** se administran fuera del perfil, mediante
  configuración segura del entorno o del sistema de secretos. Nunca se
  persisten en el prompt, el perfil, los logs ni las respuestas de la API.

El sistema debe distinguir un modelo no configurado de un perfil correctamente
configurado y comunicar el error; no debe sustituir silenciosamente el modelo.

### Capacidades y alcance

El perfil declara capacidades de forma explícita y separada:

- **Herramientas permitidas:** identificadores del catálogo de herramientas.
  Solo se pueden seleccionar herramientas conocidas y habilitadas por el
  proyecto.
- **Acceso de lectura:** recursos o áreas que puede consultar.
- **Acceso de escritura:** recursos o áreas donde puede proponer o aplicar
  cambios, según las acciones concedidas.
- **Acciones restringidas:** operaciones que no están disponibles o que
  requieren aprobación adicional.

Lectura y escritura son permisos distintos. Una lista de carpetas editables no
debe interpretarse como permiso para ejecutar cualquier herramienta o cambiar
cualquier recurso relacionado. El servidor valida cada acción contra el
catálogo y el alcance efectivo antes de ejecutarla.

No se deben ofrecer consultas Cypher arbitrarias ni permisos amplios sobre la
base de datos como sustituto de capacidades de dominio acotadas. Las reglas de
arquitectura y dependencias se expresan como políticas evaluables por Tasker.

#### Semántica de permisos y valores ausentes

- Una herramienta desconocida, una referencia inválida o una capacidad no
  habilitada por el proyecto se rechaza; nunca se interpreta como acceso
  irrestricto.
- Una lista vacía o ausente de herramientas o recursos **no concede acceso**.
  La interfaz debe distinguir claramente “sin acceso” de “heredado”.
- La autorización se calcula con las políticas de organización y proyecto y
  las restricciones del perfil. El perfil puede restringir, pero no ampliar,
  los permisos permitidos por una política superior.
- El alcance de lectura y escritura se declara por separado. La escritura
  siempre requiere una capacidad explícita; no se deriva de la lectura.
- Un agente puede **proponer** un cambio (por ejemplo, generar un parche o
  borrador sin aplicarlo) sin que eso signifique permiso para **aplicarlo**.
  La aplicación es una acción independiente, sujeta a alcance y aprobación.
- `write_access` solo define alcance potencial de escritura. No autoriza por sí
  solo ejecución de comandos, publicación, push, borrado ni otras acciones con
  efectos secundarios.

### Aprobaciones y límites

El perfil puede declarar restricciones adicionales. Las políticas de
organización/proyecto establecen los valores máximos permitidos y los
requisitos mínimos de aprobación. La interfaz muestra si cada valor es
heredado o configurado en el perfil.

- **Acciones que requieren aprobación humana**, especialmente escritura,
  borrado, publicación externa, cambios de configuración o ejecución de
  comandos con efectos secundarios.
- **Límite de costo o tokens por ejecución**, con unidades y comportamiento al
  alcanzar el límite claramente definidos.
- **Duración máxima y número máximo de pasos/acciones**, para detener ciclos o
  ejecuciones que no progresan.
- **Condiciones de escalado**, por ejemplo una prueba que sigue fallando,
  conflicto de cambios, impacto clasificado como crítico, falta de permisos o
  confianza insuficiente.

Al alcanzar un límite o necesitar aprobación, el agente debe detener la acción
afectada, registrar el motivo y dejar la ejecución en un estado visible. No
debe degradarse silenciosamente ni reportar éxito.

#### Reglas de aprobación

- Mientras no exista una política explícita que permita autonomía, las
  acciones que modifican estado o producen efectos externos requieren
  aprobación humana.
- Las acciones destructivas, publicación externa, cambios de permisos o
  configuración y operaciones sobre recursos protegidos requieren aprobación
  explícita, incluso si otras escrituras están permitidas autónomamente. Una
  política superior puede prohibirlas por completo.
- La aprobación debe proceder de una persona autenticada con permiso de
  aprobación en el proyecto. Un agente no puede aprobar su propia acción.
- La solicitud de aprobación identifica al menos la ejecución, la acción
  concreta, el alcance y el efecto previsto. Aprobar una acción no aprueba
  acciones futuras ni cambios sustanciales en su contenido.
- Un cambio en la acción después de aprobada invalida la aprobación y exige
  una nueva. Reintentar una acción idéntica no debe ampliar su alcance.
- Rechazo, revocación antes de la ejecución o ausencia de respuesta dentro del
  plazo definido deja la acción sin ejecutar y la ejecución en un estado
  visible. El plazo debe provenir de una política explícita; si no está
  configurado, el sistema no debe asumir aprobación.

Las cuotas globales, la limitación de peticiones a la API y los límites del
proveedor son políticas de organización/proyecto o de infraestructura, no
límites personales que el agente pueda elevar desde su perfil.

#### Reglas de límites

- Cada límite declara valor, unidad, ámbito (por acción, ejecución, agente o
  proyecto) y comportamiento al alcanzarlo.
- Los límites del perfil no pueden superar los máximos de organización o
  proyecto. Si ambos están configurados, se aplica el límite más restrictivo.
- Un límite ausente hereda la política superior. Si no hay límite superior
  configurado, la acción no debe presentarse como limitada; el sistema debe
  aplicar y documentar los límites operativos globales disponibles.
- El consumo se contabiliza en el servidor. Al alcanzarse el límite, se
  detienen nuevas acciones, se registra el consumo y se informa el motivo.

## Autorización efectiva

Para autorizar una acción, Tasker combina:

1. Las políticas de la organización.
2. Las políticas del proyecto.
3. El estado habilitado y las restricciones del perfil.
4. Las capacidades de la herramienta y el alcance del recurso.
5. La aprobación humana requerida para esa acción.

La autorización efectiva es la intersección de las concesiones aplicables y
las restricciones. El perfil puede restringir permisos heredados, pero no
puede ampliarlos. Si una política superior prohíbe una acción, una concesión
del perfil no la habilita. Toda acción debe volver a validarse al ejecutarse;
ocultar un botón en la interfaz no constituye control de acceso.

Las políticas de ramas Git y PR, cuando existan, deben seguir el mismo
principio: definir explícitamente las ramas y acciones permitidas, y no asumir
que un agente puede hacer push directo a ramas protegidas.

## Flujo de creación

1. La persona abre la creación de un usuario y selecciona el tipo **Agente**.
2. Define nombre, propósito, especialización y, opcionalmente, avatar y correo.
3. Selecciona un modelo permitido y sus parámetros compatibles.
4. Asigna skills, herramientas y alcance de lectura/escritura desde catálogos
   controlados.
5. Revisa aprobaciones, límites y condiciones de escalado efectivos. Los
   valores heredados deben mostrarse como heredados y no como permisos
   concedidos por el perfil.
6. El sistema valida los campos y las referencias en el servidor, y crea la
   identidad y el perfil de forma consistente.
7. El agente queda habilitado solo si la configuración es válida. Si requiere
   configuración adicional, el estado debe indicarlo y no permitir una
   ejecución no válida.
8. La interfaz confirma el resultado solo después de recibir confirmación del
   backend. Los errores de validación, permisos, duplicado o persistencia se
   muestran claramente y no cierran el formulario como si hubiera tenido
   éxito.

Crear un perfil no debe iniciar una ejecución ni conceder por sí mismo
aprobaciones, credenciales o acceso a recursos.

### Ejemplo funcional

Ejemplo de intención de configuración, no de un formato JSON/API:

| Propiedad | Agente QA |
|---|---|
| Propósito | Analizar cambios y proponer pruebas |
| Skills | Skills de testing aprobadas por el proyecto |
| Herramientas | Solo herramientas de lectura y testing del catálogo permitido |
| Lectura | Código y resultados de pruebas del proyecto |
| Escritura | Sin aplicación autónoma de cambios; puede preparar una propuesta |
| Aprobación | Requerida antes de aplicar cambios o ejecutar acciones con efectos externos |
| Límites | Heredados de la organización/proyecto, con límites adicionales si se configuran |
| Credenciales | Proporcionadas por el sistema de ejecución; no guardadas en el perfil |

Este ejemplo ilustra que el rol “QA” describe el propósito, pero no concede
permisos por sí mismo.

## Auditoría y ciclo de vida

Cada ejecución debe registrar, como mínimo, el identificador del perfil, el
modelo usado, el iniciador, las acciones solicitadas y realizadas, las
aprobaciones, los recursos afectados, los límites consumidos y el resultado.
Los logs no deben incluir secretos ni cadenas de razonamiento privadas; sí
deben conservar decisiones operativas y motivos de autorización o rechazo
suficientes para auditoría.

Deshabilitar o eliminar un perfil debe impedir su uso futuro y conservar la
trazabilidad histórica conforme a la política de retención del proyecto. Los
cambios de permisos deben tener efecto en las siguientes validaciones de
acciones, incluyendo las de ejecuciones en curso.

## Alcance actual y evolución

El perfil existente ya contempla identidad, modelo, especialización,
temperatura, prompt, herramientas, permisos de escritura, límites, skills y
estado habilitado. La interfaz y el contrato/API son parte de este alcance.
Esto no implica que todos los campos cuenten ya con autorización efectiva en
tiempo de ejecución.

Antes de presentar como funcional una opción de seguridad, debe verificarse
que se valida en backend al ejecutar la acción, que aplica a todas las rutas
relevantes y que existe una prueba de rechazo para el caso no autorizado. Una
opción de UI o una instrucción en el prompt, sin enforcement, es solo
configuración descriptiva.

## Requisitos para derivar issues

Usar los identificadores siguientes como etiquetas de referencia en los
issues. Un issue puede cubrir más de un requisito relacionado, pero debe
indicar qué identificadores completa y actualizar su estado al cerrarse.

### Fundación del contrato

- **AGENT-01 — Contrato de permisos explícito** — Pendiente. Definir en
  esquemas, almacenamiento y API permisos separados de lectura, propuesta,
  aplicación y ejecución de herramientas. **Aceptación:** valores inválidos
  se rechazan; ausencia o lista vacía no concede acceso; la respuesta y la
  documentación describen la semántica sin ambigüedad.
- **AGENT-02 — Herencia y precedencia de políticas** — Pendiente. Implementar
  la combinación organización/proyecto/perfil. **Aceptación:** una prueba
  demuestra que un perfil no puede ampliar una política superior; los valores
  heredados se distinguen de los valores explícitos y las decisiones no
  disponibles fallan de forma segura.
- **AGENT-03 — Validación de modelo y configuración** — Pendiente de verificar.
  Comprobar y completar la validación de que el modelo esté permitido y
  configurado y que sus parámetros estén dentro del rango soportado.
  **Aceptación:** modelo o parámetro inválido produce error explícito; no se
  sustituye silenciosamente por un valor distinto.

### Enforcement y seguridad operativa

- **AGENT-04 — Autorización en cada acción** — Pendiente de confirmar.
  Aplicar la decisión de permisos en el backend/herramienta al momento de cada
  acción, no solo al guardar el perfil o mostrar la UI. **Aceptación:** pruebas
  cubren acciones permitidas y denegadas, acceso a recursos fuera del alcance,
  perfil deshabilitado y cambios de política.
- **AGENT-05 — Flujo de aprobación humana** — Pendiente. Implementar solicitud,
  aprobación, rechazo, revocación y vencimiento. **Aceptación:** solo una
  persona autenticada y autorizada aprueba; la aprobación está vinculada a la
  acción concreta; acción modificada o vencida no se ejecuta con la aprobación
  anterior; rechazo o timeout no reporta éxito.
- **AGENT-06 — Enforcement de límites** — Parcial. Definir esquema tipado y
  aplicar límites de costo/tokens, duración y pasos/acciones en el servidor.
  **Aceptación:** medición y detención son comprobables; se aplica el límite
  más restrictivo; al agotarse, no se inician nuevas acciones y se registra
  el motivo.
- **AGENT-07 — Auditoría de ejecuciones** — Pendiente de confirmar. Registrar
  actor iniciador, perfil, modelo, acciones, recursos, decisiones de
  autorización, aprobaciones, consumo y resultado. **Aceptación:** el
  historial es consultable por usuarios autorizados, permite reconstruir el
  resultado y no expone secretos ni razonamiento privado.
- **AGENT-08 — Deshabilitación y cambios durante una ejecución** — Pendiente
  de confirmar. Definir y aplicar el efecto de deshabilitar, eliminar o
  cambiar permisos con ejecuciones activas. **Aceptación:** no se inician
  nuevas acciones no autorizadas; el estado final y la causa quedan auditados.

### Experiencia de creación y mantenimiento

- **AGENT-09 — Formulario fiel a la política efectiva** — Parcial. Mostrar
  propósito, capacidades, alcance, aprobaciones y límites con sus fuentes
  (perfil o política heredada). **Aceptación:** la UI no presenta
  configuración descriptiva como enforcement activo; errores de validación y
  persistencia se muestran y no simulan éxito.
- **AGENT-10 — Pruebas y documentación del contrato** — Pendiente. Mantener
  pruebas de API, persistencia, interfaz y enforcement alineadas con esta
  definición. **Aceptación:** cada campo nuevo documenta validación, valor por
  defecto, herencia y comportamiento inválido; los cambios actualizan esta
  tabla y la sección de estado.

Antes de crear un issue, comprobar el estado de implementación para evitar
duplicar trabajo. Cada issue debe indicar requisito(s) `AGENT-*`, capas
afectadas, comportamiento esperado, criterios de aceptación y pruebas
necesarias.

## Mantenimiento de esta definición

Actualizar este documento en el mismo cambio que modifique el contrato
funcional de creación o edición de agentes, incluidos cambios en:

- formulario y experiencia de creación/edición;
- esquemas, API, almacenamiento o migraciones;
- catálogo y autorización de herramientas;
- políticas, aprobaciones, límites y ejecución;
- auditoría o ciclo de vida.

Al añadir un campo, documentar su propósito, validación, valor por defecto,
alcance, precedencia respecto a políticas superiores y efecto al faltar o ser
inválido. Añadir o actualizar pruebas para el comportamiento observable,
especialmente para rechazos de permisos, límites y aprobaciones. Mantener
separados en la documentación los controles implementados de los pendientes.
