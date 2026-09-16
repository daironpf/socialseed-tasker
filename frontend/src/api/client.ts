import axios, { AxiosInstance } from 'axios'
import * as mockApi from './mockApi'
import { useToast } from '@/composables/useToast'

// Mock mode flag - set to true to use mock data
const USE_MOCK = true

const API_URL = (window as any).__API_URL__ || '/api/v1'
const API_KEY = (window as any).__API_KEY__ || ''

// Mock client that intercepts requests
const mockClient = {
  defaults: {
    headers: {
      common: {} as Record<string, string>,
    },
  },
  interceptors: {
    request: { use: () => {}, eject: () => {} },
    response: {
      use: (_success: any, _error: any) => {},
      eject: () => {},
    },
  },
  get: async (url: string, config?: any) => {
    const params = config?.params || {}
    
    // Route to appropriate mock handler
    if (url === '/issues') {
      const data = await mockApi.fetchIssues(params.page, params.limit, params.status, params.component, params.project, params.priority)
      return { data: { data, meta: { total: data.length } } }
    }
    if (url.match(/\/issues\/[^/]+\/agent-logs$/)) {
      const issueId = url.split('/')[2]
      const data = await mockApi.fetchAgentLogs(issueId)
      return { data: { data } }
    }
    if (url === '/health') {
      const data = await mockApi.fetchSystemHealth()
      return { data: { data } }
    }
    if (url === '/sync-queue') {
      const data = await mockApi.fetchSyncQueue()
      return { data: { data } }
    }
    if (url.match(/\/issues\/[^/]+$/)) {
      const id = url.split('/').pop()!
      const data = await mockApi.fetchIssue(id)
      return { data: { data } }
    }
    if (url === '/blocked-issues') {
      const data = await mockApi.fetchBlockedIssues()
      return { data: { data } }
    }
    if (url === '/components') {
      const data = await mockApi.fetchComponents()
      return { data: { data } }
    }
    if (url === '/policies') {
      const data = await mockApi.fetchPolicies()
      return { data: { data } }
    }
    if (url === '/projects') {
      const data = await mockApi.fetchProjects()
      return { data: { data } }
    }
    if (url.match(/\/projects\/[^/]+\/summary$/)) {
      const projectName = url.split('/')[2]
      const data = await mockApi.fetchProjectSummary(projectName)
      return { data: { data } }
    }
    if (url === '/users') {
      const data = await mockApi.fetchUsers()
      return { data: { data } }
    }
    if (url === '/constraints') {
      const data = await mockApi.fetchConstraints()
      return { data: { data } }
    }
    if (url === '/test-failures') {
      const data = await mockApi.fetchTestFailures()
      return { data: { data } }
    }
    if (url.match(/\/analysis\/impact\/[^/]+$/)) {
      const issueId = url.split('/').pop()!
      const data = await mockApi.analyzeImpact(issueId)
      return { data: { data } }
    }
    
    return { data: { data: null } }
  },
  post: async (url: string, body?: any) => {
    if (url === '/issues') {
      const data = await mockApi.createIssue(body)
      return { data: { data } }
    }
    if (url.match(/\/issues\/[^/]+\/close$/)) {
      const id = url.split('/')[2]
      const data = await mockApi.closeIssue(id)
      return { data: { data } }
    }
    if (url === '/users') {
      const data = await mockApi.createUser(body)
      return { data: { data } }
    }
    if (url === '/components') {
      const data = await mockApi.createComponent(body)
      return { data: { data } }
    }
    if (url === '/policies') {
      const data = await mockApi.createPolicy(body)
      return { data: { data } }
    }
    if (url === '/constraints') {
      const data = await mockApi.createConstraint(body)
      return { data: { data } }
    }
    if (url === '/admin/seed') {
      const data = await mockApi.adminSeed(body?.seed_type, body?.reset_first)
      return { data: { data } }
    }
    if (url === '/admin/reset') {
      const data = await mockApi.adminReset()
      return { data: { data } }
    }
    if (url === '/constraints/validate') {
      const data = await mockApi.validateConstraints(body.entity_type, body.entity_data)
      return { data: { data } }
    }
    if (url === '/analysis/root-cause') {
      const data = await mockApi.analyzeRootCause(body)
      return { data: { data } }
    }
    if (url === '/test-failures') {
      const data = await mockApi.fetchTestFailures()
      return { data: { data } }
    }
    
    return { data: { data: null } }
  },
  put: async (url: string, body?: any) => {
    if (url.match(/\/users\/[^/]+$/)) {
      const id = url.split('/').pop()!
      const data = await mockApi.updateUser(id, body)
      return { data: { data } }
    }
    return { data: { data: null } }
  },
  patch: async (url: string, body?: any) => {
    if (url.match(/\/issues\/[^/]+$/)) {
      const id = url.split('/').pop()!
      const data = await mockApi.updateIssue(id, body)
      return { data: { data } }
    }
    if (url.match(/\/components\/[^/]+$/)) {
      const id = url.split('/').pop()!
      const data = await mockApi.updateComponent(id, body)
      return { data: { data } }
    }
    if (url.match(/\/constraints\/[^/]+$/)) {
      const id = url.split('/').pop()!
      const data = await mockApi.updateConstraint(id, body)
      return { data: { data } }
    }
    if (url.match(/\/policies\/[^/]+$/)) {
      const id = url.split('/').pop()!
      const data = await mockApi.updatePolicy(id, body)
      return { data: { data } }
    }
    
    return { data: { data: null } }
  },
  delete: async (url: string, _config?: any) => {
    if (url.match(/\/issues\/[^/]+$/)) {
      const id = url.split('/').pop()!
      await mockApi.deleteIssue(id)
    }
    if (url.match(/\/components\/[^/]+$/)) {
      const id = url.split('/').pop()!
      await mockApi.deleteComponent(id)
    }
    if (url.match(/\/policies\/[^/]+$/)) {
      const id = url.split('/').pop()!
      await mockApi.deletePolicy(id)
    }
    if (url.match(/\/users\/[^/]+$/)) {
      const id = url.split('/').pop()!
      await mockApi.deleteUser(id)
    }
    if (url.match(/\/constraints\/[^/]+$/)) {
      const id = url.split('/').pop()!
      await mockApi.deleteConstraint(id)
    }
    
    return { data: {} }
  },
} as unknown as AxiosInstance

// Real API client
const realClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
  },
})

if (API_KEY) {
  realClient.defaults.headers.common['X-API-Key'] = API_KEY
}

realClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.error?.message ||
      error.response?.data?.detail ||
      error.message ||
      'Unknown error occurred'
    if (error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    } else if (error.response?.status >= 400) {
      useToast().error(message)
    }
    return Promise.reject(new Error(message))
  },
)

// Export based on mock mode
const client = USE_MOCK ? mockClient : realClient

export default client
export { API_KEY, USE_MOCK }

declare global {
  interface Window {
    __API_URL__?: string
    __API_KEY__?: string
  }
}
