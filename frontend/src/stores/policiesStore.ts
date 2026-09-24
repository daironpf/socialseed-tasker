import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/policiesApi'
import type { Policy } from '@/types'
import { useUiStore } from './uiStore'

export const usePoliciesStore = defineStore('policies', () => {
  const policies = ref<Policy[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const activeCount = computed(() => policies.value.filter(p => p.is_active).length)
  const inactiveCount = computed(() => policies.value.filter(p => !p.is_active).length)

  async function fetchPolicies() {
    loading.value = true
    error.value = null
    try {
      policies.value = await api.fetchPolicies()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function createPolicy(body: { name: string; description?: string; rule: string; level?: string; target_scope?: string }): Promise<Policy | null> {
    const uiStore = useUiStore()
    if (uiStore.networkMode === 'offline') {
      const now = new Date().toISOString()
      const local: Policy = {
        id: `local-policy-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`,
        name: body.name,
        description: body.description ?? '',
        rules: [],
        target_scope: body.target_scope ?? 'global',
        logic_definition: body.rule,
        is_active: true,
        created_at: now,
        updated_at: now,
      }
      policies.value.push(local)
      uiStore.enqueueMutation({ entity: 'policy', operation: 'create', entityId: local.id, payload: { ...body } as Record<string, unknown> })
      return local
    }
    try {
      const policy = await api.createPolicy(body)
      policies.value.push(policy)
      return policy
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function deletePolicy(id: string): Promise<boolean> {
    try {
      await api.deletePolicy(id)
      policies.value = policies.value.filter(p => p.id !== id)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    }
  }

  async function updatePolicy(id: string, body: Partial<{ name: string; description: string; rule: string; level: string; target_scope: string; is_active: boolean }>, options?: { skipOfflineQueue?: boolean }): Promise<Policy | null> {
    const uiStore = useUiStore()
    if (uiStore.networkMode === 'offline' && !options?.skipOfflineQueue) {
      const idx = policies.value.findIndex(p => p.id === id)
      if (idx === -1) return null
      const { rule, ...rest } = body
      const merged: Policy = {
        ...policies.value[idx],
        ...rest,
        ...(rule !== undefined ? { logic_definition: rule } : {}),
        updated_at: new Date().toISOString(),
      }
      policies.value[idx] = merged
      uiStore.enqueueMutation({ entity: 'policy', operation: 'update', entityId: id, payload: { ...body } as Record<string, unknown> })
      return merged
    }
    try {
      const updated = await api.updatePolicy(id, body)
      const idx = policies.value.findIndex(p => p.id === id)
      if (idx !== -1) policies.value[idx] = updated
      return updated
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  return {
    policies,
    loading,
    error,
    activeCount,
    inactiveCount,
    fetchPolicies,
    createPolicy,
    deletePolicy,
    updatePolicy,
  }
})
