import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  loadQueue,
  saveQueue,
  createQueueEntry,
  type QueuedMutation,
  type QueueEntity,
  type QueueOperation,
} from '@/utils/offlineQueue'

export type ViewMode = 'board' | 'list'
export type Locale = 'en' | 'es'
export type ConnectionState = 'SYNCED' | 'OFFLINE_QUEUED' | 'SYNCING' | 'DEGRADED'
export type NetworkMode = 'online' | 'degraded' | 'offline'

export interface Filters {
  status: string[]
  priority: string[]
  component: string | null
  project: string | null
  search: string
  assignee: string[]
  labels: string[]
  hasTechDebt: boolean | null
  hasAffectedFiles: boolean | null
  dateFrom: string | null
  dateTo: string | null
  operator: 'AND' | 'OR'
}

export interface SavedSearch {
  id: string
  name: string
  filters: Filters
  createdAt: string
}

export const useUiStore = defineStore('ui', () => {
  const selectedIssueId = ref<string | null>(null)
  const sidebarOpen = ref(true)
  const viewMode = ref<ViewMode>('board')
  const darkMode = ref(false)
  const locale = ref<Locale>((localStorage.getItem('locale') as Locale) || 'en')
  const currentProject = ref(localStorage.getItem('currentProject') || 'socialseed-tasker')
  const connectionState = ref<ConnectionState>('SYNCED')
  const pendingSyncCount = ref(0)
  const networkMode = ref<NetworkMode>((localStorage.getItem('networkMode') as NetworkMode) || 'online')
  const syncQueue = ref<QueuedMutation[]>(loadQueue())
  const filters = ref<Filters>({
    status: [],
    priority: [],
    component: null,
    project: null,
    search: '',
    assignee: [],
    labels: [],
    hasTechDebt: null,
    hasAffectedFiles: null,
    dateFrom: null,
    dateTo: null,
    operator: 'AND',
  })

  const savedSearches = ref<SavedSearch[]>(JSON.parse(localStorage.getItem('savedSearches') || '[]'))

  const availableProjects = ref([
    { id: 'socialseed-tasker', name: 'SocialSeed Tasker', description: 'Main task management platform' },
    { id: 'auth-service', name: 'Auth Service', description: 'Authentication microservice' },
    { id: 'api-gateway', name: 'API Gateway', description: 'Request routing and rate limiting' },
    { id: 'data-pipeline', name: 'Data Pipeline', description: 'ETL and analytics pipeline' },
  ])

  function setSelectedIssue(id: string | null) {
    selectedIssueId.value = id
  }

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function setViewMode(mode: ViewMode) {
    viewMode.value = mode
  }

  function setFilter<K extends keyof Filters>(key: K, value: Filters[K]) {
    filters.value[key] = value
  }

  function clearFilters() {
    filters.value = {
      status: [],
      priority: [],
      component: null,
      project: null,
      search: '',
      assignee: [],
      labels: [],
      hasTechDebt: null,
      hasAffectedFiles: null,
      dateFrom: null,
      dateTo: null,
      operator: 'AND',
    }
  }

  function hasActiveFilters(): boolean {
    const f = filters.value
    return f.status.length > 0 || f.priority.length > 0 || f.component !== null ||
      f.search !== '' || f.assignee.length > 0 || f.labels.length > 0 ||
      f.hasTechDebt !== null || f.hasAffectedFiles !== null ||
      f.dateFrom !== null || f.dateTo !== null
  }

  function saveSearch(name: string) {
    const search: SavedSearch = {
      id: `search-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      name,
      filters: JSON.parse(JSON.stringify(filters.value)),
      createdAt: new Date().toISOString(),
    }
    savedSearches.value.unshift(search)
    if (savedSearches.value.length > 10) {
      savedSearches.value = savedSearches.value.slice(0, 10)
    }
    localStorage.setItem('savedSearches', JSON.stringify(savedSearches.value))
    return search
  }

  function loadSearch(id: string) {
    const search = savedSearches.value.find(s => s.id === id)
    if (search) {
      filters.value = JSON.parse(JSON.stringify(search.filters))
    }
  }

  function deleteSearch(id: string) {
    savedSearches.value = savedSearches.value.filter(s => s.id !== id)
    localStorage.setItem('savedSearches', JSON.stringify(savedSearches.value))
  }

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
    if (darkMode.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('darkMode', String(darkMode.value))
  }

  function initDarkMode() {
    const stored = localStorage.getItem('darkMode')
    if (stored === 'true') {
      darkMode.value = true
      document.documentElement.classList.add('dark')
    } else if (stored === null && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      darkMode.value = true
      document.documentElement.classList.add('dark')
    }
  }

  function setLocale(newLocale: Locale) {
    locale.value = newLocale
    localStorage.setItem('locale', newLocale)
  }

  function setProject(projectId: string) {
    currentProject.value = projectId
    localStorage.setItem('currentProject', projectId)
    filters.value.project = projectId
  }

  let syncTimeout: ReturnType<typeof setTimeout> | null = null
  let flushTimeout: ReturnType<typeof setTimeout> | null = null
  let flushStepTimeout: ReturnType<typeof setTimeout> | null = null

  function simulateSync() {
    if (networkMode.value === 'offline' || syncQueue.value.length > 0 || connectionState.value === 'SYNCING') return
    connectionState.value = 'OFFLINE_QUEUED'
    pendingSyncCount.value += 1

    if (syncTimeout) clearTimeout(syncTimeout)

    syncTimeout = setTimeout(() => {
      connectionState.value = 'SYNCING'
      setTimeout(() => {
        connectionState.value = networkMode.value === 'degraded' ? 'DEGRADED' : 'SYNCED'
        pendingSyncCount.value = 0
      }, 800)
    }, 2000)
  }

  function persistQueue() {
    saveQueue(syncQueue.value)
    pendingSyncCount.value = syncQueue.value.length
  }

  function setNetworkMode(mode: NetworkMode) {
    networkMode.value = mode
    localStorage.setItem('networkMode', mode)
    if (flushTimeout) {
      clearTimeout(flushTimeout)
      flushTimeout = null
    }
    if (mode === 'online') {
      if (syncQueue.value.length) {
        flushQueue()
      } else {
        connectionState.value = 'SYNCED'
        pendingSyncCount.value = 0
      }
    } else if (mode === 'degraded') {
      connectionState.value = syncQueue.value.length ? 'OFFLINE_QUEUED' : 'DEGRADED'
    } else {
      connectionState.value = syncQueue.value.length ? 'OFFLINE_QUEUED' : 'SYNCED'
    }
  }

  function enqueueMutation(input: {
    entity: QueueEntity
    operation: QueueOperation
    entityId?: string | null
    payload: Record<string, unknown>
  }): QueuedMutation {
    const conflict =
      input.operation === 'update' &&
      (networkMode.value === 'degraded' ||
        syncQueue.value.some(e => e.operation === 'update' && e.entityId === input.entityId))
    const entry = createQueueEntry({ ...input, conflict })
    syncQueue.value.push(entry)
    persistQueue()
    connectionState.value = 'OFFLINE_QUEUED'
    return entry
  }

  function removeQueued(id: string) {
    syncQueue.value = syncQueue.value.filter(e => e.id !== id)
    persistQueue()
    if (!syncQueue.value.length && connectionState.value === 'OFFLINE_QUEUED') {
      connectionState.value = networkMode.value === 'degraded' ? 'DEGRADED' : 'SYNCED'
    }
  }

  function retryQueued(id: string) {
    const entry = syncQueue.value.find(e => e.id === id)
    if (entry) {
      entry.retries += 1
      persistQueue()
    }
  }

  function resolveConflict(id: string) {
    removeQueued(id)
  }

  function flushQueue() {
    if (!syncQueue.value.length) {
      connectionState.value = networkMode.value === 'degraded' ? 'DEGRADED' : 'SYNCED'
      pendingSyncCount.value = 0
      return
    }
    if (flushTimeout || flushStepTimeout) return
    connectionState.value = 'OFFLINE_QUEUED'
    flushTimeout = setTimeout(() => {
      flushTimeout = null
      connectionState.value = 'SYNCING'
      flushStepTimeout = setTimeout(() => {
        flushStepTimeout = null
        syncQueue.value = syncQueue.value.filter(e => e.status === 'conflict')
        persistQueue()
        if (syncQueue.value.length) {
          connectionState.value = 'OFFLINE_QUEUED'
        } else {
          connectionState.value = networkMode.value === 'degraded' ? 'DEGRADED' : 'SYNCED'
        }
      }, 900)
    }, 400)
  }

  if (syncQueue.value.length) {
    pendingSyncCount.value = syncQueue.value.length
    connectionState.value = 'OFFLINE_QUEUED'
    if (networkMode.value === 'online') {
      setTimeout(() => flushQueue(), 600)
    }
  } else if (networkMode.value === 'degraded') {
    connectionState.value = 'DEGRADED'
  } else if (networkMode.value === 'offline') {
    connectionState.value = 'SYNCED'
  }

  function getBackendFilters() {
    return {
      status: filters.value.status.length > 0 ? filters.value.status.join(',') : undefined,
      priority: filters.value.priority.length > 0 ? filters.value.priority.join(',') : undefined,
      component: filters.value.component || undefined,
      project: filters.value.project || undefined,
    }
  }

  return {
    selectedIssueId,
    sidebarOpen,
    viewMode,
    darkMode,
    locale,
    currentProject,
    availableProjects,
    filters,
    savedSearches,
    connectionState,
    pendingSyncCount,
    networkMode,
    syncQueue,
    setSelectedIssue,
    toggleSidebar,
    setViewMode,
    setFilter,
    clearFilters,
    hasActiveFilters,
    saveSearch,
    loadSearch,
    deleteSearch,
    toggleDarkMode,
    initDarkMode,
    setLocale,
    setProject,
    simulateSync,
    setNetworkMode,
    enqueueMutation,
    removeQueued,
    retryQueued,
    resolveConflict,
    flushQueue,
    getBackendFilters,
  }
})
