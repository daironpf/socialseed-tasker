<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('system.title') }}</h1>
      </div>
      <div class="flex items-center gap-3">
        <button
          class="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
          @click="refreshAll"
        >
          {{ t('system.refresh') }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
    </div>

    <template v-else>
      <!-- Main Metrics -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ health?.metrics.total_issues || 0 }}</div>
              <div class="text-sm text-gray-500">{{ t('dashboard.totalIssues') }}</div>
            </div>
            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900/30">
              <svg class="h-6 w-6 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-3xl font-bold text-red-600 dark:text-red-400">{{ health?.metrics.blocked_issues || 0 }}</div>
              <div class="text-sm text-gray-500">{{ t('dashboard.blocked') }}</div>
            </div>
            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-red-100 dark:bg-red-900/30">
              <svg class="h-6 w-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ health?.metrics.total_components || 0 }}</div>
              <div class="text-sm text-gray-500">{{ t('nav.components') }}</div>
            </div>
            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-100 dark:bg-purple-900/30">
              <svg class="h-6 w-6 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
          </div>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-3xl font-bold text-cyan-600 dark:text-cyan-400">{{ health?.metrics.agents_working || 0 }}</div>
              <div class="text-sm text-gray-500">{{ t('system.workers') }}</div>
            </div>
            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-100 dark:bg-cyan-900/30">
              <svg class="h-6 w-6 text-cyan-600 dark:text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Token Consumption Chart -->
      <AgentCostChart :data="tokenUsageData" />

      <!-- Health Check + Sync Queue -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- System Health -->
        <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
            <h2 class="font-semibold text-gray-900 dark:text-white">{{ t('system.health') }}</h2>
          </div>
          <div class="p-5 space-y-4">
            <!-- Neo4j -->
            <div class="flex items-center justify-between rounded-lg border border-gray-200 p-4 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30">
                  <svg class="h-5 w-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                  </svg>
                </div>
                <div>
                  <div class="font-medium text-gray-900 dark:text-white">{{ t('system.neo4j') }}</div>
                  <div class="text-xs text-gray-500">{{ t('system.graphDb') }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-sm text-gray-500">{{ health?.services.neo4j.latency_ms }}ms</span>
                <span class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
                  <span class="h-1.5 w-1.5 rounded-full bg-green-500"></span>
                  {{ t('system.connected') }}
                </span>
              </div>
            </div>

            <!-- API -->
            <div class="flex items-center justify-between rounded-lg border border-gray-200 p-4 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
                  <svg class="h-5 w-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                  </svg>
                </div>
                <div>
                  <div class="font-medium text-gray-900 dark:text-white">{{ t('system.api') }}</div>
                  <div class="text-xs text-gray-500">FastAPI v{{ health?.services.api.version }}</div>
                </div>
              </div>
              <span class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
                <span class="h-1.5 w-1.5 rounded-full bg-green-500"></span>
                {{ t('system.running') }}
              </span>
            </div>

            <!-- Workers -->
            <div class="flex items-center justify-between rounded-lg border border-gray-200 p-4 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/30">
                  <svg class="h-5 w-5 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </div>
                <div>
                  <div class="font-medium text-gray-900 dark:text-white">{{ t('system.workers') }}</div>
                  <div class="text-xs text-gray-500">{{ health?.services.workers.active_count }} active, {{ health?.services.workers.queue_size }} queued</div>
                </div>
              </div>
              <span class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
                <span class="h-1.5 w-1.5 rounded-full bg-green-500"></span>
                {{ t('system.running') }}
              </span>
            </div>
          </div>
        </div>

        <!-- Sync Queue -->
        <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
            <div class="flex items-center justify-between">
              <h2 class="font-semibold text-gray-900 dark:text-white">{{ t('system.syncQueue') }}</h2>
              <div class="flex items-center gap-2">
                <span v-if="syncQueue?.github_connected" class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
                  <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                  {{ t('system.connected') }}
                </span>
                <span v-else class="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400">
                  <span class="h-1.5 w-1.5 rounded-full bg-red-500"></span>
                  {{ t('system.disconnected') }}
                </span>
              </div>
            </div>
          </div>
          <div class="p-5">
            <div v-if="!syncQueue" class="text-center text-sm text-gray-400">{{ t('system.loadingSyncQueue') }}</div>
            <div v-else-if="syncQueue.queue.length === 0" class="rounded-lg border border-dashed border-gray-300 dark:border-gray-600 p-8 text-center">
              <div class="text-sm text-gray-500">{{ t('system.noPendingSync') }}</div>
              <div class="mt-1 text-xs text-gray-400">{{ t('system.allSynced') }}</div>
            </div>
            <div v-else class="space-y-3">
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-500">{{ t('system.pendingItems') }}</span>
                <span class="font-bold text-amber-600 dark:text-amber-400">{{ syncQueue.pending }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-500">{{ t('system.lastSync') }}</span>
                <span class="text-gray-700 dark:text-gray-300">{{ formatTime(syncQueue.last_sync_at) }}</span>
              </div>

              <div class="mt-4 space-y-2">
                <div
                  v-for="item in syncQueue.queue"
                  :key="item.id"
                  class="flex items-center justify-between rounded-lg border border-gray-200 p-3 dark:border-gray-700"
                >
                  <div class="flex items-center gap-2">
                    <span
                      class="inline-flex h-5 items-center rounded px-1.5 text-[10px] font-bold"
                      :class="item.action === 'push' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'"
                    >{{ item.action.toUpperCase() }}</span>
                    <span class="text-sm text-gray-700 dark:text-gray-300">{{ item.resource }}</span>
                    <span class="font-mono text-xs text-gray-400">{{ item.resource_id }}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span v-if="item.retry_count > 0" class="text-xs text-amber-500">Retry {{ item.retry_count }}</span>
                    <span
                      class="inline-flex h-2 w-2 rounded-full"
                      :class="item.status === 'pending' ? 'bg-amber-500' : 'bg-red-500'"
                    ></span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Constraints Summary -->
      <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
          <h2 class="font-semibold text-gray-900 dark:text-white">{{ t('constraints.title') }}</h2>
        </div>
        <div class="p-5">
          <div class="grid grid-cols-3 gap-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ health?.metrics.total_constraints || 0 }}</div>
              <div class="text-xs text-gray-500">{{ t('system.totalRules') }}</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ health?.metrics.active_constraints || 0 }}</div>
              <div class="text-xs text-gray-500">{{ t('system.active') }}</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-400">{{ (health?.metrics.total_constraints || 0) - (health?.metrics.active_constraints || 0) }}</div>
              <div class="text-xs text-gray-500">{{ t('system.inactive') }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Admin Section -->
      <div class="rounded-xl border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/10">
        <div class="border-b border-amber-200 px-5 py-4 dark:border-amber-800">
          <div class="flex items-center gap-2">
            <svg class="h-5 w-5 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
              <h2 class="font-semibold text-amber-800 dark:text-amber-200">{{ t('system.admin') }}</h2>
          </div>
          <p class="mt-1 text-sm text-amber-600 dark:text-amber-400">{{ t('system.protectedActions') }}</p>
        </div>
        <div class="p-5">
          <div class="flex flex-wrap gap-3">
            <button
              :disabled="adminLoading"
              class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              @click="handleSeed"
            >
              {{ adminLoading ? t('common.loading') : t('system.seed') }}
            </button>
            <button
              :disabled="adminLoading"
              class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              @click="handleReset"
            >
              {{ adminLoading ? t('common.loading') : t('system.reset') }}
            </button>
          </div>
          <div v-if="adminMessage" class="mt-3 rounded-lg border p-3 text-sm"
            :class="adminMessage.includes('success')
              ? 'border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400'
              : 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400'"
          >
            {{ adminMessage }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { fetchSystemHealth, fetchSyncQueue, adminSeed, adminReset } from '@/api/systemApi'
import type { SystemHealth, SyncQueue } from '@/types'
import AgentCostChart from '@/components/ui/AgentCostChart.vue'

const { t } = useI18n()

const health = ref<SystemHealth | null>(null)
const syncQueue = ref<SyncQueue | null>(null)
const loading = ref(true)
const adminLoading = ref(false)
const adminMessage = ref('')

const tokenUsageData = computed(() => {
  const data = []
  const models = ['claude-3.5-sonnet', 'gpt-4-turbo', 'gpt-4o']
  const now = new Date()
  for (let i = 13; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 86400000)
    data.push({
      date: date.toISOString(),
      promptTokens: Math.floor(Math.random() * 50000) + 10000,
      completionTokens: Math.floor(Math.random() * 20000) + 5000,
      model: models[Math.floor(Math.random() * models.length)],
    })
  }
  return data
})

function formatTime(iso: string) {
  return new Date(iso).toLocaleString()
}

async function refreshAll() {
  loading.value = true
  try {
    const [h, s] = await Promise.all([fetchSystemHealth(), fetchSyncQueue()])
    health.value = h
    syncQueue.value = s
  } catch (e) {
    console.error('Failed to load system data:', e)
  } finally {
    loading.value = false
  }
}

async function handleSeed() {
  if (!confirm(t('system.seedConfirm'))) return
  adminLoading.value = true
  adminMessage.value = ''
  try {
    const result = await adminSeed('full', false)
    adminMessage.value = result?.message || t('system.seedSuccess')
  } catch (e) {
    adminMessage.value = t('system.seedError')
  } finally {
    adminLoading.value = false
  }
}

async function handleReset() {
  if (!confirm(t('system.resetConfirm'))) return
  adminLoading.value = true
  adminMessage.value = ''
  try {
    const result = await adminReset()
    adminMessage.value = result?.message || t('system.resetSuccess')
  } catch (e) {
    adminMessage.value = t('system.resetError')
  } finally {
    adminLoading.value = false
  }
}

onMounted(refreshAll)
</script>
