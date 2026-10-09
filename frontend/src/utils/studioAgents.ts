import type { AgentProfile } from '@/types/agentStudio'
import type { User } from '@/types'

const LS_KEY = 'agent-studio-v1'

export function loadStudioProfiles(): AgentProfile[] {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) return parsed as AgentProfile[]
    }
  } catch {
    // corrupted storage -> start empty
  }
  return []
}

export function saveStudioProfiles(profiles: AgentProfile[]): void {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(profiles))
  } catch {
    // storage full/unavailable; keep in-memory copy
  }
}

export function profileToUser(profile: AgentProfile): User {
  return {
    id: profile.id,
    username: profile.name,
    email: `${profile.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.studio@agents.local`,
    role: profile.role,
    type: 'agent',
    avatar: profile.avatar,
    model: profile.model,
    skills: [...profile.tools],
    issues_assigned: 0,
    issues_created: 0,
    last_active: profile.lastUsedAt ?? profile.createdAt,
    is_active: profile.enabled,
    system_prompt: profile.systemPrompt,
  }
}

/** Editable subset of EditAgentModal's emitted form (#567). */
export interface StudioAgentUpdate {
  id: string
  username?: string
  avatar?: string
  model?: string
  system_prompt?: string
  skills?: string[]
  tools?: string[]
}

/**
 * Persist an agent-studio-* edit into localStorage (no network) and return
 * the refreshed card. Throws when the profile no longer exists locally.
 */
export function applyStudioUpdate(data: StudioAgentUpdate): User {
  const profiles = loadStudioProfiles()
  const idx = profiles.findIndex(p => p.id === data.id)
  if (idx === -1) throw new Error('Agent profile not found')
  const current = profiles[idx]
  const merged: AgentProfile = { ...current }
  if (data.username) merged.name = data.username
  if (data.avatar) merged.avatar = data.avatar
  if (data.model) merged.model = data.model
  if (data.system_prompt !== undefined) merged.systemPrompt = data.system_prompt
  if (data.skills || data.tools) {
    // The card maps profile.tools -> skills, so skill edits land back in
    // tools; newly toggled tools are merged in (#567).
    merged.tools = [...new Set([...(data.skills ?? []), ...(data.tools ?? [])])]
  }
  profiles[idx] = merged
  saveStudioProfiles(profiles)
  return profileToUser(merged)
}

export function mergeStudioAgents(users: User[]): User[] {
  const profiles = loadStudioProfiles()
  if (!profiles.length) return users
  const studioIds = new Set(profiles.map(p => p.id))
  const withoutStudio = users.filter(u => !u.id.startsWith('agent-studio-') || studioIds.has(u.id))
  const merged = withoutStudio.map(u => {
    // PG ids are never overwritten by a studio profile (#565): only
    // `agent-studio-*` cards are replaced with their latest local version.
    if (!u.id.startsWith('agent-studio-')) return u
    const profile = profiles.find(p => p.id === u.id)
    return profile ? profileToUser(profile) : u
  })
  const existing = new Set(merged.map(u => u.id))
  for (const profile of profiles) {
    if (!existing.has(profile.id)) merged.push(profileToUser(profile))
  }
  return merged
}
