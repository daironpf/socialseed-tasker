<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center"
        @click.self="close"
      >
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="close" />
        <div
          class="relative w-full max-w-md bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden mx-4"
        >
          <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('shortcuts.title') }}</h2>
            <button
              class="rounded-lg p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              @click="close"
            >
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="max-h-[60vh] overflow-y-auto p-5 space-y-5">
            <div v-for="group in shortcutGroups" :key="group.label">
              <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">
                {{ group.label }}
              </h3>
              <div class="space-y-1.5">
                <div
                  v-for="shortcut in group.shortcuts"
                  :key="shortcut.keys"
                  class="flex items-center justify-between py-1.5"
                >
                  <span class="text-sm text-gray-700 dark:text-gray-300">{{ shortcut.description }}</span>
                  <div class="flex items-center gap-1">
                    <kbd
                      v-for="key in shortcut.keys.split('+')"
                      :key="key"
                      class="inline-flex items-center justify-center min-w-[24px] h-6 px-1.5 rounded border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-xs font-medium text-gray-600 dark:text-gray-300"
                    >
                      {{ key }}
                    </kbd>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="px-5 py-3 border-t border-gray-200 dark:border-gray-700 text-center">
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ t('shortcuts.hint') }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const isOpen = ref(false)

interface ShortcutItem {
  keys: string
  description: string
}

interface ShortcutGroup {
  label: string
  shortcuts: ShortcutItem[]
}

const shortcutGroups = computed<ShortcutGroup[]>(() => [
  {
    label: t('shortcuts.groupNavigation'),
    shortcuts: [
      { keys: 'C', description: t('shortcuts.createIssue') },
      { keys: 'G+I', description: t('shortcuts.goList') },
      { keys: 'G+K', description: t('shortcuts.goKanban') },
      { keys: 'G+G', description: t('shortcuts.goGraph') },
      { keys: 'G+B', description: t('shortcuts.goDashboard') },
      { keys: 'G+U', description: t('shortcuts.goUsers') },
      { keys: 'G+C', description: t('shortcuts.goComponents') },
    ],
  },
  {
    label: t('shortcuts.groupCommandPalette'),
    shortcuts: [
      { keys: 'Ctrl+K', description: t('shortcuts.openPalette') },
    ],
  },
  {
    label: t('shortcuts.groupListKanban'),
    shortcuts: [
      { keys: 'J', description: t('shortcuts.nextItem') },
      { keys: 'K', description: t('shortcuts.prevItem') },
      { keys: 'Enter', description: t('shortcuts.openDetail') },
      { keys: 'Esc', description: t('shortcuts.closePanel') },
    ],
  },
  {
    label: t('shortcuts.groupGeneral'),
    shortcuts: [
      { keys: '?', description: t('shortcuts.showHelp') },
      { keys: 'D', description: t('shortcuts.toggleDark') },
    ],
  },
])

function open() {
  isOpen.value = true
}

function close() {
  isOpen.value = false
}

function toggle() {
  isOpen.value = !isOpen.value
}

function handleKeydown(e: KeyboardEvent) {
  const el = document.activeElement
  if (el) {
    const tag = el.tagName.toLowerCase()
    if (tag === 'input' || tag === 'textarea' || (el as HTMLElement).isContentEditable) return
  }

  if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey) {
    e.preventDefault()
    toggle()
  }

  if (e.key === 'Escape' && isOpen.value) {
    e.preventDefault()
    close()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

defineExpose({ open, close, toggle })
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.15s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
