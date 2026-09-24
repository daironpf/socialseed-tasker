<template>
  <section class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
    <header class="flex flex-wrap items-center justify-between gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-700">
      <div>
        <h2 class="text-base font-semibold text-gray-900 dark:text-white">
          {{ t('governanceMatrix.queue.title') }}
        </h2>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          {{ t('governanceMatrix.queue.subtitle', { count: pending.length }) }}
        </p>
      </div>
      <span
        v-if="pending.length"
        class="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
      >
        {{ pending.length }}
      </span>
    </header>

    <div v-if="!pending.length" class="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
      {{ t('governanceMatrix.queue.empty') }}
    </div>

    <div v-else class="grid grid-cols-1 gap-0 lg:grid-cols-5">
      <!-- Queue list -->
      <div class="max-h-96 overflow-y-auto border-b border-gray-200 lg:col-span-2 lg:border-r lg:border-b-0 dark:border-gray-700">
        <button
          v-for="req in pending"
          :key="req.id"
          class="block w-full border-b border-gray-100 px-4 py-3 text-left transition-colors last:border-b-0 dark:border-gray-700/50"
          :class="req.id === selectedId ? 'bg-blue-50 dark:bg-blue-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-700/40'"
          @click="selectedId = req.id"
        >
          <div class="mb-1 flex items-center gap-2">
            <span class="truncate text-sm font-medium text-gray-900 dark:text-white">{{ req.title }}</span>
            <span
              class="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-bold"
              :class="hitlStore.getSeverityColor(req.severity)"
            >
              {{ req.severity }}
            </span>
          </div>
          <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <span>{{ req.agentAvatar }} {{ req.agentName }}</span>
            <span>·</span>
            <span>{{ hitlStore.getTypeIcon(req.type) }}</span>
            <span class="truncate">{{ req.issueTitle || req.component }}</span>
          </div>
        </button>
      </div>

      <!-- Detail -->
      <div v-if="selected" class="lg:col-span-3">
        <div class="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
          <div class="mb-1 flex items-start justify-between gap-2">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ selected.title }}</h3>
            <span class="shrink-0 text-xs text-gray-400">{{ hitlStore.formatTimeAgo(selected.createdAt) }}</span>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400">{{ selected.description }}</p>
          <pre
            v-if="selected.command"
            class="mt-2 overflow-x-auto rounded bg-gray-900 px-2 py-1.5 font-mono text-[11px] text-gray-100"
          >{{ selected.command }}</pre>
        </div>

        <!-- Impact -->
        <div class="grid grid-cols-3 gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-700">
          <div class="rounded bg-gray-50 p-2 text-center dark:bg-gray-900/40">
            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ selected.impact.totalAffected }}</div>
            <div class="text-[10px] uppercase text-gray-500">{{ t('governanceMatrix.queue.totalAffected') }}</div>
          </div>
          <div class="rounded bg-gray-50 p-2 text-center dark:bg-gray-900/40">
            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ selected.impact.directDeps }}</div>
            <div class="text-[10px] uppercase text-gray-500">{{ t('governanceMatrix.queue.directDeps') }}</div>
          </div>
          <div class="rounded bg-gray-50 p-2 text-center dark:bg-gray-900/40">
            <div
              class="text-sm font-bold"
              :class="riskColor(selected.impact.riskLevel)"
            >
              {{ selected.impact.riskLevel }}
            </div>
            <div class="text-[10px] uppercase text-gray-500">{{ t('governanceMatrix.queue.risk') }}</div>
          </div>
        </div>

        <!-- Diff -->
        <div class="max-h-64 overflow-y-auto border-b border-gray-200 p-3 dark:border-gray-700">
          <template v-if="selected.diffs.length">
            <DiffViewer
              v-for="d in selected.diffs"
              :key="d.filename"
              :content="d.content"
              :filename="d.filename"
            />
          </template>
          <p v-else class="py-3 text-center text-xs text-gray-400">
            {{ t('governanceMatrix.queue.noDiffs') }}
          </p>
        </div>

        <!-- Actions -->
        <div class="px-4 py-3">
          <div v-if="!pendingAction" class="flex flex-wrap gap-2">
            <button
              class="min-h-[40px] flex-1 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
              @click="pendingAction = 'approve'"
            >
              {{ t('governanceMatrix.queue.approve') }}
            </button>
            <button
              class="min-h-[40px] flex-1 rounded-lg bg-amber-600 px-3 py-2 text-sm font-medium text-white hover:bg-amber-700"
              @click="pendingAction = 'modify'"
            >
              {{ t('governanceMatrix.queue.requestChanges') }}
            </button>
            <button
              class="min-h-[40px] flex-1 rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700"
              @click="pendingAction = 'reject'"
            >
              {{ t('governanceMatrix.queue.reject') }}
            </button>
          </div>

          <div v-else>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-300">
              {{ pendingAction === 'reject' ? t('governanceMatrix.queue.rejectFeedback') : t('governanceMatrix.queue.modifyFeedback') }}
            </label>
            <textarea
              v-model="feedback"
              rows="2"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :placeholder="pendingAction === 'reject' ? t('governanceMatrix.queue.rejectPlaceholder') : t('governanceMatrix.queue.modifyPlaceholder')"
            />
            <div class="mt-2 flex justify-end gap-2">
              <button
                class="min-h-[36px] rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                @click="pendingAction = null; feedback = ''"
              >
                {{ t('common.cancel') }}
              </button>
              <button
                v-if="pendingAction !== 'approve' && !feedback.trim()"
                disabled
                class="min-h-[36px] cursor-not-allowed rounded-lg bg-gray-300 px-3 py-1.5 text-sm font-medium text-white opacity-60 dark:bg-gray-600"
              >
                {{ t('governanceMatrix.queue.confirm') }}
              </button>
              <button
                v-else
                class="min-h-[36px] rounded-lg px-3 py-1.5 text-sm font-medium text-white"
                :class="pendingAction === 'reject' ? 'bg-red-600 hover:bg-red-700' : pendingAction === 'modify' ? 'bg-amber-600 hover:bg-amber-700' : 'bg-emerald-600 hover:bg-emerald-700'"
                @click="confirm"
              >
                {{ t('governanceMatrix.queue.confirm') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useHitlStore } from '@/stores/hitlStore'
import { useIssuesStore } from '@/stores/issuesStore'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { useToast } from '@/composables/useToast'
import DiffViewer from '@/components/ui/DiffViewer.vue'
import { IssueStatus } from '@/types'
import type { HITLRequest } from '@/types/hitl'

const { t } = useI18n()
const hitlStore = useHitlStore()
const issuesStore = useIssuesStore()
const notificationsStore = useNotificationsStore()
const toast = useToast()

const selectedId = ref<string | null>(null)
const pendingAction = ref<'approve' | 'reject' | 'modify' | null>(null)
const feedback = ref('')

const pending = computed(() => hitlStore.pendingRequests)
const selected = computed<HITLRequest | null>(
  () => pending.value.find((r) => r.id === selectedId.value) || pending.value[0] || null,
)

watch(
  pending,
  (list) => {
    if (!list.some((r) => r.id === selectedId.value)) {
      selectedId.value = list[0]?.id || null
    }
    if (selectedId.value && !list.some((r) => r.id === selectedId.value)) {
      pendingAction.value = null
    }
  },
  { immediate: true },
)

function riskColor(level: string): string {
  if (level === 'CRITICAL') return 'text-red-600 dark:text-red-400'
  if (level === 'HIGH') return 'text-amber-600 dark:text-amber-400'
  if (level === 'MEDIUM') return 'text-yellow-600 dark:text-yellow-400'
  return 'text-emerald-600 dark:text-emerald-400'
}

async function confirm() {
  const req = selected.value
  if (!req || !pendingAction.value) return
  const chosen = pendingAction.value
  const fb = feedback.value.trim()
  if (chosen !== 'approve' && !fb) return

  const success = await hitlStore.resolveAction(req.id, chosen, fb || undefined)
  if (!success) {
    toast.error(t('hitlQuickAction.failed'))
    return
  }

  const statusMap = {
    approve: IssueStatus.IN_PROGRESS,
    reject: IssueStatus.OPEN,
    modify: IssueStatus.IN_PROGRESS,
  } as const
  if (req.issueId) {
    try {
      await issuesStore.updateIssue(req.issueId, { status: statusMap[chosen] })
    } catch {
      // mock may not have the issue
    }
  }

  toast.success(t(`hitlQuickAction.resolved_${chosen === 'approve' ? 'approve' : chosen === 'reject' ? 'reject' : 'modify'}`, { title: req.title }))
  notificationsStore.addNotification({
    title: t('hitlQuickAction.resolvedTitle'),
    message: t(`hitlQuickAction.resolved_${chosen}`, { title: req.title }),
    category: 'hitl',
    requiresAction: false,
    linkTo: { name: 'HITLCommandCenter' },
    hitlRequestId: req.id,
  })

  pendingAction.value = null
  feedback.value = ''
  selectedId.value = null
}
</script>
