<template>
  <Teleport to="body">
    <Transition name="palette">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
        @click.self="close"
      >
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="close" />
        <div
          class="relative w-full max-w-lg bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
        >
          <div class="flex items-center border-b border-gray-200 dark:border-gray-700 px-4">
            <svg class="h-5 w-5 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              ref="inputRef"
              v-model="query"
              type="text"
              :placeholder="t('palette.placeholder')"
              class="flex-1 bg-transparent px-3 py-4 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none"
              @keydown.down.prevent="moveDown"
              @keydown.up.prevent="moveUp"
              @keydown.enter.prevent="executeSelected"
              @keydown.escape.prevent="close"
            />
            <kbd class="hidden sm:inline-flex items-center rounded border border-gray-300 dark:border-gray-600 px-1.5 py-0.5 text-xs font-medium text-gray-500 dark:text-gray-400">
              ESC
            </kbd>
          </div>

          <div class="max-h-80 overflow-y-auto p-2">
            <div v-if="query === '' && recentActions.length > 0" class="mb-2">
              <div class="px-3 py-1.5 text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                {{ t('palette.recent') }}
              </div>
              <button
                v-for="(action, idx) in recentActions"
                :key="'recent-' + idx"
                class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors"
                :class="selectedIndex === idx ? 'bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50'"
                @click="executeAction(action)"
                @mouseenter="selectedIndex = idx"
              >
                <span class="text-lg" v-html="action.icon" />
                <span class="flex-1 text-left">{{ action.label }}</span>
                <span class="text-xs text-gray-400 dark:text-gray-500">{{ action.category }}</span>
              </button>
            </div>

            <div v-if="query !== '' && filteredResults.length === 0" class="py-8 text-center text-sm text-gray-400 dark:text-gray-500">
              {{ t('palette.noResults') }}
            </div>

            <template v-for="(group, groupName) in groupedResults" :key="groupName">
              <div class="px-3 py-1.5 text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                {{ groupName }}
              </div>
              <button
                v-for="item in group"
                :key="item.id"
                class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors"
                :class="selectedIndex === globalIndex(item) ? 'bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50'"
                @click="executeResult(item)"
                @mouseenter="selectedIndex = globalIndex(item)"
              >
                <span class="text-lg" v-html="item.icon" />
                <span class="flex-1 text-left truncate">{{ item.label }}</span>
                <span v-if="item.description" class="text-xs text-gray-400 dark:text-gray-500 truncate max-w-[120px]">{{ item.description }}</span>
              </button>
            </template>
          </div>

          <div class="flex items-center gap-4 border-t border-gray-200 dark:border-gray-700 px-4 py-2 text-xs text-gray-400 dark:text-gray-500">
            <span class="flex items-center gap-1">
              <kbd class="rounded border border-gray-300 dark:border-gray-600 px-1 py-0.5">↑↓</kbd>
              {{ t('palette.navigate') }}
            </span>
            <span class="flex items-center gap-1">
              <kbd class="rounded border border-gray-300 dark:border-gray-600 px-1 py-0.5">↵</kbd>
              {{ t('palette.select') }}
            </span>
            <span class="flex items-center gap-1">
              <kbd class="rounded border border-gray-300 dark:border-gray-600 px-1 py-0.5">esc</kbd>
              {{ t('palette.close') }}
            </span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useIssuesStore } from '@/stores/issuesStore'
import { useComponentsStore } from '@/stores/componentsStore'
import { useUiStore } from '@/stores/uiStore'

const { t } = useI18n()
const router = useRouter()
const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()
const uiStore = useUiStore()

const isOpen = ref(false)
const query = ref('')
const selectedIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)

interface PaletteItem {
  id: string
  label: string
  description?: string
  icon: string
  category: string
  group: string
  action: () => void
}

const pages: PaletteItem[] = [
  { id: 'page-board', label: t('header.dashboard'), icon: '📊', category: 'Page', group: 'pages', action: () => router.push('/board') },
  { id: 'page-kanban', label: t('header.kanban'), icon: '📋', category: 'Page', group: 'pages', action: () => router.push('/kanban') },
  { id: 'page-list', label: t('header.issues'), icon: '📝', category: 'Page', group: 'pages', action: () => router.push('/list') },
  { id: 'page-components', label: t('header.components'), icon: '🧩', category: 'Page', group: 'pages', action: () => router.push('/components') },
  { id: 'page-policies', label: t('header.policies'), icon: '📜', category: 'Page', group: 'pages', action: () => router.push('/policies') },
  { id: 'page-constraints', label: t('header.constraints'), icon: '🔒', category: 'Page', group: 'pages', action: () => router.push('/constraints') },
  { id: 'page-users', label: t('header.users'), icon: '👥', category: 'Page', group: 'pages', action: () => router.push('/users') },
  { id: 'page-graph', label: t('header.graph'), icon: '🕸️', category: 'Page', group: 'pages', action: () => router.push('/graph') },
  { id: 'page-analysis', label: t('header.analysis'), icon: '🔍', category: 'Page', group: 'pages', action: () => router.push('/analysis') },
  { id: 'page-system', label: t('header.system'), icon: '⚙️', category: 'Page', group: 'pages', action: () => router.push('/system') },
]

