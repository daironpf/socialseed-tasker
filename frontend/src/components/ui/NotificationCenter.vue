<template>
  <div class="relative" ref="containerRef">
    <button
      class="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
      @click="open = !open"
      :aria-label="t('notifications.title')"
    >
      <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      <span
        v-if="unreadCount > 0"
        class="absolute -top-0.5 -right-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white"
      >
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
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
          ref="panelRef"
          class="fixed top-14 right-4 z-50 w-[400px] max-h-[560px] rounded-xl border border-gray-200 bg-white shadow-2xl dark:border-gray-700 dark:bg-gray-900 flex flex-col"
        >
          <!-- Header -->
          <div class="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('notifications.title') }}</h3>
            <div class="flex items-center gap-3">
              <button
                v-if="unreadCount > 0"
                class="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
                @click="store.markAllAsRead()"
              >{{ t('notifications.markAllRead') }}</button>
              <button
                v-if="filteredNotifications.length > 0"
                class="text-xs text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                @click="clearAll"
              >{{ t('notifPanel.clearAll') }}</button>
            </div>
          </div>

          <!-- Filter tabs -->
          <div class="flex border-b border-gray-200 dark:border-gray-700">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="flex-1 px-3 py-2 text-xs font-medium transition-colors border-b-2"
              :class="activeTab === tab.key
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
              <span v-if="tab.count > 0" class="ml-1 rounded-full bg-gray-200 px-1.5 text-[9px] dark:bg-gray-700">{{ tab.count }}</span>
            </button>
          </div>

          <!-- Channel chips -->
          <div class="flex gap-1.5 overflow-x-auto border-b border-gray-200 px-3 py-2 dark:border-gray-700">
            <button
              v-for="chip in channelChips"
              :key="chip.key"
              class="shrink-0 rounded-full px-2.5 py-1 text-[10px] font-semibold transition-colors"
              :class="channelFilter === chip.key
                ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
              @click="channelFilter = chip.key"
            >
              {{ t(`notifPanel.channel.${chip.key}`) }}
            </button>
          </div>

          <!-- Grouped notifications -->
          <div class="flex-1 overflow-y-auto">
            <div v-if="filteredNotifications.length === 0" class="flex flex-col items-center justify-center py-12 text-gray-400">
              <svg class="h-10 w-10 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <p class="text-sm">{{ t('notifications.empty') }}</p>
            </div>

            <div v-for="group in groups" :key="group.key">
              <div class="sticky top-0 z-10 flex items-center justify-between border-b border-gray-100 bg-gray-50/90 px-4 py-1.5 backdrop-blur dark:border-gray-800 dark:bg-gray-900/90">
                <div class="flex items-center gap-1.5">
                  <span class="h-1.5 w-1.5 rounded-full" :class="groupDot[group.key]" />
                  <span class="text-[10px] font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    {{ t(`notifPanel.groups.${group.key}`) }}
                  </span>
                  <span class="rounded-full bg-gray-200 px-1.5 text-[9px] font-bold text-gray-500 dark:bg-gray-700 dark:text-gray-300">{{ group.items.length }}</span>
                </div>
                <button
                  v-if="group.items.some(n => !n.read)"
                  class="text-[10px] text-blue-600 hover:text-blue-700 dark:text-blue-400"
                  @click="markGroupRead(group)"
                >
                  {{ t('notifPanel.markGroupRead') }}
                </button>
              </div>
              <NotificationItem
                v-for="notif in group.items"
                :key="notif.id"
                :notification="notif"
                @dismiss="store.dismiss"
                @markRead="store.markAsRead"
              />
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { SEVERITY_GROUPS, type NotificationCategory, type SeverityGroup, type AppNotification } from '@/types/notifications'
import NotificationItem from './NotificationItem.vue'

const { t } = useI18n()
const store = useNotificationsStore()

const open = ref(false)
const activeTab = ref<'all' | 'unread' | 'action'>('all')
const channelFilter = ref<'all' | NotificationCategory>('all')
const containerRef = ref<HTMLElement | null>(null)
const panelRef = ref<HTMLElement | null>(null)

const tabs = computed(() => [
  { key: 'all' as const, label: t('notifications.tabs.all'), count: store.notifications.length },
  { key: 'unread' as const, label: t('notifications.tabs.unread'), count: store.unreadCount },
  { key: 'action' as const, label: t('notifications.tabs.action'), count: store.notifications.filter(n => n.requiresAction && !n.read).length },
])

const channelChips: Array<{ key: 'all' | NotificationCategory }> = [
  { key: 'all' },
  { key: 'hitl' },
  { key: 'constraint_violation' },
  { key: 'agent_failure' },
  { key: 'sla' },
  { key: 'mention' },
]

const filteredNotifications = computed(() =>
  store.getFiltered(activeTab.value).filter(
    n => channelFilter.value === 'all' || n.category === channelFilter.value
  )
)

const groupOrder: SeverityGroup[] = ['emergency', 'warning', 'info']

const groups = computed(() =>
  groupOrder
    .map(key => ({
      key,
      items: filteredNotifications.value.filter(n => SEVERITY_GROUPS[key].includes(n.category)),
    }))
    .filter(g => g.items.length > 0)
)

const groupDot: Record<SeverityGroup, string> = {
  emergency: 'bg-red-500',
  warning: 'bg-amber-500',
  info: 'bg-blue-500',
}

const unreadCount = computed(() => store.unreadCount)

function markGroupRead(group: { items: AppNotification[] }) {
  store.markManyRead(group.items.filter(n => !n.read).map(n => n.id))
}

function clearAll() {
  store.dismissMany(filteredNotifications.value.map(n => n.id))
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as Node
  if (containerRef.value?.contains(target)) return
  if (panelRef.value?.contains(target)) return
  open.value = false
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  store.seedMockNotifications()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
