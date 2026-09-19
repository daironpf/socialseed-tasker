<template>
  <div class="flex h-[calc(100vh-8rem)] gap-4">
    <!-- Left Panel: Inbox -->
    <div class="flex w-96 flex-shrink-0 flex-col rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <!-- Header -->
      <div class="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">{{ t('hitlCenter.title') }}</h2>
          <span
            v-if="hitlStore.pendingCount > 0"
            class="flex h-6 min-w-6 items-center justify-center rounded-full bg-red-500 px-2 text-xs font-bold text-white"
          >
            {{ hitlStore.pendingCount }}
          </span>
        </div>
        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ t('hitlCenter.subtitle') }}</p>
      </div>

      <!-- Filters -->
      <div class="border-b border-gray-100 px-4 py-2 dark:border-gray-700">
        <div class="flex gap-1">
          <button
            v-for="filter in statusFilters"
            :key="filter.value"
            class="rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors"
            :class="activeStatusFilter === filter.value
              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
              : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'"
            @click="activeStatusFilter = filter.value"
          >
            {{ filter.label }}
            <span v-if="filter.count > 0" class="ml-1 rounded-full bg-gray-200 px-1 text-[9px] dark:bg-gray-600">{{ filter.count }}</span>
          </button>
        </div>
        <div class="mt-2 flex gap-1">
          <select
            v-model="severityFilter"
            class="rounded-lg border border-gray-200 bg-gray-50 px-2 py-1 text-[11px] text-gray-700 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
          >
            <option value="all">{{ t('hitlCenter.allSeverities') }}</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
          <select
            v-model="componentFilter"
            class="flex-1 rounded-lg border border-gray-200 bg-gray-50 px-2 py-1 text-[11px] text-gray-700 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
          >
            <option value="all">{{ t('hitlCenter.allComponents') }}</option>
            <option v-for="comp in uniqueComponents" :key="comp" :value="comp">{{ comp }}</option>
          </select>
        </div>
      </div>

      <!-- Request List -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="filteredRequests.length === 0" class="flex flex-col items-center justify-center py-12 px-4">
          <svg class="h-12 w-12 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="mt-3 text-sm text-gray-500 dark:text-gray-400">{{ t('hitlCenter.noRequests') }}</p>
        </div>

        <button
          v-for="req in filteredRequests"
          :key="req.id"
          class="w-full border-b border-gray-50 px-4 py-3 text-left transition-colors hover:bg-gray-50 dark:border-gray-700/50 dark:hover:bg-gray-700/30"
          :class="hitlStore.selectedRequestId === req.id ? 'bg-blue-50 dark:bg-blue-900/10' : ''"
          @click="hitlStore.selectRequest(req.id)"
        >
          <div class="flex items-start gap-3">
            <div class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-gray-100 text-sm dark:bg-gray-700">
              {{ hitlStore.getTypeIcon(req.type) }}
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span class="truncate text-sm font-semibold text-gray-900 dark:text-white">{{ req.title }}</span>
                <span
                  class="flex-shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold"
                  :class="hitlStore.getSeverityColor(req.severity)"
                >
                  {{ req.severity }}
                </span>
              </div>
              <div class="mt-1 flex items-center gap-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ req.agentName }}</span>
                <span class="text-gray-300 dark:text-gray-600">·</span>
                <span class="text-xs text-gray-400 dark:text-gray-500">{{ req.issueId }}</span>
                <span class="text-gray-300 dark:text-gray-600">·</span>
                <span class="text-xs text-gray-400 dark:text-gray-500">{{ hitlStore.formatTimeAgo(req.createdAt) }}</span>
              </div>
              <div class="mt-1.5 flex items-center gap-1">
                <span
                  class="rounded px-1.5 py-0.5 text-[10px] font-medium"
                  :class="hitlStore.getStatusColor(req.status)"
                >
                  {{ t(`hitlCenter.statuses.${req.status}`) }}
                </span>
                <span class="text-[10px] text-gray-400 dark:text-gray-500">{{ req.component }}</span>
              </div>
            </div>
          </div>
        </button>
      </div>
    </div>

    <!-- Right Panel: Detail View -->
    <div class="flex flex-1 flex-col overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <!-- No Selection -->
      <div v-if="!hitlStore.selectedRequest" class="flex flex-1 flex-col items-center justify-center">
        <svg class="h-16 w-16 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="mt-4 text-sm text-gray-500 dark:text-gray-400">{{ t('hitlCenter.selectRequest') }}</p>
      </div>

      <template v-else>
        <!-- Detail Header -->
        <div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <div class="flex items-start justify-between">
            <div>
              <div class="flex items-center gap-2">
                <span class="text-lg font-bold text-gray-900 dark:text-white">{{ hitlStore.selectedRequest.title }}</span>
                <span
                  class="rounded-full px-2.5 py-0.5 text-xs font-bold"
                  :class="hitlStore.getSeverityColor(hitlStore.selectedRequest.severity)"
                >
                  {{ hitlStore.selectedRequest.severity }}
                </span>
              </div>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ hitlStore.selectedRequest.description }}</p>
              <div class="mt-2 flex items-center gap-3 text-xs text-gray-400 dark:text-gray-500">
                <span>{{ hitlStore.selectedRequest.agentName }}</span>
                <span>·</span>
                <span>{{ hitlStore.selectedRequest.issueId }} — {{ hitlStore.selectedRequest.issueTitle }}</span>
                <span>·</span>
                <span>{{ hitlStore.selectedRequest.component }}</span>
                <span>·</span>
                <span>{{ hitlStore.formatTimeAgo(hitlStore.selectedRequest.createdAt) }}</span>
              </div>
            </div>

            <!-- Actions (only for pending) -->
            <div v-if="hitlStore.selectedRequest.status === 'pending'" class="flex items-center gap-2">
              <button
                class="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors"
                @click="handleApprove"
              >
                <svg class="mr-1.5 inline h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                {{ t('hitlCenter.approve') }}
              </button>
              <button
                class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
                @click="showModifyForm = !showModifyForm"
              >
                <svg class="mr-1.5 inline h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                {{ t('hitlCenter.modify') }}
              </button>
              <button
                class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
                @click="showRejectForm = !showRejectForm"
              >
                <svg class="mr-1.5 inline h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
                {{ t('hitlCenter.reject') }}
              </button>
            </div>

            <!-- Status badge for reviewed -->
            <div v-else>
              <span
                class="rounded-full px-3 py-1.5 text-sm font-bold"
                :class="hitlStore.getStatusColor(hitlStore.selectedRequest.status)"
              >
                {{ t(`hitlCenter.statuses.${hitlStore.selectedRequest.status}`) }}
              </span>
            </div>
          </div>

          <!-- Reject Form -->
          <div v-if="showRejectForm && hitlStore.selectedRequest.status === 'pending'" class="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/10">
            <label class="block text-sm font-medium text-red-700 dark:text-red-400">{{ t('hitlCenter.rejectFeedback') }}</label>
            <textarea
              v-model="rejectFeedback"
              rows="3"
              class="mt-2 w-full rounded-lg border border-red-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-red-800 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
              :placeholder="t('hitlCenter.rejectPlaceholder')"
            ></textarea>
            <div class="mt-3 flex justify-end gap-2">
              <button
                class="rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                @click="showRejectForm = false; rejectFeedback = ''"
              >
                {{ t('common.cancel') }}
              </button>
              <button
                class="rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                :disabled="!rejectFeedback.trim()"
                @click="handleReject"
              >
                {{ t('hitlCenter.confirmReject') }}
              </button>
            </div>
          </div>

          <!-- Modify Form -->
          <div v-if="showModifyForm && hitlStore.selectedRequest.status === 'pending'" class="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-900/10">
            <label class="block text-sm font-medium text-amber-700 dark:text-amber-400">{{ t('hitlCenter.modifyFeedback') }}</label>
            <textarea
              v-model="modifyFeedback"
              rows="3"
              class="mt-2 w-full rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-amber-800 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
              :placeholder="t('hitlCenter.modifyPlaceholder')"
            ></textarea>
            <div class="mt-3 flex justify-end gap-2">
              <button
                class="rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                @click="showModifyForm = false; modifyFeedback = ''"
              >
                {{ t('common.cancel') }}
              </button>
              <button
                class="rounded-lg bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
                :disabled="!modifyFeedback.trim()"
                @click="handleModify"
              >
                {{ t('hitlCenter.confirmModify') }}
              </button>
            </div>
          </div>

          <!-- Reviewed feedback -->
          <div v-if="hitlStore.selectedRequest.feedback" class="mt-3 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-600 dark:bg-gray-700/50">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('hitlCenter.reviewFeedback') }}</p>
            <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ hitlStore.selectedRequest.feedback }}</p>
          </div>
        </div>

        <!-- Split View: Diff + Impact -->
        <div class="flex flex-1 overflow-hidden">
          <!-- Diff Panel -->
          <div class="flex flex-1 flex-col overflow-hidden border-r border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-2 border-b border-gray-100 px-4 py-2 dark:border-gray-700">
              <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span class="text-xs font-semibold text-gray-700 dark:text-gray-300">{{ t('hitlCenter.codeChanges') }}</span>
              <span class="text-[10px] text-gray-400 dark:text-gray-500">({{ hitlStore.selectedRequest.diffs.length }} {{ t('hitlCenter.files') }})</span>
            </div>
            <div class="flex-1 overflow-y-auto p-4">
              <div v-if="hitlStore.selectedRequest.diffs.length === 0" class="flex flex-col items-center justify-center py-8">
                <p class="text-sm text-gray-400 dark:text-gray-500">{{ t('hitlCenter.noDiffs') }}</p>
              </div>
              <div v-else class="space-y-4">
                <DiffViewer
                  v-for="diff in hitlStore.selectedRequest.diffs"
                  :key="diff.filename"
                  :content="diff.content"
                  :filename="diff.filename"
                />
              </div>
            </div>
          </div>

          <!-- Impact Panel -->
          <div class="flex w-80 flex-shrink-0 flex-col overflow-hidden">
            <div class="flex items-center gap-2 border-b border-gray-100 px-4 py-2 dark:border-gray-700">
              <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span class="text-xs font-semibold text-gray-700 dark:text-gray-300">{{ t('hitlCenter.impactAnalysis') }}</span>
            </div>
            <div class="flex-1 overflow-y-auto p-4">
              <!-- Risk Level -->
              <div class="mb-4">
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('hitlCenter.riskLevel') }}</p>
                <span
                  class="mt-1 inline-block rounded-full px-3 py-1 text-sm font-bold"
                  :class="riskBadgeClass(hitlStore.selectedRequest.impact.riskLevel)"
                >
                  {{ hitlStore.selectedRequest.impact.riskLevel }}
                </span>
              </div>

              <!-- Impact Stats -->
              <div class="mb-4 grid grid-cols-3 gap-2">
                <div class="rounded-lg bg-gray-50 p-2.5 text-center dark:bg-gray-700/50">
                  <p class="text-lg font-bold text-gray-900 dark:text-white">{{ hitlStore.selectedRequest.impact.totalAffected }}</p>
                  <p class="text-[10px] text-gray-500 dark:text-gray-400">{{ t('hitlCenter.totalAffected') }}</p>
                </div>
                <div class="rounded-lg bg-blue-50 p-2.5 text-center dark:bg-blue-900/20">
                  <p class="text-lg font-bold text-blue-700 dark:text-blue-400">{{ hitlStore.selectedRequest.impact.directDeps }}</p>
                  <p class="text-[10px] text-blue-600 dark:text-blue-500">{{ t('hitlCenter.direct') }}</p>
                </div>
                <div class="rounded-lg bg-amber-50 p-2.5 text-center dark:bg-amber-900/20">
                  <p class="text-lg font-bold text-amber-700 dark:text-amber-400">{{ hitlStore.selectedRequest.impact.transitiveDeps }}</p>
                  <p class="text-[10px] text-amber-600 dark:text-amber-500">{{ t('hitlCenter.transitive') }}</p>
                </div>
              </div>

              <!-- Affected Components -->
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('hitlCenter.affectedComponents') }}</p>
                <div class="mt-2 flex flex-wrap gap-1.5">
                  <span
                    v-for="comp in hitlStore.selectedRequest.impact.affectedComponents"
                    :key="comp"
                    class="rounded-full bg-purple-100 px-2.5 py-1 text-xs font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400"
                  >
                    {{ comp }}
                  </span>
                </div>
              </div>

              <!-- Command -->
              <div class="mt-4">
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('hitlCenter.command') }}</p>
                <div class="mt-1.5 rounded-lg bg-gray-900 p-3 font-mono text-xs text-green-400">
                  {{ hitlStore.selectedRequest.command }}
                </div>
              </div>

              <!-- Target -->
              <div v-if="hitlStore.selectedRequest.target" class="mt-3">
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('hitlCenter.target') }}</p>
                <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ hitlStore.selectedRequest.target }}</p>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useHitlStore } from '@/stores/hitlStore'
