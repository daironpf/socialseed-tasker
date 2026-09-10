import type { Issue, IssueCreateRequest, IssueUpdateRequest, Component, ComponentCreateRequest, Policy } from '@/types'

// Import mock data
import issuesData from '../../../dataset-de-pruebas/issues.json'
import componentsData from '../../../dataset-de-pruebas/components.json'
import policiesData from '../../../dataset-de-pruebas/policies.json'

// Clone data for mutable operations
let issues: Issue[] = issuesData.issues as unknown as Issue[]
let components: Component[] = componentsData.components as unknown as Component[]
let policies: Policy[] = policiesData.policies as unknown as Policy[]

// Simulate network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// Issues API
export async function fetchIssues(
  page = 1,
  limit = 50,
  status?: string,
  _component?: string,
  _project?: string,
): Promise<Issue[]> {
  await delay(100)
  
  let filtered = [...issues]
  
  if (status) {
    filtered = filtered.filter(i => i.status === status)
  }
  
  const start = (page - 1) * limit
  const end = start + limit
  
  return filtered.slice(start, end)
}

export async function fetchIssue(id: string): Promise<Issue> {
  await delay(50)
  const issue = issues.find(i => i.id === id)
  if (!issue) throw new Error('Issue not found')
  return issue
}

export async function createIssue(body: IssueCreateRequest): Promise<Issue> {
  await delay(200)
  
  const newIssue: Issue = {
    id: `ISS-${String(issues.length + 1).padStart(3, '0')}`,
    title: body.title,
    description: body.description || '',
    status: 'OPEN',
    priority: body.priority || 'MEDIUM',
    component_id: body.component_id,
    labels: body.labels || [],
    dependencies: [],
    blocks: [],
    affects: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    closed_at: null,
    architectural_constraints: body.architectural_constraints || [],
    agent_working: false,
  }
  
  issues.unshift(newIssue)
  return newIssue
}

export async function updateIssue(id: string, body: IssueUpdateRequest): Promise<Issue> {
  await delay(150)
  
  const idx = issues.findIndex(i => i.id === id)
  if (idx === -1) throw new Error('Issue not found')
  
  issues[idx] = {
    ...issues[idx],
    ...body,
    updated_at: new Date().toISOString(),
  }
  
  return issues[idx]
}

export async function deleteIssue(id: string): Promise<void> {
  await delay(100)
  issues = issues.filter(i => i.id !== id)
}

export async function closeIssue(id: string): Promise<Issue> {
  await delay(150)
  
  const idx = issues.findIndex(i => i.id === id)
  if (idx === -1) throw new Error('Issue not found')
  
  issues[idx] = {
    ...issues[idx],
    status: 'CLOSED',
    closed_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  
  return issues[idx]
}

export async function fetchBlockedIssues(): Promise<Issue[]> {
  await delay(100)
  return issues.filter(i => i.status === 'BLOCKED')
}

// Components API
export async function fetchComponents(): Promise<Component[]> {
  await delay(100)
  return components
}

export async function fetchComponent(id: string): Promise<Component> {
  await delay(50)
  const comp = components.find(c => c.id === id)
  if (!comp) throw new Error('Component not found')
  return comp
}

export async function createComponent(body: ComponentCreateRequest): Promise<Component> {
  await delay(200)
  
  const newComp: Component = {
    id: `550e8400-e29b-41d4-a716-${String(Date.now()).padStart(12, '0')}`,
    name: body.name,
    description: body.description || null,
    project: body.project,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  
  components.push(newComp)
  return newComp
}

export async function updateComponent(id: string, body: Partial<ComponentCreateRequest>): Promise<Component> {
  await delay(150)
  
  const idx = components.findIndex(c => c.id === id)
  if (idx === -1) throw new Error('Component not found')
  
  components[idx] = {
    ...components[idx],
    ...body,
    updated_at: new Date().toISOString(),
  }
  
  return components[idx]
}

export async function deleteComponent(id: string): Promise<void> {
  await delay(100)
  components = components.filter(c => c.id !== id)
}

// Policies API
export async function fetchPolicies(): Promise<Policy[]> {
  await delay(100)
  return policies
}

export async function createPolicy(policy: any): Promise<Policy> {
  await delay(200)
  
  const newPolicy: Policy = {
    id: `550e8400-e29b-41d4-a716-${String(Date.now()).padStart(12, '0')}`,
    name: policy.name,
    description: policy.description || '',
    rules: policy.rules || [],
    target_scope: policy.target_scope || 'project',
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  
  policies.push(newPolicy)
  return newPolicy
}

// Dashboard Stats API
export async function fetchDashboardStats() {
  await delay(100)
  
  const statsData = {
    total_issues: issues.length,
    open_issues: issues.filter(i => i.status === 'OPEN').length,
    in_progress_issues: issues.filter(i => i.status === 'IN_PROGRESS').length,
    blocked_issues: issues.filter(i => i.status === 'BLOCKED').length,
    closed_issues: issues.filter(i => i.status === 'CLOSED').length,
    total_components: components.length,
    total_policies: policies.length,
    active_policies: policies.filter(p => p.is_active).length,
  }
  
  return statsData
}

// Projects API
export async function fetchProjects() {
  await delay(50)
  return [{ name: 'socialseed-tasker', slug: 'socialseed-tasker' }]
}

export async function fetchProjectSummary(projectName: string) {
  await delay(100)
  return {
    name: projectName,
    slug: projectName,
    description: 'Graph-based task management framework',
    total_issues: issues.length,
    total_components: components.length,
  }
}

// Users API
export async function fetchUsers() {
  await delay(50)
  return [
    { id: 'human-001', username: 'pedro', email: 'pedro@socialseed.com', role: 'lead-developer' },
    { id: 'human-002', username: 'juan', email: 'juan@socialseed.com', role: 'developer' },
    { id: 'human-003', username: 'manolo', email: 'manolo@socialseed.com', role: 'developer' },
  ]
}

// Get all issues (for components that need full list)
export function getAllIssues(): Issue[] {
  return issues
}

// Get issue stats
export function getIssueStats() {
  return {
    total: issues.length,
    open: issues.filter(i => i.status === 'OPEN').length,
    in_progress: issues.filter(i => i.status === 'IN_PROGRESS').length,
    blocked: issues.filter(i => i.status === 'BLOCKED').length,
    closed: issues.filter(i => i.status === 'CLOSED').length,
  }
}
