import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useIssuesStore } from './issuesStore'
import { useComponentsStore } from './componentsStore'

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

  const issuesStore = useIssuesStore()

  const filteredIssues = computed(() => {
    let result = Array.isArray(issuesStore.issues) ? [...issuesStore.issues] : []
    const f = filters.value

    if (f.search) {
      const q = f.search.toLowerCase()
      result = result.filter(
        (i) =>
          i.title.toLowerCase().includes(q) ||
          i.description.toLowerCase().includes(q),
      )
    }

    if (f.status.length > 0) {
      result = result.filter((i) => f.status.includes(i.status))
    }

    if (f.priority.length > 0) {
      result = result.filter((i) => f.priority.includes(i.priority))
    }

    if (f.component) {
      result = result.filter((i) => i.component_id === f.component)
    }

    if (f.project) {
      const componentsStore = useComponentsStore()
      result = result.filter((i) => {
        const comp = componentsStore.getComponentById(i.component_id)
        return !comp || comp.project === f.project
      })
    }

    console.log('[UIStore] Final filtered issues:', result.length)
    return result
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

  return {
    selectedIssueId,
    sidebarOpen,
    viewMode,
    darkMode,
    filters,
    filteredIssues,
    setSelectedIssue,
    toggleSidebar,
    setViewMode,
    setFilter,
    clearFilters,
    toggleDarkMode,
    initDarkMode,
  }
})