import DiffViewer from '@/components/ui/DiffViewer.vue'
import type { HITLRequestStatus } from '@/types/hitl'

const { t } = useI18n()
const hitlStore = useHitlStore()

const activeStatusFilter = ref<'all' | HITLRequestStatus>('all')
const severityFilter = ref('all')
const componentFilter = ref('all')
const showRejectForm = ref(false)
const showModifyForm = ref(false)
const rejectFeedback = ref('')
const modifyFeedback = ref('')

const uniqueComponents = computed(() => {
  const comps = new Set(hitlStore.requests.map(r => r.component))
  return Array.from(comps).sort()
})

const statusFilters = computed(() => [
  { value: 'all' as const, label: t('hitlCenter.all'), count: hitlStore.requests.length },
  { value: 'pending' as const, label: t('hitlCenter.pending'), count: hitlStore.pendingRequests.length },
  { value: 'approved' as const, label: t('hitlCenter.approved'), count: hitlStore.approvedRequests.length },
  { value: 'rejected' as const, label: t('hitlCenter.rejected'), count: hitlStore.rejectedRequests.length },
  { value: 'modified' as const, label: t('hitlCenter.modified'), count: hitlStore.modifiedRequests.length },
])

const filteredRequests = computed(() => {
  let result = hitlStore.requests
  if (activeStatusFilter.value !== 'all') {
    result = result.filter(r => r.status === activeStatusFilter.value)
  }
  if (severityFilter.value !== 'all') {
    result = result.filter(r => r.severity === severityFilter.value)
  }
  if (componentFilter.value !== 'all') {
    result = result.filter(r => r.component === componentFilter.value)
  }
  return result
})

function riskBadgeClass(level: string): string {
  const map: Record<string, string> = {
    LOW: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
    MEDIUM: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    HIGH: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
    CRITICAL: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  }
  return map[level] || map.MEDIUM
}

function handleApprove() {
  if (!hitlStore.selectedRequest) return
  hitlStore.approveRequest(hitlStore.selectedRequest.id)
}

function handleReject() {
  if (!hitlStore.selectedRequest || !rejectFeedback.value.trim()) return
  hitlStore.rejectRequest(hitlStore.selectedRequest.id, rejectFeedback.value.trim())
  rejectFeedback.value = ''
  showRejectForm.value = false
}

function handleModify() {
  if (!hitlStore.selectedRequest || !modifyFeedback.value.trim()) return
  hitlStore.modifyRequest(hitlStore.selectedRequest.id, modifyFeedback.value.trim())
  modifyFeedback.value = ''
  showModifyForm.value = false
}

onMounted(() => {
  hitlStore.fetchRequests()
})
</script>
