import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/mockApi'
import type { User } from '@/types'

export const useUsersStore = defineStore('users', () => {
  const users = ref<User[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const humans = computed(() => users.value.filter(u => u.type === 'human'))
  const agents = computed(() => users.value.filter(u => u.type === 'agent'))
  const activeAgents = computed(() => agents.value.filter(a => a.is_active))

  async function fetchUsers() {
    loading.value = true
    error.value = null
    try {
      users.value = await api.fetchUsers()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function updateUser(id: string, data: Partial<User>): Promise<User | null> {
    try {
      const updated = await api.updateUser(id, data)
      const idx = users.value.findIndex(u => u.id === id)
      if (idx !== -1) users.value[idx] = updated
      return updated
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  return {
    users,
    loading,
    error,
    humans,
    agents,
    activeAgents,
    fetchUsers,
    updateUser,
  }
})
