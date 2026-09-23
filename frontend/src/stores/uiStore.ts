import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ViewMode = 'board' | 'list'
export type Locale = 'en' | 'es'
export type ConnectionState = 'SYNCED' | 'OFFLINE_QUEUED' | 'SYNCING'

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

  function simulateSync() {
    connectionState.value = 'OFFLINE_QUEUED'
    pendingSyncCount.value += 1

    if (syncTimeout) clearTimeout(syncTimeout)

    syncTimeout = setTimeout(() => {
      connectionState.value = 'SYNCING'
      setTimeout(() => {
        connectionState.value = 'SYNCED'
        pendingSyncCount.value = 0
      }, 800)
    }, 2000)
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
    getBackendFilters,
  }
})