const quickActions: PaletteItem[] = [
  { id: 'action-create-issue', label: t('commandPalette.createIssue'), icon: '➕', category: 'Action', group: 'actions', action: () => { close(); router.push('/list'); } },
  { id: 'action-toggle-dark', label: t('commandPalette.toggleDark'), icon: '🌙', category: 'Action', group: 'actions', action: () => { uiStore.toggleDarkMode(); close(); } },
  { id: 'action-toggle-sidebar', label: t('commandPalette.toggleSidebar'), icon: '📌', category: 'Action', group: 'actions', action: () => { uiStore.toggleSidebar(); close(); } },
  { id: 'action-clear-filters', label: t('commandPalette.clearFilters'), icon: '🧹', category: 'Action', group: 'actions', action: () => { uiStore.clearFilters(); close(); } },
]

const allItems = computed<PaletteItem[]>(() => {
  const items = [...pages, ...quickActions]

  for (const issue of issuesStore.issues) {
    items.push({
      id: 'issue-' + issue.id,
      label: issue.title,
      description: issue.id.slice(0, 8),
      icon: issue.status === 'CLOSED' ? '✅' : issue.status === 'BLOCKED' ? '🔴' : issue.status === 'IN_PROGRESS' ? '🟡' : '🔵',
      category: 'Issue',
      group: 'issues',
      action: () => { close(); router.push('/list'); },
    })
  }

  for (const comp of componentsStore.components) {
    items.push({
      id: 'comp-' + comp.id,
      label: comp.name,
      description: comp.project,
      icon: '🧩',
      category: 'Component',
      group: 'components',
      action: () => { close(); router.push('/components'); },
    })
  }

  return items
})

function fuzzyMatch(text: string, pattern: string): boolean {
  const lower = text.toLowerCase()
  const pat = pattern.toLowerCase()
  let pi = 0
  for (let i = 0; i < lower.length && pi < pat.length; i++) {
    if (lower[i] === pat[pi]) pi++
  }
  return pi === pat.length
}

const filteredResults = computed(() => {
  if (!query.value.trim()) return []
  return allItems.value.filter((item) =>
    fuzzyMatch(item.label, query.value) ||
    fuzzyMatch(item.description || '', query.value) ||
    fuzzyMatch(item.category, query.value)
  )
})

const groupedResults = computed(() => {
  const groups: Record<string, PaletteItem[]> = {}
  for (const item of filteredResults.value) {
    const groupName = item.group === 'pages' ? t('palette.groupPages') :
      item.group === 'actions' ? t('palette.groupActions') :
      item.group === 'issues' ? t('palette.groupIssues') :
      t('palette.groupComponents')
    if (!groups[groupName]) groups[groupName] = []
    groups[groupName].push(item)
  }
  return groups
})

const flatFiltered = computed(() => filteredResults.value)

function globalIndex(item: PaletteItem): number {
  return flatFiltered.value.findIndex((i) => i.id === item.id)
}

const recentActions = computed<PaletteItem[]>(() => {
  try {
    const stored = JSON.parse(localStorage.getItem('palette-recent') || '[]') as string[]
    return stored
      .map((id) => allItems.value.find((item) => item.id === id))
      .filter((item): item is PaletteItem => !!item)
      .slice(0, 5)
  } catch {
    return []
  }
})

function saveRecent(id: string) {
  try {
    const stored = JSON.parse(localStorage.getItem('palette-recent') || '[]') as string[]
    const filtered = stored.filter((s) => s !== id)
    filtered.unshift(id)
    localStorage.setItem('palette-recent', JSON.stringify(filtered.slice(0, 10)))
  } catch {
    localStorage.setItem('palette-recent', JSON.stringify([id]))
  }
}

function moveDown() {
  const max = query.value ? flatFiltered.value.length : recentActions.value.length
  if (max === 0) return
  selectedIndex.value = (selectedIndex.value + 1) % max
}

function moveUp() {
  const max = query.value ? flatFiltered.value.length : recentActions.value.length
  if (max === 0) return
  selectedIndex.value = (selectedIndex.value - 1 + max) % max
}

function executeSelected() {
  if (query.value) {
    const item = flatFiltered.value[selectedIndex.value]
    if (item) executeResult(item)
  } else {
    const item = recentActions.value[selectedIndex.value]
    if (item) executeAction(item)
  }
}

function executeResult(item: PaletteItem) {
  saveRecent(item.id)
  item.action()
}

function executeAction(item: PaletteItem) {
  saveRecent(item.id)
  item.action()
}

function open() {
  isOpen.value = true
  query.value = ''
  selectedIndex.value = 0
  nextTick(() => inputRef.value?.focus())
}

function close() {
  isOpen.value = false
  query.value = ''
  selectedIndex.value = 0
}

watch(query, () => {
  selectedIndex.value = 0
})

function handleKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    if (isOpen.value) {
      close()
    } else {
      open()
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

defineExpose({ open, close })
</script>

<style scoped>
.palette-enter-active,
.palette-leave-active {
  transition: opacity 0.15s ease;
}
.palette-enter-from,
.palette-leave-to {
  opacity: 0;
}
</style>
