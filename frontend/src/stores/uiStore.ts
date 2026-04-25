import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ViewMode = 'board' | 'list'

export interface Filters {
  status: string[]
  priority: string[]
  component: string | null
  project: string | null
  search: string
}

export const useUiStore = defineStore('ui', () => {
  const selectedIssueId = ref<string | null>(null)
  const sidebarOpen = ref(true)
  const viewMode = ref<ViewMode>('board')
  const darkMode = ref(false)
  const filters = ref<Filters>({
    status: [],
    priority: [],
    component: null,
    project: null,
    search: '',
  })

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
    }
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

  function getBackendFilters() {
    return {
      status: filters.value.status.length > 0 ? filters.value.status.join(',') : undefined,
      component: filters.value.component || undefined,
      project: filters.value.project || undefined,
    }
  }

  return {
    selectedIssueId,
    sidebarOpen,
    viewMode,
    darkMode,
    filters,
    setSelectedIssue,
    toggleSidebar,
    setViewMode,
    setFilter,
    clearFilters,
    toggleDarkMode,
    initDarkMode,
    getBackendFilters,
  }
})
