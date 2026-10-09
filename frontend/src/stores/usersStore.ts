import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/usersApi'
import {
  createAgentProfile,
  deleteAgentProfile,
  fetchAgentProfiles,
  updateAgentProfile,
  type AgentProfilePayload,
} from '@/api/agentProfilesApi'
import { isMockMode } from '@/api/client'
import { applyStudioUpdate, mergeStudioAgents, removeStudioProfile } from '@/utils/studioAgents'
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

  /**
   * Create an agent card through POST /agents/profiles (#566): the 201 is
   * normalized to the `User` shape (never raw), so the card keeps badge,
   * avatar and skills. Agents have no credential, so there is no temporary
   * password to show. In mock mode the mock collection owns its entities.
   */
  async function createAgent(body: AgentProfilePayload): Promise<User> {
    try {
      let created: User
      if (isMockMode()) {
        const result = await api.createUser({
          ...body,
          type: 'agent',
          role: 'ai-agent',
        } as unknown as api.UserCreateRequest)
        created = result.user
      } else {
        created = await createAgentProfile(body)
      }
      error.value = null
      users.value.push(created)
      return created
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

  function toProfilePayload(data: Partial<User>): AgentProfilePayload {
    const payload: AgentProfilePayload = {}
    if (data.username !== undefined) payload.username = data.username
    if (data.email !== undefined) payload.email = data.email
    if (data.avatar !== undefined) payload.avatar = data.avatar
    if (data.model !== undefined) payload.model = data.model
    if (data.specialization !== undefined) payload.specialization = data.specialization
    if (data.temperature !== undefined) payload.temperature = data.temperature
    if (data.system_prompt !== undefined) payload.system_prompt = data.system_prompt
    if (data.tools !== undefined) payload.tools = data.tools
    if (data.write_access !== undefined) payload.write_access = data.write_access
    if (data.skills !== undefined) payload.skills = data.skills
    return payload
  }

  /**
   * Single dispatch for card edits (#567): `agent-studio-*` persists in
   * localStorage, endpoint agents go to PUT /agents/profiles/{id} (mock mode
   * keeps its whole collection in /users, like createAgent in #566) and
   * humans stay on /users/{id} (#560). A 404 (profile deleted upstream)
   * refreshes the list so the stale card disappears.
   */
  async function editUser(data: Partial<User> & { id: string }): Promise<User> {
    try {
      let updated: User
      if (data.id.startsWith('agent-studio-')) {
        updated = applyStudioUpdate(data)
      } else if (isMockMode()) {
        updated = await api.updateUser(data.id, data)
      } else if (
        data.type === 'agent' ||
        users.value.find(u => u.id === data.id)?.type === 'agent'
      ) {
        updated = await updateAgentProfile(data.id, toProfilePayload(data))
      } else {
        updated = await api.updateUser(data.id, data)
      }
      const idx = users.value.findIndex(u => u.id === data.id)
      if (idx !== -1) users.value[idx] = updated
      error.value = null
      return updated
    } catch (e) {
      // fetchUsers() clears `error` synchronously, so kick it off first and
      // record the failure afterwards (404 -> stale card triggers a refetch).
      if ((e as { status?: number }).status === 404) void fetchUsers()
      error.value = (e as Error).message
      throw e
    }
  }

  /**
   * Delete an agent card (#568): `agent-studio-*` only clears localStorage,
   * mock mode goes through the mock collection (it owns its entities, #566)
   * and endpoint agents hit DELETE /agents/profiles/{id} — the human
   * "last guard" (#562) never applies here. A 404 (already deleted upstream)
   * refreshes the list; on any error the card stays put.
   */
  async function deleteAgent(user: User): Promise<void> {
    try {
      if (user.id.startsWith('agent-studio-')) {
        removeStudioProfile(user.id)
      } else if (isMockMode()) {
        await api.deleteUser(user.id)
      } else {
        await deleteAgentProfile(user.id)
      }
      users.value = users.value.filter(u => u.id !== user.id)
      error.value = null
    } catch (e) {
      // fetchUsers() clears `error` synchronously: kick it off first (#567/#568).
      if ((e as { status?: number }).status === 404) void fetchUsers()
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
    createAgent,
    editUser,
    deleteAgent,
    deleteUser,
  }
})
