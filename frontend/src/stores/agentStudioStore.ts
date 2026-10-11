import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import i18n from '@/i18n'
import { useToast } from '@/composables/useToast'
import { useUsersStore } from '@/stores/usersStore'
import type { AgentProfile } from '@/types/agentStudio'
import { DEFAULT_LIMITS } from '@/types/agentStudio'
import { isMockMode } from '@/api/client'
import {
  createAgentProfileRaw,
  deleteAgentProfile,
  fetchAgentProfilesRaw,
  updateAgentProfile,
} from '@/api/agentProfilesApi'
import {
  loadStudioProfiles,
  saveStudioProfiles,
  profileToUser,
  backendProfileToStudio,
  studioProfileToPayload,
  wasStudioImported,
  markStudioImported,
} from '@/utils/studioAgents'

export const useAgentStudioStore = defineStore('agentStudio', () => {
  const toast = useToast()
  const usersStore = useUsersStore()

  // Mock seeds synchronously from localStorage; real mode replaces this list
  // when loadProfiles() hits GET /agents/profiles (#573).
  const profiles = ref<AgentProfile[]>(loadStudioProfiles())

  const enabledCount = computed(() => profiles.value.filter(p => p.enabled).length)

  /** Mock persistence: localStorage + card sync into the users view (#573). */
  function persistLocal() {
    saveStudioProfiles(profiles.value)
    syncUsers()
  }

  function syncUsers() {
    const studioIds = new Set(profiles.value.map(p => p.id))
    usersStore.users = usersStore.users
      .filter(u => !u.id.startsWith('agent-studio-') || studioIds.has(u.id))
      .map(u => {
        const profile = profiles.value.find(p => p.id === u.id)
        return profile ? profileToUser(profile) : u
      })
    for (const profile of profiles.value) {
      if (!usersStore.users.some(u => u.id === profile.id)) {
        usersStore.users.push(profileToUser(profile))
      }
    }
  }

  /** Real-mode mutations refresh the Users view so PG-uid cards stay current. */
  function refreshUsers() {
    if (!isMockMode()) void usersStore.fetchUsers()
  }

  async function loadProfiles(): Promise<void> {
    if (isMockMode()) {
      profiles.value = loadStudioProfiles()
      return
    }
    try {
      await importLocalProfiles()
      const raw = await fetchAgentProfilesRaw()
      profiles.value = raw.map(backendProfileToStudio)
    } catch (e) {
      // Degrade to the local copy rather than an empty library (#573).
      console.warn('agent profiles unavailable, keeping local copy:', e)
      profiles.value = loadStudioProfiles()
    }
  }

  /**
   * One-time import of legacy `agent-studio-*` profiles into /agents/profiles
   * (#573): every local profile becomes a PG row (uid generated there) and the
   * legacy key is cleared behind the `agent-studio-v1-imported` flag so the
   * import never runs twice. A 409 (username already in PG) or a failed POST
   * only skips that profile.
   */
  async function importLocalProfiles(): Promise<void> {
    if (wasStudioImported()) return
    const local = loadStudioProfiles()
    let imported = 0
    for (const profile of local) {
      try {
        await createAgentProfileRaw(studioProfileToPayload(profile))
        imported++
      } catch (e) {
        console.warn(`studio profile "${profile.name}" was not imported:`, e)
      }
    }
    markStudioImported()
    if (local.length) saveStudioProfiles([])
    if (imported > 0) {
      toast.success(i18n.global.t('agentStudio.imported', { count: imported }))
    }
    refreshUsers()
  }

  function blankProfile(): Omit<AgentProfile, 'id' | 'createdAt'> {
    return {
      name: '',
      role: 'developer',
      avatar: '🤖',
      model: 'gpt-4o',
      systemPrompt: '',
      tools: [],
      limits: { ...DEFAULT_LIMITS },
      enabled: true,
    }
  }

  async function saveProfile(
    input: Omit<AgentProfile, 'id' | 'createdAt'>,
    existingId?: string,
  ): Promise<AgentProfile | null> {
    const name = input.name.trim()
    if (!name) {
      toast.error('Agent name is required')
      return null
    }
    if (existingId) {
      const idx = profiles.value.findIndex(p => p.id === existingId)
      if (idx < 0) return null
      const merged: AgentProfile = { ...profiles.value[idx], ...input, name }
      if (isMockMode()) {
        profiles.value[idx] = merged
        persistLocal()
        toast.success(`Agent "${name}" updated`)
        return merged
      }
      try {
        await updateAgentProfile(existingId, studioProfileToPayload(merged))
        profiles.value[idx] = merged
        toast.success(`Agent "${name}" updated`)
        refreshUsers()
        return merged
      } catch (e) {
        toast.error((e as Error).message)
        return null
      }
    }
    if (isMockMode()) {
      const profile: AgentProfile = {
        ...input,
        name,
        id: `agent-studio-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
        createdAt: new Date().toISOString(),
      }
      profiles.value.push(profile)
      persistLocal()
      toast.success(`Agent "${name}" saved to library`)
      return profile
    }
    try {
      const created = await createAgentProfileRaw(studioProfileToPayload({ ...input, name }))
      const profile = backendProfileToStudio(created)
      profiles.value.push(profile)
      toast.success(`Agent "${name}" saved to library`)
      refreshUsers()
      return profile
    } catch (e) {
      toast.error((e as Error).message)
      return null
    }
  }

  async function cloneProfile(id: string): Promise<AgentProfile | null> {
    const source = profiles.value.find(p => p.id === id)
    if (!source) return null
    const name = `${source.name}-copy`
    const draft = { ...source, name, limits: { ...source.limits }, tools: [...source.tools], enabled: false }
    if (isMockMode()) {
      const clone: AgentProfile = {
        ...draft,
        id: `agent-studio-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
        createdAt: new Date().toISOString(),
      }
      profiles.value.push(clone)
      persistLocal()
      toast.success(`Cloned as "${clone.name}"`)
      return clone
    }
    try {
      const created = await createAgentProfileRaw(studioProfileToPayload(draft))
      const clone = backendProfileToStudio(created)
      profiles.value.push(clone)
      toast.success(`Cloned as "${clone.name}"`)
      refreshUsers()
      return clone
    } catch (e) {
      toast.error((e as Error).message)
      return null
    }
  }

  async function toggleEnabled(id: string): Promise<void> {
    const profile = profiles.value.find(p => p.id === id)
    if (!profile) return
    if (isMockMode()) {
      profile.enabled = !profile.enabled
      persistLocal()
      toast.success(`${profile.name} ${profile.enabled ? 'activated' : 'deactivated'}`)
      return
    }
    const next = !profile.enabled
    try {
      await updateAgentProfile(id, { enabled: next })
      profile.enabled = next
      toast.success(`${profile.name} ${next ? 'activated' : 'deactivated'}`)
      refreshUsers()
    } catch (e) {
      toast.error((e as Error).message)
    }
  }

  async function removeProfile(id: string): Promise<void> {
    const profile = profiles.value.find(p => p.id === id)
    if (isMockMode()) {
      profiles.value = profiles.value.filter(p => p.id !== id)
      persistLocal()
      if (profile) toast.success(`Agent "${profile.name}" removed`)
      return
    }
    try {
      await deleteAgentProfile(id)
      profiles.value = profiles.value.filter(p => p.id !== id)
      if (profile) toast.success(`Agent "${profile.name}" removed`)
      refreshUsers()
    } catch (e) {
      toast.error((e as Error).message)
    }
  }

  async function markUsed(id: string): Promise<void> {
    const profile = profiles.value.find(p => p.id === id)
    if (!profile) return
    profile.lastUsedAt = new Date().toISOString()
    if (isMockMode()) {
      persistLocal()
      return
    }
    try {
      await updateAgentProfile(id, { last_used_at: profile.lastUsedAt })
    } catch (e) {
      // The sandbox is local by design: a failed stamp must never break it (#573).
      console.warn('markUsed failed:', e)
    }
  }

  return {
    profiles,
    enabledCount,
    blankProfile,
    loadProfiles,
    saveProfile,
    cloneProfile,
    toggleEnabled,
    removeProfile,
    markUsed,
    syncUsers,
  }
})
