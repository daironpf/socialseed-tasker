<template>
  <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
    <div class="flex items-center justify-between mb-3">
      <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('githubSync.title') }}</h4>
      <span
        class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-bold"
        :class="statusClass"
      >
        <span class="h-1.5 w-1.5 rounded-full" :class="statusDotClass"></span>
        {{ t(`githubSync.status.${github.sync_status}`) }}
      </span>
    </div>

    <div class="space-y-2">
      <div class="flex items-center gap-2">
        <svg class="h-4 w-4 text-gray-500 dark:text-gray-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
        </svg>
        <a
          :href="github.github_url"
          target="_blank"
          rel="noopener noreferrer"
          class="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 hover:underline"
        >
          #{{ github.issue_number }}
        </a>
        <a
          v-if="github.pr_url"
          :href="github.pr_url"
          target="_blank"
          rel="noopener noreferrer"
          class="text-[10px] font-medium text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-300 hover:underline"
        >
          {{ t('githubSync.prView') }}
        </a>
      </div>

      <div class="text-[10px] text-gray-500 dark:text-gray-400">
        {{ t('githubSync.lastSynced') }}:
        {{ github.last_synced_at ? new Date(github.last_synced_at).toLocaleString() : t('githubSync.neverSynced') }}
      </div>

      <div
        v-if="github.error"
        class="rounded-md bg-red-50 border border-red-200 px-2.5 py-1.5 text-[11px] text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-300"
      >
        {{ t('githubSync.error') }}: {{ github.error }}
      </div>

      <div
        v-if="conflict"
        class="rounded-md border border-orange-300 bg-orange-50 p-3 dark:border-orange-700 dark:bg-orange-900/20"
      >
        <div class="text-[11px] font-semibold text-orange-800 dark:text-orange-300">
          {{ t('githubSync.conflict') }}
        </div>
        <p class="mt-0.5 text-[10px] text-orange-700 dark:text-orange-400">
          {{ t('githubSync.conflictHint') }}
        </p>

        <div class="mt-2 space-y-2">
          <div
            v-for="field in conflict.fields"
            :key="field"
            class="rounded border border-orange-200 bg-white p-2 dark:border-orange-800 dark:bg-gray-900"
          >
            <div class="text-[10px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
              {{ field }}
            </div>
            <template v-if="merging">
              <label class="mt-1 block text-[10px] text-gray-500 dark:text-gray-400">
                {{ t('githubSync.local') }}
              </label>
              <textarea
                v-model="mergeValues[field]"
                rows="2"
                class="mt-0.5 w-full rounded border border-gray-300 bg-white px-2 py-1 text-xs text-gray-800 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
              ></textarea>
            </template>
            <template v-else>
              <div class="mt-1 grid grid-cols-2 gap-2">
                <div>
                  <div class="text-[9px] font-semibold uppercase text-gray-500 dark:text-gray-400">
                    {{ t('githubSync.local') }}
                  </div>
                  <div class="break-words text-[11px] text-gray-700 dark:text-gray-300">
                    {{ displayValue(conflict.local[field]) }}
                  </div>
                </div>
                <div>
                  <div class="text-[9px] font-semibold uppercase text-gray-500 dark:text-gray-400">
                    {{ t('githubSync.remote') }}
                  </div>
                  <div class="break-words text-[11px] text-gray-700 dark:text-gray-300">
                    {{ displayValue(conflict.remote[field]) }}
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <div class="mt-2.5 flex flex-wrap gap-1.5">
          <template v-if="!merging">
            <button
              :disabled="busy"
              class="rounded-md border border-gray-300 bg-white px-2.5 py-1 text-[11px] font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              @click="resolve('local')"
            >
              {{ t('githubSync.keepLocal') }}
            </button>
            <button
              :disabled="busy"
              class="rounded-md border border-gray-300 bg-white px-2.5 py-1 text-[11px] font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              @click="resolve('remote')"
            >
              {{ t('githubSync.keepRemote') }}
            </button>
            <button
              :disabled="busy"
              class="rounded-md border border-blue-300 bg-blue-50 px-2.5 py-1 text-[11px] font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-50 dark:border-blue-700 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:bg-blue-900/50"
              @click="startMerge"
            >
              {{ t('githubSync.merge') }}
            </button>
          </template>
          <template v-else>
            <button
              :disabled="busy"
              class="rounded-md border border-blue-500 bg-blue-600 px-2.5 py-1 text-[11px] font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              @click="applyMerge"
            >
              {{ busy ? t('githubSync.syncing') : t('githubSync.applyMerge') }}
            </button>
            <button
              :disabled="busy"
              class="rounded-md border border-gray-300 bg-white px-2.5 py-1 text-[11px] font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              @click="merging = false"
            >
              {{ t('issues.cancel') }}
            </button>
          </template>
        </div>
      </div>

      <div
        v-if="actionError"
        class="rounded-md bg-red-50 border border-red-200 px-2.5 py-1.5 text-[11px] text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-300"
      >
        {{ t('githubSync.actionFailed') }}: {{ actionError }}
      </div>

      <button
        :disabled="busy"
        class="mt-2 inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2.5 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        @click="resync"
      >
        <svg v-if="!busy" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <svg v-else class="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        {{ busy ? t('githubSync.syncing') : t('githubSync.forceResync') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { GitHubSync, Issue } from '../../types'
import { resyncIssue, resolveConflict, type ConflictResolution } from '../../api/githubSyncApi'

const { t } = useI18n()

const props = defineProps<{
  issueId: string
  github: GitHubSync
}>()

const emit = defineEmits<{
  (e: 'sync:updated', issue: Issue): void
}>()

const busy = ref(false)
const actionError = ref<string | null>(null)
const merging = ref(false)
const mergeValues = ref<Record<string, string>>({})

const conflict = computed(() => {
  const c = props.github.conflict
  return c && c.fields && c.fields.length > 0 ? c : null
})

const statusClass = computed(() => {
  switch (props.github.sync_status) {
    case 'SYNCED': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
    case 'PENDING_PUSH': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
    case 'ERROR': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
    case 'CONFLICT': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'
    default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  }
})

const statusDotClass = computed(() => {
  switch (props.github.sync_status) {
    case 'SYNCED': return 'bg-green-500'
    case 'PENDING_PUSH': return 'bg-yellow-500'
    case 'ERROR': return 'bg-red-500'
    case 'CONFLICT': return 'bg-orange-500'
    default: return 'bg-gray-500'
  }
})

function displayValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return value
  return JSON.stringify(value)
}

function errorMessage(err: unknown): string {
  return err instanceof Error && err.message ? err.message : t('githubSync.actionFailed')
}

async function resync() {
  busy.value = true
  actionError.value = null
  try {
    const issue = await resyncIssue(props.issueId)
    emit('sync:updated', issue)
  } catch (err) {
    actionError.value = errorMessage(err)
  } finally {
    busy.value = false
  }
}

function startMerge() {
  const c = conflict.value
  if (!c) return
  const values: Record<string, string> = {}
  for (const field of c.fields) {
    const local = c.local[field]
    values[field] = typeof local === 'string' ? local : displayValue(local)
  }
  mergeValues.value = values
  merging.value = true
}

async function resolve(resolution: ConflictResolution, fields?: Record<string, unknown>) {
  busy.value = true
  actionError.value = null
  try {
    const issue = await resolveConflict(props.issueId, resolution, fields)
    merging.value = false
    emit('sync:updated', issue)
  } catch (err) {
    actionError.value = errorMessage(err)
  } finally {
    busy.value = false
  }
}

function applyMerge() {
  resolve('merge', { ...mergeValues.value })
}
</script>
