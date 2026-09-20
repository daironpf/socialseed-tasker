<template>
  <header class="sticky top-0 z-30 border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
    <div class="flex h-16 items-center justify-between px-6">
      <div class="flex items-center gap-4">
        <h1 class="text-lg font-bold text-gray-900 dark:text-white">
          {{ pageTitle }}
        </h1>
      </div>
      <div class="flex items-center gap-3">
        <ProjectSelector />
        <NotificationCenter />
        <UserMenu />
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import UserMenu from './UserMenu.vue'
import NotificationCenter from '@/components/ui/NotificationCenter.vue'
import ProjectSelector from '@/components/ui/ProjectSelector.vue'

const route = useRoute()
const { t } = useI18n()

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/board': t('header.dashboard'),
    '/system': t('header.system'),
    '/kanban': t('header.kanban'),
    '/list': t('header.issues'),
    '/graph': t('header.graph'),
    '/components': t('header.components'),
    '/policies': t('header.policies'),
    '/constraints': t('header.constraints'),
    '/sandbox': t('header.sandbox'),
    '/rag': t('header.rag'),
    '/finops': t('header.finops'),
    '/auto-healing': t('header.autoHealing'),
    '/users': t('header.users'),
    '/chat': t('header.chat'),
    '/mcp': t('header.mcp'),
    '/hitl': t('header.hitl'),
    '/analysis': t('header.analysis'),
  }
  return titles[route.path] || t('header.dashboard')
})
</script>
