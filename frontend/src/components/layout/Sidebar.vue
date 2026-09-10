<template>
  <aside
    class="fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-gray-200 bg-white transition-all duration-300 dark:border-gray-700 dark:bg-gray-900 pb-10"
    :class="isExpanded ? 'w-64' : 'w-20'"
    @mouseenter="isExpanded = true"
    @mouseleave="isExpanded = false"
  >
    <!-- Logo -->
    <div class="flex h-16 items-center border-b border-gray-200 px-4 dark:border-gray-700">
      <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-brand-600">
        <svg class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
      </div>
      <span
        v-if="isExpanded"
        class="ml-3 text-lg font-bold text-gray-900 transition-opacity dark:text-white"
      >
        SocialSeed
      </span>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto px-3 py-4">
      <div v-for="group in navGroups" :key="group.label" class="mb-6">
        <p
          v-if="isExpanded"
          class="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500"
        >
          {{ group.label }}
        </p>
        <div v-else class="mb-2 h-px bg-gray-200 dark:bg-gray-700" />

        <div class="space-y-1">
          <NavItem
            v-for="item in group.items"
            :key="item.path"
            :item="item"
            :is-expanded="isExpanded"
            :is-active="route.path === item.path"
            @click="navigateTo(item.path)"
          />
        </div>
      </div>
    </nav>

    <!-- Bottom Actions -->
    <div class="border-t border-gray-200 p-3 dark:border-gray-700">
      <NavItem
        :item="darkModeItem"
        :is-expanded="isExpanded"
        :is-active="false"
        @click="uiStore.toggleDarkMode"
      />
      <NavItem
        :item="logoutItem"
        :is-expanded="isExpanded"
        :is-active="false"
        @click="handleLogout"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUiStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'
import NavItem from './NavItem.vue'

interface NavItem {
  path: string
  label: string
  icon: string
  badge?: number
}

const route = useRoute()
const router = useRouter()
const uiStore = useUiStore()
const authStore = useAuthStore()

const isExpanded = ref(false)

const navGroups = [
  {
    label: 'Principal',
    items: [
      {
        path: '/board',
        label: 'Dashboard',
        icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
      },
      {
        path: '/kanban',
        label: 'Kanban',
        icon: 'M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2',
      },
      {
        path: '/list',
        label: 'Issues',
        icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
      },
    ],
  },
  {
    label: 'Gestión',
    items: [
      {
        path: '/components',
        label: 'Componentes',
        icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
      },
      {
        path: '/policies',
        label: 'Políticas',
        icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
      },
    ],
  },
  {
    label: 'Análisis',
    items: [
      {
        path: '/graph',
        label: 'Grafo',
        icon: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1',
      },
    ],
  },
]

const darkModeItem = {
  path: '',
  label: uiStore.darkMode ? 'Modo Claro' : 'Modo Oscuro',
  icon: uiStore.darkMode
    ? 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z'
    : 'M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z',
}

const logoutItem = {
  path: '',
  label: 'Salir',
  icon: 'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1',
}

function navigateTo(path: string) {
  if (path) {
    router.push(path)
  }
}

function handleLogout() {
  authStore.clearApiKey()
  window.location.reload()
}
</script>
