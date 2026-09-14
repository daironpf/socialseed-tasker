<template>
  <div class="relative" ref="containerRef">
    <button
      class="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:bg-gray-700"
      :aria-label="t('projects.title')"
      @click="open = !open"
    >
      <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
      <span class="max-w-[140px] truncate font-medium text-gray-700 dark:text-gray-300">
        {{ currentProjectName }}
      </span>
      <svg class="h-3.5 w-3.5 text-gray-400 transition-transform" :class="{ 'rotate-180': open }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="scale-95 opacity-0"
        enter-to-class="scale-100 opacity-100"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="scale-100 opacity-100"
        leave-to-class="scale-95 opacity-0"
      >
        <div
          v-if="open"
          class="fixed top-12 left-4 z-50 w-72 rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900"
        >
          <div class="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('projects.title') }}</h3>
          </div>

          <div class="max-h-64 overflow-y-auto p-2">
            <button
              v-for="project in projects"
              :key="project.id"
              class="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors"
              :class="project.id === uiStore.currentProject
                ? 'bg-blue-50 dark:bg-blue-900/20'
                : 'hover:bg-gray-50 dark:hover:bg-gray-800'"
              @click="selectProject(project.id)"
            >
              <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-700">
                <svg class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-sm font-medium text-gray-900 dark:text-white">{{ project.name }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ project.description }}</div>
              </div>
              <svg
                v-if="project.id === uiStore.currentProject"
                class="h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400"
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUiStore } from '@/stores/uiStore'

const { t } = useI18n()
const uiStore = useUiStore()

const open = ref(false)
const containerRef = ref<HTMLElement | null>(null)

const projects = computed(() => uiStore.availableProjects)

const currentProjectName = computed(() => {
  const p = projects.value.find(p => p.id === uiStore.currentProject)
  return p?.name || uiStore.currentProject
})

function selectProject(id: string) {
  if (id !== uiStore.currentProject) {
    uiStore.setProject(id)
  }
  open.value = false
}

function handleClickOutside(e: MouseEvent) {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>
