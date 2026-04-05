import client from './client'
import type { APIResponse, Component, ComponentCreateRequest } from '@/types'

export async function fetchComponents(project?: string): Promise<Component[]> {
  const params: Record<string, string> = {}
  if (project) params.project = project
  const { data } = await client.get<APIResponse<Component[]>>('/components', { params })
  return data.data ?? []
}

export async function fetchComponent(id: string): Promise<Component> {
  const { data } = await client.get<APIResponse<Component>>(`/components/${id}`)
  if (!data.data) throw new Error('Component not found')
  return data.data
}

export async function createComponent(body: ComponentCreateRequest): Promise<Component> {
  const { data } = await client.post<APIResponse<Component>>('/components', body)
  if (!data.data) throw new Error('Failed to create component')
  return data.data
}

export async function updateComponent(
  id: string,
  body: Partial<ComponentCreateRequest>,
): Promise<Component> {
  const { data } = await client.patch<APIResponse<Component>>(`/components/${id}`, body)
  if (!data.data) throw new Error('Failed to update component')
  return data.data
}

export async function deleteComponent(id: string, force = false): Promise<void> {
  await client.delete(`/components/${id}`, { params: { force } })
}
