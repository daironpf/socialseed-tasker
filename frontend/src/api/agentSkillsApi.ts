import client from './client'
import type { APIResponse } from '@/types'

/** One row of `GET /agent-skills` (issue #577): `behavior` is the large adoption prompt. */
export interface AgentSkill {
  id: string
  name: string
  behavior: string
}

/** Catalog of agent skills (separate from the human `GET /skills`, issue #577). */
export async function fetchAgentSkills(): Promise<AgentSkill[]> {
  const { data } = await client.get<APIResponse<AgentSkill[]>>('/agent-skills', {
    suppressErrorToast: true,
  })
  return data.data ?? []
}

/** Create an agent skill (name + large behavior text) from the picker (#577). */
export async function createAgentSkill(name: string, behavior: string): Promise<AgentSkill> {
  const { data } = await client.post<APIResponse<AgentSkill>>('/agent-skills', { name, behavior })
  return data.data as AgentSkill
}

/** Rename/rewrite one catalog row; 409 when the new name collides (#610). */
export async function updateAgentSkill(
  id: string,
  patch: { name?: string; behavior?: string },
): Promise<AgentSkill> {
  const { data } = await client.put<APIResponse<AgentSkill>>(`/agent-skills/${id}`, patch)
  return data.data as AgentSkill
}

/** Delete one catalog row (assignments cascade); 404 when unknown (#610). */
export async function deleteAgentSkill(id: string): Promise<void> {
  await client.delete<APIResponse<boolean>>(`/agent-skills/${id}`)
}

/** Upload one .md file; name from the first '# heading' (or the file stem) (#610). */
export async function importAgentSkill(file: File): Promise<AgentSkill> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post<APIResponse<AgentSkill>>('/agent-skills/import', form, {
    suppressErrorToast: true,
  })
  return data.data as AgentSkill
}

/** Import from a GitHub URL (github.com blob or raw.githubusercontent.com) (#610). */
export async function importAgentSkillFromUrl(url: string): Promise<AgentSkill> {
  const { data } = await client.post<APIResponse<AgentSkill>>(
    '/agent-skills/import-url',
    { url },
    { suppressErrorToast: true },
  )
  return data.data as AgentSkill
}
