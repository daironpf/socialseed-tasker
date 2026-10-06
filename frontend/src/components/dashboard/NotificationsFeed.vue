<template>
  <ModuleCard :title="t('boardModules.latestNotifications')">
    <template #action>
      <span
        v-if="notificationsStore.unreadCount > 0"
        class="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
      >
        {{ notificationsStore.unreadCount }}
      </span>
    </template>

    <div v-if="recent.length === 0" class="text-sm text-gray-500 dark:text-gray-400">
      {{ t('boardModules.noNotifications') }}
    </div>

    <ul v-else class="space-y-3">
      <li
        v-for="n in recent"
        :key="n.id"
        class="-mx-1 flex cursor-pointer items-start gap-3 rounded-md px-1 py-1 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/60"
        :aria-expanded="expandedId === n.id"
        @click="toggle(n)"
      >
        <span
          class="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold"
          :class="CATEGORY_STYLES[n.category]"
        >
          {{ CATEGORY_CONFIG[n.category].icon }}
        </span>
        <div class="min-w-0 flex-1">
          <p
            class="truncate text-sm"
            :class="n.read ? 'text-gray-500 dark:text-gray-400' : 'font-medium text-gray-900 dark:text-white'"
          >
            {{ n.title }}
          </p>
          <p class="text-xs" :class="messageClass(n)">{{ n.message }}</p>
          <div
            v-if="expandedId === n.id"
            class="mt-1.5 flex items-center justify-between gap-2 border-t border-gray-100 pt-1.5 dark:border-gray-800"
          >
            <span class="text-[10px] text-gray-500 dark:text-gray-400">{{ fullDate(n.createdAt) }}</span>
            <button
              v-if="n.linkTo"
              class="shrink-0 rounded-md bg-blue-600 px-2 py-0.5 text-[10px] font-semibold text-white transition-colors hover:bg-blue-700"
              @click.stop="openLink(n)"
            >
              {{ t('notifItem.open') }}
            </button>
          </div>
        </div>
        <span class="flex-shrink-0 text-[10px] text-gray-500 dark:text-gray-400">{{ timeOf(n.createdAt) }}</span>
      </li>
    </ul>
  </ModuleCard>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ModuleCard from './ModuleCard.vue'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { CATEGORY_CONFIG, type AppNotification, type NotificationCategory } from '@/types/notifications'

const { t } = useI18n()

const notificationsStore = useNotificationsStore()
const router = useRouter()

const expandedId = ref<string | null>(null)

const CATEGORY_STYLES: Record<NotificationCategory, string> = {
  mention: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  hitl: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  constraint_violation: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  agent_failure: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  sla: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
  welcome: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
}

const recent = computed(() =>
  [...notificationsStore.notifications]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 4)
)

function toggle(n: AppNotification) {
  expandedId.value = expandedId.value === n.id ? null : n.id
  if (!n.read) notificationsStore.markAsRead(n.id)
}

function messageClass(n: AppNotification): string {
  const overflow = expandedId.value === n.id ? 'whitespace-pre-wrap break-words' : 'truncate'
  return `${overflow} text-xs text-gray-500 dark:text-gray-400`
}

function openLink(n: AppNotification) {
  if (n.linkTo) router?.push(n.linkTo)
}

function timeOf(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function fullDate(iso: string): string {
  return new Date(iso).toLocaleString()
}
</script>
