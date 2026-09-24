import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useToast } from '@/composables/useToast'
import { useUsersStore } from '@/stores/usersStore'
import type { AgentProfile } from '@/types/agentStudio'
import { DEFAULT_LIMITS } from '@/types/agentStudio'
import {
  loadStudioProfiles,
  saveStudioProfiles,
  profileToUser,
} from '@/utils/studioAgents'

export const useAgentStudioStore = defineStore('agentStudio', () => {
  const toast = useToast()
  const usersStore = useUsersStore()

  const profiles = ref<AgentProfile[]>(loadStudioProfiles())

  const enabledCount = computed(() => profiles.value.filter(p => p.enabled).length)

  function persist() {
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

  function saveProfile(input: Omit<AgentProfile, 'id' | 'createdAt'>, existingId?: string): AgentProfile | null {
    const name = input.name.trim()
    if (!name) {
      toast.error('Agent name is required')
      return null
    }
    if (existingId) {
      const idx = profiles.value.findIndex(p => p.id === existingId)
      if (idx < 0) return null
      profiles.value[idx] = { ...profiles.value[idx], ...input, name }
      persist()
      toast.success(`Agent "${name}" updated`)
      return profiles.value[idx]
    }
    const profile: AgentProfile = {
      ...input,
      name,
      id: `agent-studio-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
      createdAt: new Date().toISOString(),
    }
    profiles.value.push(profile)
    persist()
    toast.success(`Agent "${name}" saved to library`)
    return profile
  }

  function cloneProfile(id: string): AgentProfile | null {
    const source = profiles.value.find(p => p.id === id)
    if (!source) return null
    const clone: AgentProfile = {
      ...source,
      limits: { ...source.limits },
      tools: [...source.tools],
      id: `agent-studio-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
      name: `${source.name}-copy`,
      enabled: false,
      createdAt: new Date().toISOString(),
    }
    profiles.value.push(clone)
    persist()
    toast.success(`Cloned as "${clone.name}"`)
    return clone
  }

  function toggleEnabled(id: string) {
    const profile = profiles.value.find(p => p.id === id)
    if (!profile) return
    profile.enabled = !profile.enabled
    persist()
    toast.success(`${profile.name} ${profile.enabled ? 'activated' : 'deactivated'}`)
  }

  function removeProfile(id: string) {
    const profile = profiles.value.find(p => p.id === id)
    profiles.value = profiles.value.filter(p => p.id !== id)
    persist()
    if (profile) toast.success(`Agent "${profile.name}" removed`)
  }

  function markUsed(id: string) {
    const profile = profiles.value.find(p => p.id === id)
    if (!profile) return
    profile.lastUsedAt = new Date().toISOString()
    persist()
  }

  return {
    profiles,
    enabledCount,
    blankProfile,
    saveProfile,
    cloneProfile,
    toggleEnabled,
    removeProfile,
    markUsed,
    syncUsers,
  }
})
