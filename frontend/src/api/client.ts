import axios, { AxiosInstance } from 'axios'
import { ref } from 'vue'
import * as mockApi from './mockApi'
import { useToast } from '@/composables/useToast'
import { getAccessToken } from './authSession'
import { refresh } from './authApi'

// API mode: mock (default) or real FastAPI backend (issue #517).
// Resolution order: localStorage override > VITE_USE_MOCK env flag > mock.
export type ApiMode = 'mock' | 'real'

const env = import.meta.env as unknown as Record<string, string | undefined>
const envMock = (env.VITE_USE_MOCK ?? 'true') !== 'false'
const storedMode = localStorage.getItem('socialseed-api-mode')

export const apiMode = ref<ApiMode>(
  storedMode === 'real' || storedMode === 'mock'
    ? storedMode
    : envMock
      ? 'mock'
      : 'real',
)

export function isMockMode(): boolean {
  return apiMode.value === 'mock'
}

export function setApiMode(mode: ApiMode): void {
  apiMode.value = mode
  localStorage.setItem('socialseed-api-mode', mode)
}

const API_URL =
  (window as unknown as { __API_URL__?: string }).__API_URL__ || env.VITE_API_URL || '/api/v1'
const API_KEY = (window as unknown as { __API_KEY__?: string }).__API_KEY__ || ''

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
    if (url.match(/\/issues\/[^/]+\/github-sync\/resolve$/)) {
      const id = url.split('/')[2]
      const data = await mockApi.resolveGithubConflict(id, body?.resolution, body?.fields)
      return { data: { data } }
    }
    if (url.match(/\/issues\/[^/]+\/github-sync$/)) {
      const id = url.split('/')[2]
      const data = await mockApi.resyncGithubIssue(id)
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

// Attach the short-lived JWT when a session exists (issue #519).
realClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token && !(config.url || '').startsWith('/auth/')) {
    config.headers = config.headers ?? {}
    ;(config.headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }
  return config
})

realClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const message =
      error.response?.data?.error?.message ||
      error.response?.data?.detail ||
      error.message ||
      'Unknown error occurred'
    const original = error.config as
      | ({ url?: string; __retried?: boolean } & Record<string, unknown>)
      | undefined
    const isAuthPath = (original?.url || '').startsWith('/auth/')

    // Expired access token: rotate the refresh token once and retry (issue #519).
    if (error.response?.status === 401 && original && !isAuthPath && !original.__retried) {
      original.__retried = true
      const renewed = await refresh()
      if (renewed) {
        return realClient(original as never)
      }
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
      return Promise.reject(new Error(message))
    }

    if (error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    } else if (error.response?.status >= 400) {
      useToast().error(message)
    }
    return Promise.reject(new Error(message))
  },
)

// Dynamic client: dispatches each call to the mock or real client based on
// the reactive `apiMode`, so the mode can be switched at runtime (issue #517)
const client = {
  defaults: realClient.defaults,
  interceptors: realClient.interceptors,
  get: (url: string, config?: any) => pickClient().get(url, config),
  post: (url: string, body?: any, config?: any) => pickClient().post(url, body, config),
  put: (url: string, body?: any, config?: any) => pickClient().put(url, body, config),
  patch: (url: string, body?: any, config?: any) => pickClient().patch(url, body, config),
  delete: (url: string, config?: any) => pickClient().delete(url, config),
} as unknown as AxiosInstance

function pickClient(): AxiosInstance {
  return isMockMode() ? mockClient : realClient
}

export default client
export { API_KEY, API_URL }

declare global {
  interface Window {
    __API_URL__?: string
    __API_KEY__?: string
  }
}
