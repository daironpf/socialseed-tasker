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
    // corrupted storage -> fall through to seeds
  }
  return seedProfiles()
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

function seedProfiles(): AgentProfile[] {
  const now = new Date().toISOString()
  return [
    {
      id: 'agent-studio-seed-1',
      name: 'review-sentinel',
      role: 'code-reviewer',
      avatar: '🔍',
      model: 'claude-3.5-sonnet',
      systemPrompt:
        'You are a staff code-reviewer agent. Review diffs for correctness, security and maintainability. Use code_search and test_runner to validate findings, then summarize blockers vs nits with file references.',
      tools: ['code_search', 'fs_read', 'test_runner', 'docs_writer'],
      limits: { maxTokensPerRun: 12000, timeoutSeconds: 180, maxRisk: 'MEDIUM' },
      enabled: true,
      createdAt: now,
    },
    {
      id: 'agent-studio-seed-2',
      name: 'data-guardian',
      role: 'data-engineer',
      avatar: '🛡️',
      model: 'gpt-4o',
      systemPrompt:
        'You are a data pipeline guardian. Monitor Neo4j and warehouse health, run diagnostics with neo4j_query, open fixes via github_pr and never mutate production data without approval.',
      tools: ['neo4j_query', 'fs_read', 'github_pr', 'web_search'],
      limits: { maxTokensPerRun: 6000, timeoutSeconds: 90, maxRisk: 'LOW' },
      enabled: false,
      createdAt: now,
    },
  ]
}
