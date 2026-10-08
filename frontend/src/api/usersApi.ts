import client from './client'
import type { APIResponse, User } from '@/types'
import { mergeStudioAgents } from '@/utils/studioAgents'

type BackendUser = Partial<User> & {
  email?: string | null
  role?: string | null
  created_at?: string | null
  last_login?: string | null
}

function normalizeBackendUser(raw: BackendUser): User {
  const type = raw.type || 'human'
  return {
    id: raw.id ?? '',
    username: raw.username ?? '',
    email: raw.email ?? '',
    role: raw.role ?? (type === 'agent' ? 'ai-agent' : 'DEVELOPER'),
    type,
    avatar: raw.avatar || '👤',
    model: raw.model,
    skills: raw.skills ?? [],
    issues_assigned: raw.issues_assigned ?? 0,
    issues_created: raw.issues_created ?? 0,
    last_active: raw.last_active ?? raw.last_login ?? raw.created_at ?? new Date(0).toISOString(),
    specialization: raw.specialization,
    is_active: raw.is_active ?? true,
  }
}

export async function fetchUsers(): Promise<User[]> {
  const { data } = await client.get<APIResponse<BackendUser[]>>('/users')
  return mergeStudioAgents((data.data || []).map(normalizeBackendUser))
}

export async function updateUser(userId: string, userData: Partial<User>): Promise<User> {
  // The view translates 409/422 itself, so the generic interceptor toast is muted.
  const { data } = await client.put<APIResponse<BackendUser>>(`/users/${userId}`, userData, {
    suppressErrorToast: true,
  })
  if (!data.data) throw new Error('Failed to update user')
  return normalizeBackendUser(data.data)
}

export interface UserCreateRequest {
  username: string
  email: string
  role?: string
  type?: string
  avatar?: string
  skills?: string[]
  specialization?: string
}

export interface CreateUserResult {
  user: User
  temporaryPassword: string | null
}

export async function createUser(userData: UserCreateRequest): Promise<CreateUserResult> {
  // The view translates 409/422 itself, so the generic interceptor toast is muted.
  const { data } = await client.post<APIResponse<BackendUser & { temporary_password?: string | null }>>(
    '/users',
    userData,
    { suppressErrorToast: true },
  )
  if (!data.data) throw new Error('Failed to create user')
  return {
    user: normalizeBackendUser(data.data),
    temporaryPassword: data.data.temporary_password ?? null,
  }
}

export async function deleteUser(userId: string): Promise<void> {
  // The view shows the backend detail itself, so the generic interceptor toast is muted (#562).
  await client.delete(`/users/${userId}`, { suppressErrorToast: true })
}
