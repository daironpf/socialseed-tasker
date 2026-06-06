# Issue #410: Menú interactivo de tasker init no documentado para scripting

## Description
El menú interactivo de `tasker init` requiere "START" o Enter para proceder con la configuración, pero la documentación no especifica el formato exacto de entrada esperado para uso automatizado o mediante scripts. Cuando se usan tuberías (pipes) para enviar entrada, el menú no responde de forma predecible.

## Expected Behavior
Debería haber una forma documentada de usar `tasker init` de manera no interactiva, ya sea mediante un flag `--non-interactive` o documentando claramente el formato de entrada esperado.

## Actual Behavior
Al enviar entrada mediante pipes o scripts, el menú no siempre interpreta correctamente las opciones. Por ejemplo, un salto de línea vacío ("\n") produce "Invalid option", mientras que "START\n" funciona de forma impredecible dependiendo del contexto del menú.

## Steps to Reproduce
1. Ejecutar `echo "" | tasker init`
2. Observar que el menú responde con "Invalid option"
3. Intentar `echo "START" | tasker init` y observar comportamiento inconsistente

## Status: COMPLETED

## Priority: LOW

## Component
CLI

## Suggested Fix
Añadir un flag `--non-interactive` o `--yes` que acepte valores por defecto y permita la inicialización sin intervención manual. Alternativamente, documentar el formato exacto de entrada para scripting.

## Impact
Dificulta la automatización del setup y pruebas de CI/CD. Usuarios que intentan scriptear la inicialización se encuentran con comportamiento impredecible.

## Related Issues
- (none)

## Changes Made
En `src/socialseed_tasker/cli/init_command.py`:
- Añadido flag `--yes` / `-y` a la función `interactive_init_command`
- Cuando `--yes` está activo: se salta todo el menú interactivo y la selección de modo, usando valores por defecto (modo Direct)
- Se imprime "[dim]--yes flag detected, using all default values.[/dim]" para feedback visual

## Verification
1. Ejecutar `tasker init --yes` en un proyecto limpio
2. Verificar que no aparece el menú interactivo
3. Verificar que procede directamente con defaults (modo Direct)
4. Verificar que el proyecto se inicializa correctamente
5. Verificar que `tasker init` sin `--yes` sigue siendo interactivo como antes
