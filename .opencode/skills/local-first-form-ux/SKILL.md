---
name: local-first-form-ux
description: Use cuando el usuario reporte que agregar skills o campos en la "tarjeta de datos"/modal de edición tarda en reflejarse, que "Save changes"/"Guardar cambios" deja la vista congelada sin indicador de carga, o pida que una edición se guarde recién al pulsar Save (estado local hasta guardar, overlay de carga). Cubre el flujo completo en este repo: diagnóstico (bundle viejo en tasker-board), implementación Vue local-first, tests, build y despliegue.
---

# Flujo de trabajo: formularios local-first con guardado explícito

Patrón a seguir cuando una UI de edición sea lenta por llamadas API por-campo
o un guardado sin feedback. Objetivo: mínimo código, mínimo tokens, cero
regresiones. Aplicado y probado en `EditUserModal.vue` + `UsersView.vue`.

## 1. Diagnóstico rápido

1. ¿Dónde corre la UI? `19001` sirve `tasker-board` con **bundle pre-compilado**
   de `frontend/dist/` (el Dockerfile NO compila). Si el usuario reporta
   comportamiento viejo (POST/DELETE por chip, demoras), reconstruir ANTES de
   concluir que el fix falló (ver §5).
2. Localizar el componente (grep por clave i18n o "Save changes") y clasificar
   cada llamada API:
   - **Escritura por acción de UI** (POST/DELETE al agregar/quitar, Enter, "+")
     → mover a la única acción de guardado.
   - **Lectura redundante al abrir** (GET de datos que ya vienen en el prop)
     → eliminar; conservar solo lecturas de catálogos compartidos.
   - **Escritura en Save** (PUT) → la única correcta.

## 2. Reglas de diseño (no negociables)

1. Formulario = **estado local puro**: chips/campos al instante, sin `busy`,
   sin `await`, sin errores inline por campo. Dedupe case-insensitive.
2. **Única** llamada de escritura en "Save changes". Verificar en backend que
   el PUT hace replace de la colección (en `user_store.py`: bloque
   `if skills is not None: DELETE ... INSERT ...`) antes de eliminar los
   endpoints por-campo del cliente.
3. **Nunca perder ediciones**: clic en Save → el modal **se cierra ya** →
   overlay full-screen (`LoadingSpinner` + i18n `users.saving`, `z-[90]`,
   `role="status"`) mientras corre el PUT → éxito: toast + la vista se
   actualiza con la **respuesta del PUT** (sin refetch); fallo: toast de error
   y **reabrir el modal con el borrador** (patrón #566 conservado).
4. El hijo solo hace `emit('save', {...form})`; el padre (vista) controla
   cierre, overlay y reapertura. El modal nunca emite `close` en save.
5. **Variante crear** (`CreateUserModal`): mismo contrato + prop `initial`
   (borrador que el padre re-pasa al reabrir tras fallo; el modal lo copia al
   form en su `watch(show)` y si no hay borrador hace `resetForm()`). El
   padre usa un único ref de overlay con etiqueta condicional
   (`users.creating` vs `users.saving`).
6. i18n: claves nuevas en `frontend/src/locales/en.json` **y** `es.json`
   (sección `users`).

## 3. Archivos clave de este repo

- Modal/form: `frontend/src/components/users/EditUserModal.vue` (contrato
  emit igual en `EditAgentModal.vue` y `CreateUserModal.vue`).
- Vista + overlay + `saveUser()`: `frontend/src/views/UsersView.vue`
  (ref `savingUser`; cierra → overlay → éxito/fallo-reabre).
- Store: `frontend/src/stores/usersStore.ts` (`updateUser` sustituye la fila
  con la respuesta).
- `frontend/src/api/userSkillsApi.ts`: **conservar** aunque el modal ya no lo
  use (los endpoints siguen vivos y sus `not.toHaveBeenCalled` en tests son la
  red de seguridad contra recaídas).

## 4. Tests (obligatorios)

- Spec del componente: "instantáneo" se prueba **sin** `flushPromises` antes
  del assert de chip + `expect(addX).not.toHaveBeenCalled()`.
- Spec de la vista: `mockImplementation(() => new Promise(...))` y afirmar
  mientras está en vuelo: (a) modal cerrado, (b) overlay visible, (c) sin
  toast; resolver → (d) overlay fuera, (e) toast éxito. Los tests de fallo
  (409/422/429) deben seguir afirmando `props('show') === true` al final.
- Comandos (PowerShell, desde `frontend/`):
  1. `npx vitest run <spec-tocado>`
  2. `npm test`
  3. `npm run lint` (0 errores; 2 warnings preexistentes en `IssueDetailView.vue` son aceptables)
  4. `npx vue-tsc -b`

## 5. Build y despliegue en vivo

```
npm run build
Select-String -Path dist\assets\*.js -Pattern '<string nuevo>'
docker compose build tasker-board
docker compose up -d tasker-board
```
Verificar que `http://127.0.0.1:19001/` referencia el hash nuevo del bundle y
que ese JS contiene el string nuevo. El usuario prueba contra `19001`, no
contra `vite dev`.

## 6. Git

- Mensajes en español **sin tildes** (`fix(users): ...`, `feat(users): ...`).
- **Nunca** commitear sin `si` explícito; antes: `git status --short` y
  confirmar que solo cambiaron los archivos previstos (`dist/` está ignorado).

## Anti-patrones

- Llamar a la API "para refrescar" tras mutar un campo local.
- Modal abierto durante el PUT sin indicador (UI "congelada").
- Cerrar sin conservar el borrador en error (pierde ediciones).
- Recrear contenedores con volúmenes anónimos sin re-verificar conteo de datos.
