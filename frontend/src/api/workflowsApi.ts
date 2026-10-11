import client from './client'
import type { APIResponse } from '@/types'

/** Origin of a workflow definition (issue #575). */
export type WorkflowSource = 'builtin' | 'custom'

/** One row of `GET /workflows/{slug}` (issue #575). */
export interface Workflow {
  slug: string
  name: string
  description?: string | null
  source: WorkflowSource
  created_by?: string | null
  created_at?: string | null
  updated_at?: string | null
  content_md?: string | null
  steps?: unknown[] | Record<string, unknown> | null
}

/** Body of `POST /workflows` (issue #575). */
export interface WorkflowCreatePayload {
  slug: string
  name: string
  description?: string | null
  content_md?: string | null
  steps?: unknown[] | Record<string, unknown> | null
}

/** Body of `PUT /workflows/{slug}` (issue #575); omitted fields keep their value. */
export interface WorkflowUpdatePayload {
  name?: string | null
  description?: string | null
  content_md?: string | null
  steps?: unknown[] | Record<string, unknown> | null
}

export async function fetchWorkflows(source?: WorkflowSource): Promise<Workflow[]> {
  const { data } = await client.get<APIResponse<Workflow[]>>('/workflows', {
    params: source ? { source } : {},
  })
  return data.data ?? []
}

export async function fetchWorkflow(slug: string): Promise<Workflow> {
  const { data } = await client.get<APIResponse<Workflow>>(`/workflows/${encodeURIComponent(slug)}`)
  return data.data as Workflow
}

export async function createWorkflow(payload: WorkflowCreatePayload): Promise<Workflow> {
  const { data } = await client.post<APIResponse<Workflow>>('/workflows', payload)
  return data.data as Workflow
}

export async function updateWorkflow(slug: string, payload: WorkflowUpdatePayload): Promise<Workflow> {
  const { data } = await client.put<APIResponse<Workflow>>(`/workflows/${encodeURIComponent(slug)}`, payload)
  return data.data as Workflow
}

export async function deleteWorkflow(slug: string): Promise<void> {
  await client.delete(`/workflows/${encodeURIComponent(slug)}`)
}
