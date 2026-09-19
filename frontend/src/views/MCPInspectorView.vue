<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('mcp.title') }}</h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('mcp.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <span
            class="h-2.5 w-2.5 rounded-full"
            :class="mcpStore.streamConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'"
          ></span>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ mcpStore.streamConnected ? t('mcp.streamLive') : t('mcp.streamOff') }}
          </span>
        </div>
        <button
          class="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="toggleStream"
        >
          {{ mcpStore.streamConnected ? t('mcp.stopStream') : t('mcp.startStream') }}
        </button>
        <button
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
          @click="mcpStore.fetchSessions()"
        >
          {{ t('mcp.refresh') }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="mcpStore.loading" class="flex items-center justify-center py-20">
      <LoadingSpinner />
    </div>

    <template v-else>
      <!-- Metrics Cards -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('mcp.totalSessions') }}</span>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <svg class="h-4 w-4 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </span>
          </div>
          <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{{ mcpStore.metrics.totalSessions }}</p>
          <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">{{ t('mcp.allConnections') }}</p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('mcp.activeSessions') }}</span>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30">
              <svg class="h-4 w-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M13 12a1 1 0 11-2 0 1 1 0 012 0z" />
              </svg>
            </span>
          </div>
          <p class="mt-2 text-3xl font-bold text-green-600 dark:text-green-400">{{ mcpStore.metrics.activeSessions }}</p>
          <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">{{ t('mcp.currentlyConnected') }}</p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('mcp.contextConsumed') }}</span>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30">
              <svg class="h-4 w-4 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            </span>
          </div>
          <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{{ mcpStore.formatBytes(mcpStore.metrics.totalContextConsumed) }}</p>
          <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">{{ t('mcp.acrossAllSessions') }}</p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('mcp.cypherQueries') }}</span>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <svg class="h-4 w-4 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c-1.306 0-2.417.835-2.83 2M9 14a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </span>
          </div>
          <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{{ mcpStore.metrics.totalCypherQueries.toLocaleString() }}</p>
          <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">{{ t('mcp.avgPerMin', { rate: mcpStore.metrics.avgQueriesPerMin.toFixed(1) }) }}</p>
        </div>
      </div>

      <!-- Sessions Matrix -->
      <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('mcp.sessionMatrix') }}</h3>
          <div class="flex items-center gap-2">
            <button
              v-for="filter in statusFilters"
              :key="filter.value"
              class="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
              :class="activeFilter === filter.value
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'"
              @click="activeFilter = filter.value"
            >
              {{ filter.label }}
              <span
                v-if="filter.count > 0"
                class="ml-1 rounded-full bg-gray-200 px-1.5 text-[10px] dark:bg-gray-600"
              >{{ filter.count }}</span>
            </button>
          </div>
        </div>

        <div v-if="filteredSessions.length === 0" class="px-6 py-12 text-center">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          <p class="mt-3 text-sm text-gray-500 dark:text-gray-400">{{ t('mcp.noSessions') }}</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100 dark:border-gray-700">
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.client') }}</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.status') }}</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.uptime') }}</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.context') }}</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.queries') }}</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.tools') }}</th>
                <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('mcp.actions') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50 dark:divide-gray-700/50">
              <tr
                v-for="session in filteredSessions"
                :key="session.id"
                class="transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/30"
              >
                <!-- Client -->
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                    <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 text-lg dark:bg-gray-700">
                      {{ mcpStore.getClientIcon(session.clientType) }}
                    </div>
                    <div>
                      <p class="text-sm font-semibold text-gray-900 dark:text-white">{{ session.clientName }}</p>
                      <p class="text-xs text-gray-400 dark:text-gray-500">{{ session.id }}</p>
                    </div>
                  </div>
                </td>

                <!-- Status -->
                <td class="px-6 py-4">
                  <span
                    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                    :class="mcpStore.getStatusColor(session.status)"
                  >
                    <span
                      class="mr-1.5 h-1.5 w-1.5 rounded-full"
                      :class="{
                        'bg-green-500': session.status === 'active',
                        'bg-amber-500': session.status === 'paused',
                        'bg-red-500': session.status === 'revoked',
                        'bg-gray-400': session.status === 'idle',
                      }"
                    ></span>
                    {{ t(`mcp.statuses.${session.status}`) }}
                  </span>
                </td>

                <!-- Uptime -->
                <td class="px-6 py-4">
                  <span class="text-sm text-gray-700 dark:text-gray-300">{{ mcpStore.formatUptime(session.uptime) }}</span>
                </td>

                <!-- Context -->
                <td class="px-6 py-4">
                  <div class="w-32">
                    <div class="flex items-center justify-between text-xs">
                      <span class="text-gray-700 dark:text-gray-300">{{ mcpStore.formatBytes(session.contextConsumed) }}</span>
                      <span class="text-gray-400 dark:text-gray-500">{{ Math.round((session.contextConsumed / session.contextLimit) * 100) }}%</span>
                    </div>
                    <div class="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-600">
                      <div
                        class="h-full rounded-full transition-all duration-500"
                        :class="getContextBarColor(session)"
                        :style="{ width: `${(session.contextConsumed / session.contextLimit) * 100}%` }"
                      ></div>
                    </div>
                  </div>
                </td>

                <!-- Cypher Queries -->
                <td class="px-6 py-4">
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">{{ session.cypherQueries.toLocaleString() }}</p>
                    <p class="text-xs text-gray-400 dark:text-gray-500">
                      {{ session.status === 'active' ? `${session.cypherQueriesPerMin} ${t('mcp.perMin')}` : t('mcp.idle') }}
                    </p>
                  </div>
                </td>

                <!-- Tools -->
                <td class="px-6 py-4">
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="tool in session.toolsUsed.slice(0, 3)"
                      :key="tool"
                      class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-400"
                    >
                      {{ tool }}
                    </span>
                    <span
                      v-if="session.toolsUsed.length > 3"
                      class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500 dark:bg-gray-700 dark:text-gray-500"
                    >
                      +{{ session.toolsUsed.length - 3 }}
                    </span>
                  </div>
                </td>

                <!-- Actions -->
                <td class="px-6 py-4">
                  <div class="flex items-center justify-end gap-1">
                    <button
                      v-if="session.status === 'active'"
                      class="rounded-lg p-1.5 text-amber-600 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20"
                      :aria-label="t('mcp.pause')"
                      :title="t('mcp.pause')"
                      @click="handlePause(session.id)"
                    >
                      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                    <button
                      v-if="session.status === 'paused'"
                      class="rounded-lg p-1.5 text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/20"
                      :aria-label="t('mcp.resume')"
                      :title="t('mcp.resume')"
                      @click="handleResume(session.id)"
                    >
                      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                    <button
                      v-if="session.status !== 'revoked'"
                      class="rounded-lg p-1.5 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                      :aria-label="t('mcp.revoke')"
                      :title="t('mcp.revoke')"
                      @click="handleRevoke(session.id)"
                    >
                      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Confirm Modal -->
    <div
      v-if="confirmModal.show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="confirmModal.show = false"
    >
      <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ confirmModal.title }}</h3>
        <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">{{ confirmModal.message }}</p>
        <div class="mt-6 flex justify-end gap-3">
          <button
            class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="confirmModal.show = false"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            class="rounded-lg px-4 py-2 text-sm font-medium text-white"
            :class="confirmModal.danger ? 'bg-red-600 hover:bg-red-700' : 'bg-amber-600 hover:bg-amber-700'"
            @click="confirmModal.onConfirm(); confirmModal.show = false"
          >
            {{ confirmModal.confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMcpStore } from '@/stores/mcpStore'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import type { MCPSessionStatus } from '@/types/mcp'

const { t } = useI18n()
const mcpStore = useMcpStore()

const activeFilter = ref<'all' | MCPSessionStatus>('all')

const confirmModal = ref<{
  show: boolean
  title: string
  message: string
  confirmLabel: string
  danger: boolean
  onConfirm: () => void
}>({
  show: false,
  title: '',
  message: '',
  confirmLabel: '',
  danger: false,
  onConfirm: () => {},
})

const statusFilters = computed(() => [
  { value: 'all' as const, label: t('mcp.filterAll'), count: mcpStore.sessions.length },
  { value: 'active' as const, label: t('mcp.filterActive'), count: mcpStore.activeSessions.length },
  { value: 'paused' as const, label: t('mcp.filterPaused'), count: mcpStore.pausedSessions.length },
  { value: 'idle' as const, label: t('mcp.filterIdle'), count: mcpStore.idleSessions.length },
  { value: 'revoked' as const, label: t('mcp.filterRevoked'), count: mcpStore.revokedSessions.length },
])

const filteredSessions = computed(() => {
  if (activeFilter.value === 'all') return mcpStore.sessions
  return mcpStore.sessions.filter(s => s.status === activeFilter.value)
})

function getContextBarColor(session: { contextConsumed: number; contextLimit: number }): string {
  const pct = (session.contextConsumed / session.contextLimit) * 100
  if (pct >= 90) return 'bg-red-500'
  if (pct >= 70) return 'bg-amber-500'
  return 'bg-blue-500'
}

function handlePause(id: string) {
  confirmModal.value = {
    show: true,
    title: t('mcp.pauseSessionTitle'),
    message: t('mcp.pauseSessionMessage'),
    confirmLabel: t('mcp.pauseSessionConfirm'),
    danger: false,
    onConfirm: () => mcpStore.pauseSession(id),
  }
}

function handleResume(id: string) {
  mcpStore.resumeSession(id)
}

function handleRevoke(id: string) {
  confirmModal.value = {
    show: true,
    title: t('mcp.revokeSessionTitle'),
    message: t('mcp.revokeSessionMessage'),
    confirmLabel: t('mcp.revokeSessionConfirm'),
    danger: true,
    onConfirm: () => mcpStore.revokeSession(id),
  }
}

function toggleStream() {
  if (mcpStore.streamConnected) {
    mcpStore.stopStream()
  } else {
    mcpStore.startStream()
  }
}

onMounted(() => {
  mcpStore.fetchSessions()
  mcpStore.startStream()
})

onUnmounted(() => {
  mcpStore.stopStream()
})
</script>
