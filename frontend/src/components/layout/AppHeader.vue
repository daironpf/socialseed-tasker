<template>
  <header class="sticky top-0 z-30 border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
    <!-- Global HITL Banner -->
    <div
      v-if="hitlStore.urgentPendingCount > 0"
      class="flex items-center justify-between gap-3 border-b border-amber-300 bg-amber-50 px-6 py-2 dark:border-amber-700 dark:bg-amber-900/20"
      role="alert"
    >
      <button
        class="flex min-w-0 flex-1 items-center gap-2 text-left"
        @click="router.push({ name: 'HITLCommandCenter' })"
      >
        <span class="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-amber-500 text-[10px] font-bold text-white">
          !
        </span>
        <span class="truncate text-xs font-medium text-amber-800 dark:text-amber-300">
          {{ t('hitlBanner.message', { count: hitlStore.urgentPendingCount }) }}
        </span>
        <span class="flex-shrink-0 text-xs font-semibold text-amber-600 underline hover:text-amber-700 dark:text-amber-400">
          {{ t('hitlBanner.viewAll') }}
        </span>
      </button>
      <button
        class="flex-shrink-0 rounded-lg bg-amber-600 px-3 py-1 text-xs font-semibold text-white hover:bg-amber-700 transition-colors"
        @click="openFirstUrgent"
      >
        {{ t('hitlBanner.review') }}
      </button>
    </div>

    <div class="flex h-16 items-center justify-between px-6">
      <div class="flex items-center gap-4">
        <h1 class="text-lg font-bold text-gray-900 dark:text-white">
          {{ pageTitle }}
        </h1>
      </div>
      <div class="flex items-center gap-3">
        <ProjectSelector />
        <SyncStatusBadge />
        <NotificationCenter />
        <UserMenu />
      </div>
    </div>

    <!-- Quick Action Modal -->
    <HITLQuickActionModal
      v-if="quickRequest"
      :request="quickRequest"
      @close="hitlStore.closeQuickAction()"
    />
  </header>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import UserMenu from './UserMenu.vue'
import NotificationCenter from '@/components/ui/NotificationCenter.vue'
import ProjectSelector from '@/components/ui/ProjectSelector.vue'
import SyncStatusBadge from '@/components/ui/SyncStatusBadge.vue'
import HITLQuickActionModal from '@/components/ui/HITLQuickActionModal.vue'
import { useHitlStore } from '@/stores/hitlStore'
import { useNotificationsStore } from '@/stores/notificationsStore'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const hitlStore = useHitlStore()
const notificationsStore = useNotificationsStore()

const quickRequest = computed(() =>
  hitlStore.requests.find(r => r.id === hitlStore.quickActionRequestId) || null
)

function openFirstUrgent() {
  const first = hitlStore.urgentPendingRequests[0]
  if (first) hitlStore.openQuickAction(first.id)
}

onMounted(async () => {
  await hitlStore.fetchRequests()
  notificationsStore.ensureHitlNotifications(hitlStore.pendingRequests)
})

watch(
  () => hitlStore.pendingRequests.length,
  () => {
    notificationsStore.ensureHitlNotifications(hitlStore.pendingRequests)
  }
)

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
    '/replay': t('header.replay'),
    '/executive': t('header.executive'),
    '/users': t('header.users'),
    '/chat': t('header.chat'),
    '/mcp': t('header.mcp'),
    '/hitl': t('header.hitl'),
    '/analysis': t('header.analysis'),
  }
  return titles[route.path] || t('header.dashboard')
})
</script>
