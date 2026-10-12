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
