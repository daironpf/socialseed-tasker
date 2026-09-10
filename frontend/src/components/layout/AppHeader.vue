<template>
  <header class="sticky top-0 z-30 border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
    <div class="flex h-16 items-center justify-between px-6">
      <div class="flex items-center gap-4">
        <h1 class="text-lg font-bold text-gray-900 dark:text-white">
          {{ pageTitle }}
        </h1>
      </div>
      <div class="flex items-center gap-3">
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/board': 'Dashboard',
    '/kanban': 'Kanban',
    '/list': 'Issues',
    '/graph': 'Grafo de Dependencias',
    '/components': 'Componentes',
    '/policies': 'Políticas',
    '/settings': 'Configuración',
  }
  return titles[route.path] || 'Dashboard'
})
</script>
