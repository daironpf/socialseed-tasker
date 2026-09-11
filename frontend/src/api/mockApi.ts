import type { Issue, IssueCreateRequest, Component, ComponentCreateRequest, Policy, ImpactAnalysis, CausalLink, TestFailure } from '@/types'

const MOCK_API_URL = '/mock-api'

// Helper function for API calls
async function apiCall<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${MOCK_API_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  const data = await response.json()
  return data.data || data
}

// Issues API
export async function fetchIssues(
  page = 1,
  limit = 200,
  status?: string,
  _component?: string,
  _project?: string,
): Promise<Issue[]> {
  let url = `/mock/issues?page=${page}&limit=${limit}`
  if (status) url += `&status=${status}`
  return apiCall<Issue[]>(url)
}

export async function fetchIssue(id: string): Promise<Issue> {
  const issues = await fetchIssues()
  const issue = issues.find(i => i.id === id)
  if (!issue) throw new Error('Issue not found')
  return issue
}

export async function createIssue(body: IssueCreateRequest): Promise<Issue> {
  return apiCall<Issue>('/mock/issues', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function updateIssue(id: string, body: any): Promise<Issue> {
  const issues = await fetchIssues()
  const issue = issues.find(i => i.id === id)
  if (!issue) throw new Error('Issue not found')
  return { ...issue, ...body } as Issue
}

export async function deleteIssue(_id: string): Promise<void> {
  // Mock delete
}

export async function closeIssue(id: string): Promise<Issue> {
  const issue = await fetchIssue(id)
  return { ...issue, status: 'CLOSED', closed_at: new Date().toISOString() }
}

export async function fetchBlockedIssues(): Promise<Issue[]> {
  return fetchIssues(1, 200, 'BLOCKED')
}

// Components API
export async function fetchComponents(): Promise<Component[]> {
  return apiCall<Component[]>('/mock/components')
}

export async function fetchComponent(id: string): Promise<Component> {
  const components = await fetchComponents()
  const comp = components.find(c => c.id === id)
  if (!comp) throw new Error('Component not found')
  return comp
}

export async function createComponent(body: ComponentCreateRequest): Promise<Component> {
  return { id: crypto.randomUUID(), ...body, created_at: new Date().toISOString(), updated_at: new Date().toISOString() } as Component
}

export async function updateComponent(id: string, body: Partial<ComponentCreateRequest>): Promise<Component> {
  const comp = await fetchComponent(id)
  return { ...comp, ...body } as Component
}

export async function deleteComponent(_id: string): Promise<void> {
  // Mock delete
}

// Policies API
export async function fetchPolicies(): Promise<Policy[]> {
  return apiCall<Policy[]>('/mock/policies')
}

export async function createPolicy(policy: any): Promise<Policy> {
  return { id: crypto.randomUUID(), ...policy, is_active: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() } as Policy
}

// Users API
export async function fetchUsers() {
  return apiCall<any[]>('/mock/users')
}

export async function updateUser(userId: string, data: any) {
  return apiCall<any>(`/mock/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

// Dashboard Stats API
export async function fetchDashboardStats() {
  return apiCall<any>('/mock/dashboard-stats')
}

// Projects API
export async function fetchProjects() {
  return [{ name: 'socialseed-tasker', slug: 'socialseed-tasker' }]
}

export async function fetchProjectSummary(projectName: string) {
  return {
    name: projectName,
    slug: projectName,
    description: 'Graph-based task management framework',
    total_issues: 100,
    total_components: 5,
  }
}

// Get all issues (for components that need full list)
export function getAllIssues(): Issue[] {
  return []
}

// Get issue stats
export function getIssueStats() {
  return {
    total: 100,
    open: 0,
    in_progress: 0,
    blocked: 0,
    closed: 0,
  }
}

// Analysis API
export async function analyzeImpact(issueId: string): Promise<ImpactAnalysis> {
  return apiCall<ImpactAnalysis>(`/mock/analysis/impact/${issueId}`)
}

export async function analyzeRootCause(body: {
  test_name: string
  error_message: string
  component?: string
  labels?: string[]
}): Promise<CausalLink[]> {
  return apiCall<CausalLink[]>('/mock/analysis/root-cause', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function fetchTestFailures(): Promise<TestFailure[]> {
  return apiCall<TestFailure[]>('/mock/test-failures')
}
