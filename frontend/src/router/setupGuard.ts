import type { RouteLocationNormalized } from 'vue-router'
import { isMockMode } from '@/api/client'
import { useUiStore } from '@/stores/uiStore'
import { useToast } from '@/composables/useToast'
import i18n from '@/i18n'

export type SetupGuardDecision = true | { path: string; replace: boolean }

/**
 * First-installation guard (issue #544). Runs after `initSession()`:
 * a fresh system (installed === false) is forced into /setup, while an
 * installed system cannot enter the wizard. In mock mode the demo is
 * never blocked and the setup API is never called.
 */
export async function applySetupGuard(
  to: Pick<RouteLocationNormalized, 'path'>,
): Promise<SetupGuardDecision> {
  if (isMockMode()) {
    return true
  }
  const uiStore = useUiStore()
  const firstCheck = !uiStore.setupChecked
  const ok = await uiStore.checkSetupStatus()
  if (!ok && firstCheck) {
    useToast().warning(i18n.global.t('setup.statusError'))
  }
  if (uiStore.isInstalled === false && to.path !== '/setup') {
    return { path: '/setup', replace: true }
  }
  if (uiStore.isInstalled === true && to.path === '/setup') {
    return { path: '/board', replace: true }
  }
  return true
}
