<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    @click.self="$emit('close')"
    role="dialog"
    aria-modal="true"
  >
    <div class="w-full max-w-lg rounded-xl bg-white shadow-2xl dark:bg-gray-800 overflow-hidden">
      <!-- Header -->
      <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-start gap-3">
            <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-gray-100 text-lg dark:bg-gray-700">
              {{ hitlStore.getTypeIcon(request.type) }}
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <h3 class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ request.title }}</h3>
                <span
                  class="flex-shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold"
                  :class="hitlStore.getSeverityColor(request.severity)"
                >
                  {{ request.severity }}
                </span>
              </div>
              <p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                {{ request.agentAvatar }} {{ request.agentName }} · {{ request.issueId }}
              </p>
            </div>
          </div>
          <button
            class="flex-shrink-0 rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
            :aria-label="t('common.close')"
            @click="$emit('close')"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Body -->
      <div class="px-5 py-4 space-y-4 max-h-[60vh] overflow-y-auto">
        <p class="text-sm text-gray-600 dark:text-gray-400">{{ request.description }}</p>

        <!-- Command -->
        <div>
          <label class="block text-[10px] font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-1">
            {{ t('hitlQuickAction.command') }}
          </label>
          <pre class="rounded-lg bg-gray-900 p-3 text-xs font-mono text-green-400 overflow-x-auto">{{ request.command }}</pre>
        </div>

        <!-- Impact -->
        <div class="grid grid-cols-3 gap-2">
          <div class="rounded-lg bg-gray-50 p-2.5 text-center dark:bg-gray-700/50">
            <p class="text-lg font-bold text-gray-900 dark:text-white">{{ request.impact.totalAffected }}</p>
            <p class="text-[10px] text-gray-500 dark:text-gray-400">{{ t('hitlQuickAction.affected') }}</p>
          </div>
          <div class="rounded-lg bg-blue-50 p-2.5 text-center dark:bg-blue-900/20">
            <p class="text-lg font-bold text-blue-700 dark:text-blue-400">{{ request.impact.directDeps }}</p>
            <p class="text-[10px] text-blue-600 dark:text-blue-500">{{ t('hitlQuickAction.direct') }}</p>
          </div>
          <div class="rounded-lg bg-amber-50 p-2.5 text-center dark:bg-amber-900/20">
            <p class="text-lg font-bold text-amber-700 dark:text-amber-400">{{ request.impact.riskLevel === 'CRITICAL' ? '!' : request.impact.riskLevel === 'HIGH' ? '!!' : 'OK' }}</p>
            <p class="text-[10px] text-amber-600 dark:text-amber-500">{{ request.impact.riskLevel }}</p>
          </div>
        </div>

        <!-- Feedback textarea (for reject/modify) -->
        <div v-if="action === 'reject' || action === 'modify'">
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">
            {{ action === 'reject' ? t('hitlQuickAction.rejectFeedback') : t('hitlQuickAction.modifyFeedback') }}
          </label>
          <textarea
            v-model="feedback"
            rows="3"
            class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            :placeholder="action === 'reject' ? t('hitlQuickAction.rejectPlaceholder') : t('hitlQuickAction.modifyPlaceholder')"
          ></textarea>
        </div>

        <!-- Confirmation message -->
        <div v-if="action === 'approve'" class="rounded-lg border border-green-200 bg-green-50 p-3 dark:border-green-800 dark:bg-green-900/10">
          <p class="text-xs text-green-700 dark:text-green-400">{{ t('hitlQuickAction.approveConfirm') }}</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-gray-200 px-5 py-4 dark:border-gray-700">
        <div v-if="!action" class="flex flex-wrap gap-2">
          <button
            class="flex-1 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-700 transition-colors flex items-center justify-center gap-1.5"
            @click="action = 'approve'"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            {{ t('hitlQuickAction.approve') }}
          </button>
          <button
            class="flex-1 rounded-lg border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors flex items-center justify-center gap-1.5"
            @click="action = 'modify'"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            {{ t('hitlQuickAction.modify') }}
          </button>
          <button
            class="flex-1 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-700 transition-colors flex items-center justify-center gap-1.5"
            @click="action = 'reject'"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            {{ t('hitlQuickAction.reject') }}
          </button>
        </div>

        <div v-else class="flex items-center justify-between gap-2">
          <button
            class="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700"
            @click="action = null; feedback = ''"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            class="rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors disabled:opacity-50"
            :class="action === 'approve' ? 'bg-green-600 hover:bg-green-700' : action === 'reject' ? 'bg-red-600 hover:bg-red-700' : 'bg-amber-600 hover:bg-amber-700'"
            :disabled="(action !== 'approve' && !feedback.trim())"
            @click="confirmAction"
          >
            {{ t(`hitlQuickAction.confirm${action!.charAt(0).toUpperCase()}${action!.slice(1)}`) }}
          </button>
        </div>

        <button
          class="mt-3 w-full text-center text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          @click="viewFullContext"
        >
          {{ t('hitlQuickAction.viewFullContext') }} →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useHitlStore } from '@/stores/hitlStore'
import { useIssuesStore } from '@/stores/issuesStore'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { useToast } from '@/composables/useToast'
import { IssueStatus } from '@/types'
import type { HITLRequest } from '@/types/hitl'

const { t } = useI18n()
const router = useRouter()
const hitlStore = useHitlStore()
const issuesStore = useIssuesStore()
const notificationsStore = useNotificationsStore()
const toast = useToast()

const props = defineProps<{ request: HITLRequest }>()
const emit = defineEmits<{ close: [] }>()

const action = ref<'approve' | 'reject' | 'modify' | null>(null)
const feedback = ref('')

async function confirmAction() {
  const req = props.request
  if (!req) return

  if (!action.value) return
  const chosen = action.value
  const fb = feedback.value.trim()

  if (chosen !== 'approve' && !fb) return

  const success = await hitlStore.resolveAction(req.id, chosen, fb || undefined)
  if (!success) {
    toast.error(t('hitlQuickAction.failed'))
    return
  }

  if (chosen === 'approve') {
    toast.success(t('hitlQuickAction.approved', { title: req.title }))
    await updateIssueStatus(req.issueId, IssueStatus.IN_PROGRESS)
  } else if (chosen === 'reject') {
    toast.error(t('hitlQuickAction.rejected', { title: req.title }))
    await updateIssueStatus(req.issueId, IssueStatus.OPEN)
  } else {
    toast.info(t('hitlQuickAction.modified', { title: req.title }))
    await updateIssueStatus(req.issueId, IssueStatus.IN_PROGRESS)
  }

  notificationsStore.addNotification({
    title: t('hitlQuickAction.resolvedTitle'),
    message: t(`hitlQuickAction.resolved_${chosen}`, { title: req.title }),
    category: 'hitl',
    requiresAction: false,
    linkTo: { name: 'issues', params: { id: req.issueId } },
  })
  emit('close')
}

async function updateIssueStatus(issueId: string, status: IssueStatus) {
  if (!issueId) return
  try {
    await issuesStore.updateIssue(issueId, { status })
  } catch {
    // mock may not have the issue; ignore
  }
}

function viewFullContext() {
  hitlStore.selectRequest(props.request.id)
  hitlStore.closeQuickAction()
  emit('close')
  router.push({ name: 'HITLCommandCenter' })
}
</script>
