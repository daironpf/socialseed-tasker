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
  }
}

export function mergeStudioAgents(users: User[]): User[] {
  const profiles = loadStudioProfiles()
  if (!profiles.length) return users
  const studioIds = new Set(profiles.map(p => p.id))
  const withoutStudio = users.filter(u => !u.id.startsWith('agent-studio-') || studioIds.has(u.id))
  const merged = withoutStudio.map(u => {
    const profile = profiles.find(p => p.id === u.id)
    return profile ? profileToUser(profile) : u
  })
  const existing = new Set(merged.map(u => u.id))
  for (const profile of profiles) {
    if (!existing.has(profile.id)) merged.push(profileToUser(profile))
  }
  return merged
}
