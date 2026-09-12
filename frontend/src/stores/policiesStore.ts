import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchPolicies as apiFetchPolicies, createPolicy as apiCreatePolicy, deletePolicy as apiDeletePolicy } from '@/api/mockApi'
import type { Policy } from '@/types'

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
      policies.value = await apiFetchPolicies()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function createPolicy(body: { name: string; description?: string; rule: string; level?: string; target_scope?: string }): Promise<Policy | null> {
    try {
      const policy = await apiCreatePolicy(body)
      policies.value.push(policy)
      return policy
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function deletePolicy(id: string): Promise<boolean> {
    try {
      await apiDeletePolicy(id)
      policies.value = policies.value.filter(p => p.id !== id)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
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
  }
})
