import client from './client'
import type { APIResponse, User } from '@/types'

/** Backend payload of `GET/POST/PUT /agents/profiles` (issue #564). */
export interface BackendAgentProfile {
  id: string
  username: string
  email?: string | null
  role?: string | null
  type?: string
  avatar?: string | null
  model?: string | null
  specialization?: string | null
  temperature?: number | null
  system_prompt?: string | null
  tools?: string[]
  write_access?: string[]
  limits?: Record<string, unknown> | null
  enabled?: boolean
  skills?: string[]
  created_at?: string | null
  last_used_at?: string | null
}

/** Snake_case payload accepted by the endpoint (EditAgentModal maps to this, #567). */
export interface AgentProfilePayload {
  username?: string
  email?: string | null
  avatar?: string | null
  model?: string | null
  specialization?: string | null
  temperature?: number | null
  system_prompt?: string | null
  tools?: string[]
  write_access?: string[]
  limits?: Record<string, unknown> | null
  skills?: string[]
  enabled?: boolean
}

/**
 * Convert a PG agent profile into the card `User` shape (issue #565):
 * `role` is always null for agents (no RBAC role, #558) so it is derived as
 * `'ai-agent'`, and `enabled` maps onto `is_active`.
 */
export function normalizeAgentProfile(raw: BackendAgentProfile): User {
  return {
    id: raw.id,
    username: raw.username ?? '',
    email: raw.email ?? '',
    role: raw.role ?? 'ai-agent',
    type: 'agent',
    avatar: raw.avatar || '🤖',
    model: raw.model ?? undefined,
    skills: raw.skills ?? [],
    issues_assigned: 0,
    issues_created: 0,
    last_active: raw.last_used_at ?? raw.created_at ?? new Date(0).toISOString(),
    specialization: raw.specialization ?? undefined,
    is_active: raw.enabled ?? true,
  }
}

export async function fetchAgentProfiles(): Promise<User[]> {
  // The store degrades to humans-only on failure, so no global error toast (#565).
  const { data } = await client.get<APIResponse<BackendAgentProfile[]>>('/agents/profiles', {
    suppressErrorToast: true,
  })
  return (data.data || []).map(normalizeAgentProfile)
}

export async function createAgentProfile(payload: AgentProfilePayload): Promise<User> {
  const { data } = await client.post<APIResponse<BackendAgentProfile>>('/agents/profiles', payload, {
    suppressErrorToast: true,
  })
  if (!data.data) throw new Error('Failed to create agent profile')
  return normalizeAgentProfile(data.data)
}

export async function updateAgentProfile(id: string, payload: AgentProfilePayload): Promise<User> {
  const { data } = await client.put<APIResponse<BackendAgentProfile>>(
    `/agents/profiles/${id}`,
    payload,
    { suppressErrorToast: true },
  )
  if (!data.data) throw new Error('Failed to update agent profile')
  return normalizeAgentProfile(data.data)
}

export async function deleteAgentProfile(id: string): Promise<void> {
  await client.delete(`/agents/profiles/${id}`, { suppressErrorToast: true })
}
