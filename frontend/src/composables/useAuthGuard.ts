// Route/action-level RBAC helpers for components (issue #519).
// authStore stays router-free to avoid import cycles; path checks resolve
// meta through the router instance instead.

import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

export function useAuthGuard() {
  const authStore = useAuthStore()
  const router = useRouter()

  return {
    can: (action: string) => authStore.can(action),
    hasRole: (...roles: string[]) => authStore.hasRole(...roles),
    canRoute: (path: string) => {
      const resolved = router.resolve(path)
      return authStore.rolesAllowed(resolved.meta.roles as string[] | undefined)
    },
  }
}
