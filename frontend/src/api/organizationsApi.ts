import type { Organization, OrganizationCreateRequest } from '@/types/organizations'

const MOCK_API_URL = '/mock-api'

async function apiCall<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${MOCK_API_URL}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  const data = await response.json()
  return data.data || data
}

export async function fetchOrganizations(): Promise<Organization[]> {
  return apiCall<Organization[]>('/mock/organizations')
}

export async function fetchOrganization(id: string): Promise<Organization> {
  return apiCall<Organization>(`/mock/organizations/${id}`)
}

export async function createOrganization(body: OrganizationCreateRequest): Promise<Organization> {
  return apiCall<Organization>('/mock/organizations', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function updateOrganization(
  id: string,
  body: Partial<Organization>,
): Promise<Organization> {
  return apiCall<Organization>(`/mock/organizations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export async function deleteOrganization(id: string): Promise<void> {
  await apiCall(`/mock/organizations/${id}`, { method: 'DELETE' })
}
