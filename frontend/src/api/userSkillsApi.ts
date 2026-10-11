import client from './client'
import type { APIResponse } from '@/types'

/** One user↔skill assignment from `GET /users/{id}/skills` (issue #576). */
export interface UserSkill {
  user_id: string
  skill_id: string
  name: string
}

export async function fetchUserSkills(userId: string): Promise<UserSkill[]> {
  const { data } = await client.get<APIResponse<UserSkill[]>>(`/users/${encodeURIComponent(userId)}/skills`)
  return data.data ?? []
}

/** Find-or-create the catalog skill by name and link it to the user (issue #576). */
export async function addUserSkill(userId: string, name: string): Promise<UserSkill> {
  const { data } = await client.post<APIResponse<UserSkill>>(`/users/${encodeURIComponent(userId)}/skills`, { name })
  return data.data as UserSkill
}

/** Unlink one skill; the catalog entry is kept (issue #576). */
export async function removeUserSkill(userId: string, skillId: string): Promise<void> {
  await client.delete(`/users/${encodeURIComponent(userId)}/skills/${encodeURIComponent(skillId)}`)
}
