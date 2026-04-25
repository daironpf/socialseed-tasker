import client from './client'
import type { APIResponse, Component, ComponentCreateRequest, PaginatedResponse } from '@/types'

export async function fetchComponents(project?: string): Promise<Component[]> {
  const params: Record<string, string> = {}
  if (project) params.project = project
  const { data } = await client.get<APIResponse<PaginatedResponse<Component>>>('/components', { params })
  // Handle both paginated and non-paginated responses
  const responseData = data.data
  if (Array.isArray(responseData)) {
    return responseData // Direct array response
  }
  return responseData?.items ?? []
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
