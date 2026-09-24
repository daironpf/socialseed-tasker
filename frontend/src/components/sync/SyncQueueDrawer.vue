<template>
  <div class="fixed inset-0 z-50 flex" role="dialog" aria-modal="true" :aria-label="t('syncQueue.title')">
    <div class="absolute inset-0 bg-black/40" @click="$emit('close')" />

    <aside class="relative ml-auto flex h-full w-full max-w-md flex-col bg-white shadow-xl dark:bg-gray-800">
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-gray-200 px-5 py-4 dark:border-gray-700">
        <div>
          <h2 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('syncQueue.title') }}</h2>
          <p class="text-xs text-gray-400">{{ t('syncQueue.subtitle') }}</p>
        </div>
        <div class="flex items-center gap-2">
          <span
            class="rounded-full px-2 py-0.5 text-[10px] font-bold"
            :class="uiStore.syncQueue.length
              ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
              : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'"
          >
            {{ t('syncQueue.count', { n: uiStore.syncQueue.length }) }}
          </span>
          <button
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            :aria-label="t('common.close')"
            @click="$emit('close')"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Toolbar -->
      <div class="flex items-center justify-between gap-2 border-b border-gray-200 px-5 py-3 dark:border-gray-700">
        <div class="text-xs text-gray-500 dark:text-gray-400">
          {{ t(`offline.${uiStore.networkMode}`) }}
          · <span class="font-medium" :class="stateTextClass">{{ stateLabel }}</span>
        </div>
        <button
          class="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          :disabled="!uiStore.syncQueue.length || uiStore.connectionState === 'SYNCING'"
          @click="forceSync"
        >
          {{ uiStore.connectionState === 'SYNCING' ? t('syncQueue.syncing') : t('syncQueue.forceSync') }}
        </button>
      </div>

      <!-- Queue list -->
      <div class="flex-1 space-y-3 overflow-y-auto px-5 py-4">
        <div v-if="!uiStore.syncQueue.length" class="py-12 text-center text-sm text-gray-400">
          {{ t('syncQueue.empty') }}
        </div>

        <div
          v-for="entry in uiStore.syncQueue"
          :key="entry.id"
          class="rounded-xl border p-3"
          :class="entry.status === 'conflict'
            ? 'border-amber-300 bg-amber-50/50 dark:border-amber-700 dark:bg-amber-900/10'
            : 'border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900/40'"
        >
          <div class="flex items-center gap-2">
            <span class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[9px] font-bold uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-300">
              {{ entry.entity }}
            </span>
            <span
              class="rounded px-1.5 py-0.5 text-[9px] font-bold uppercase"
              :class="entry.operation === 'create'
                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
                : 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300'"
            >
              {{ entry.operation }}
            </span>
            <span class="min-w-0 flex-1 truncate text-xs font-medium text-gray-700 dark:text-gray-300">
              {{ summary(entry) }}
            </span>
            <span v-if="entry.status === 'conflict'" class="rounded bg-amber-200 px-1.5 py-0.5 text-[9px] font-bold text-amber-800 dark:bg-amber-800 dark:text-amber-200">
              {{ t('syncQueue.conflict') }}
            </span>
          </div>

          <div class="mt-1.5 flex items-center justify-between text-[10px] text-gray-400">
            <span>{{ formatTime(entry.timestamp) }}<template v-if="entry.retries"> · {{ t('syncQueue.retries', { n: entry.retries }) }}</template></span>
            <span v-if="entry.status === 'pending'" class="font-medium text-amber-600 dark:text-amber-400">{{ t('syncQueue.pending') }}</span>
          </div>

          <!-- Pending actions -->
          <div v-if="entry.status === 'pending'" class="mt-2 flex gap-1.5">
            <button
              class="rounded-lg border border-gray-300 px-2 py-1 text-[10px] font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              @click="uiStore.retryQueued(entry.id)"
            >
              {{ t('syncQueue.retry') }}
            </button>
            <button
              class="rounded-lg border border-red-200 px-2 py-1 text-[10px] font-medium text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-900/20"
              @click="uiStore.removeQueued(entry.id)"
            >
              {{ t('common.delete') }}
            </button>
          </div>

          <!-- Conflict resolution -->
          <div v-else class="mt-2 space-y-2">
            <div class="grid grid-cols-2 gap-1 font-mono text-[9px]">
              <div class="rounded bg-gray-50 p-1.5 dark:bg-gray-900/60">
                <div class="mb-1 font-sans font-bold uppercase text-gray-400">{{ t('syncQueue.local') }}</div>
                <div class="break-all text-gray-600 dark:text-gray-300">{{ shortJson(entry.payload) }}</div>
              </div>
              <div class="rounded bg-gray-50 p-1.5 dark:bg-gray-900/60">
                <div class="mb-1 font-sans font-bold uppercase text-gray-400">{{ t('syncQueue.remote') }}</div>
                <div class="break-all text-gray-600 dark:text-gray-300">{{ shortJson(entry.remotePayload) }}</div>
              </div>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <button
                class="rounded-lg bg-gray-900 px-2 py-1 text-[10px] font-semibold text-white hover:bg-gray-700 dark:bg-gray-600 dark:hover:bg-gray-500"
                @click="applyResolution(entry, 'local')"
              >
                {{ t('syncQueue.keepLocal') }}
              </button>
              <button
                class="rounded-lg bg-sky-600 px-2 py-1 text-[10px] font-semibold text-white hover:bg-sky-700"
                @click="applyResolution(entry, 'remote')"
              >
                {{ t('syncQueue.keepRemote') }}
              </button>
              <button
                class="rounded-lg border border-gray-300 px-2 py-1 text-[10px] font-semibold text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                @click="entry.id === mergingId ? (mergingId = null) : startMerge(entry)"
              >
                {{ t('syncQueue.merge') }}
              </button>
            </div>
            <div v-if="mergingId === entry.id" class="space-y-1.5">
              <textarea
                v-model="mergeDraft"
                rows="4"
                class="w-full resize-none rounded-lg border border-gray-200 bg-gray-50 p-2 font-mono text-[10px] text-gray-800 focus:border-blue-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
              />
              <button
                class="w-full rounded-lg bg-emerald-600 px-2 py-1.5 text-[10px] font-semibold text-white hover:bg-emerald-700"
                @click="applyResolution(entry, 'merge')"
              >
                {{ t('syncQueue.applyMerge') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-gray-200 px-5 py-3 text-[10px] text-gray-400 dark:border-gray-700">
        {{ t('syncQueue.footerHint') }}
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUiStore } from '@/stores/uiStore'
import { useIssuesStore } from '@/stores/issuesStore'
import { usePoliciesStore } from '@/stores/policiesStore'
import type { QueuedMutation } from '@/utils/offlineQueue'

defineEmits<{ close: [] }>()

const { t, d } = useI18n()
const uiStore = useUiStore()
const issuesStore = useIssuesStore()
const policiesStore = usePoliciesStore()

const mergingId = ref<string | null>(null)
const mergeDraft = ref('')

const stateLabel = computed(() => {
  switch (uiStore.connectionState) {
    case 'SYNCING':
      return t('sync.syncing')
    case 'OFFLINE_QUEUED':
      return t('sync.offlineQueued', { count: uiStore.pendingSyncCount })
    case 'DEGRADED':
      return t('offline.degraded')
    default:
      return t('sync.synced')
  }
})

const stateTextClass = computed(() => {
  switch (uiStore.connectionState) {
    case 'SYNCING':
      return 'text-blue-600 dark:text-blue-400'
    case 'OFFLINE_QUEUED':
      return 'text-amber-600 dark:text-amber-400'
    case 'DEGRADED':
      return 'text-amber-600 dark:text-amber-400'
    default:
      return 'text-emerald-600 dark:text-emerald-400'
  }
})

function summary(entry: QueuedMutation): string {
  const payload = entry.payload as Record<string, string | undefined>
  if (entry.operation === 'create') return payload.title || payload.name || entry.entityId || '—'
  return entry.entityId || '—'
}

function shortJson(value: unknown): string {
  if (!value) return '—'
  const json = JSON.stringify(value)
  return json.length > 140 ? `${json.slice(0, 140)}…` : json
}

function formatTime(iso: string): string {
  try {
    return d(new Date(iso), 'short')
  } catch {
    return iso.slice(11, 16)
  }
}

function forceSync() {
  uiStore.flushQueue()
}

function startMerge(entry: QueuedMutation) {
  mergingId.value = entry.id
  mergeDraft.value = JSON.stringify(entry.remotePayload ?? entry.payload, null, 2)
}

function parseMerge(): Record<string, unknown> | null {
  try {
    const parsed = JSON.parse(mergeDraft.value)
    if (parsed && typeof parsed === 'object') return parsed as Record<string, unknown>
  } catch {
    // invalid JSON -> caller keeps drawer open
  }
  return null
}

async function applyResolution(entry: QueuedMutation, resolution: 'local' | 'remote' | 'merge') {
  if (resolution === 'remote' || resolution === 'merge') {
    const payload = resolution === 'remote' ? entry.remotePayload : parseMerge()
    if (!payload) return
    if (entry.entity === 'issue' && entry.entityId) {
      await issuesStore.updateIssue(entry.entityId, payload as never, { skipOfflineQueue: true })
    } else if (entry.entity === 'policy' && entry.entityId) {
      await policiesStore.updatePolicy(entry.entityId, payload as never, { skipOfflineQueue: true })
    }
  }
  uiStore.resolveConflict(entry.id)
  mergingId.value = null
  mergeDraft.value = ''
}
</script>
