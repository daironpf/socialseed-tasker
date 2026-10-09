import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/usersApi'
import { fetchAgentProfiles } from '@/api/agentProfilesApi'
import { isMockMode } from '@/api/client'
import { mergeStudioAgents } from '@/utils/studioAgents'
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
      if (isMockMode()) {
        // Mock owns its whole collection (#565): no /agents/profiles call in mock mode.
        users.value = mergeStudioAgents(await api.fetchUsers())
        return
      }
      const [humansResult, profilesResult] = await Promise.allSettled([
        api.fetchUsers().then(mergeStudioAgents),
        fetchAgentProfiles(),
      ])
      if (humansResult.status === 'rejected') throw humansResult.reason
      const humansList = humansResult.value
      if (profilesResult.status === 'rejected') {
        // A 503 (no database) must never hide the humans (#565).
        console.warn('agent profiles unavailable, showing humans only:', profilesResult.reason)
        users.value = humansList
        return
      }
      const seen = new Set(humansList.map(u => u.id))
      const merged = [...humansList]
      for (const profile of profilesResult.value) {
        if (!seen.has(profile.id)) {
          seen.add(profile.id)
          merged.push(profile)
        }
      }
      users.value = merged
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function updateUser(id: string, data: Partial<User>): Promise<User> {
    try {
      const updated = await api.updateUser(id, data)
      const idx = users.value.findIndex(u => u.id === id)
      if (idx !== -1) users.value[idx] = updated
      error.value = null
      return updated
    } catch (e) {
      error.value = (e as Error).message
      throw e
    }
  }

  async function createUser(body: api.UserCreateRequest): Promise<api.CreateUserResult> {
    try {
      const result = await api.createUser(body)
      error.value = null
      users.value.push(result.user)
      return result
    } catch (e) {
      error.value = (e as Error).message
      throw e
    }
  }

  async function deleteUser(id: string): Promise<void> {
    try {
      await api.deleteUser(id)
      users.value = users.value.filter(u => u.id !== id)
      error.value = null
    } catch (e) {
      error.value = (e as Error).message
      throw e
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
    createUser,
    deleteUser,
  }
})
