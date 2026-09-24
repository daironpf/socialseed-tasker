<template>
  <main class="flex-1 overflow-auto p-4 sm:p-6">
    <div class="mx-auto max-w-6xl">
      <div class="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white sm:text-2xl">
            {{ t('governanceMatrix.title') }}
          </h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ t('governanceMatrix.subtitle') }}
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            class="min-h-[40px] rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="confirmReset"
          >
            {{ t('governanceMatrix.reset') }}
          </button>
          <button
            class="min-h-[40px] rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
            @click="showSimulator = !showSimulator"
          >
            {{ t('governanceMatrix.simulate') }}
          </button>
        </div>
      </div>

      <!-- Active alerts -->
      <div
        v-for="alert in governanceStore.activeAlerts"
        :key="alert.id"
        class="mb-4 rounded-lg border-l-4 border-amber-500 bg-amber-50 px-4 py-3 dark:border-amber-600 dark:bg-amber-900/20"
        role="alert"
      >
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="min-w-0">
            <div class="text-sm font-semibold text-amber-800 dark:text-amber-300">
              {{ t('governanceMatrix.alert.title') }}
            </div>
            <div class="text-xs text-amber-700 dark:text-amber-400">
              {{ alert.agentName }} · {{ t(`governanceMatrix.actions.${alert.action}`) }} ·
              {{ t(`governanceMatrix.risk.${alert.riskLevel}`) }} ·
              {{ t('governanceMatrix.alert.pausedFlag') }}
            </div>
          </div>
          <div class="flex gap-2">
            <button
              class="min-h-[36px] rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700"
              @click="decideAlert(alert.id, 'approved')"
            >
              {{ t('governanceMatrix.alert.resume') }}
            </button>
            <button
              class="min-h-[36px] rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700"
              @click="decideAlert(alert.id, 'rejected')"
            >
              {{ t('governanceMatrix.alert.halt') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Simulator -->
      <div
        v-if="showSimulator"
        class="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
      >
        <h2 class="mb-3 text-sm font-semibold text-gray-900 dark:text-white">
          {{ t('governanceMatrix.simulatorTitle') }}
        </h2>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              {{ t('governanceMatrix.fields.agent') }}
            </label>
            <select v-model="sim.agentType" class="gov-select">
              <option v-for="a in GOVERNANCE_AGENT_TYPES" :key="a" :value="a">
                {{ t(`governanceMatrix.agents.${a}`) }}
              </option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              {{ t('governanceMatrix.fields.risk') }}
            </label>
            <select v-model="sim.riskLevel" class="gov-select">
              <option v-for="r in GOVERNANCE_RISK_LEVELS" :key="r" :value="r">
                {{ t(`governanceMatrix.risk.${r}`) }}
              </option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              {{ t('governanceMatrix.fields.action') }}
            </label>
            <select v-model="sim.action" class="gov-select">
              <option v-for="a in GOVERNANCE_ACTIONS" :key="a" :value="a">
                {{ t(`governanceMatrix.actions.${a}`) }}
              </option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
              {{ t('governanceMatrix.fields.issue') }}
            </label>
            <select v-model="sim.issueId" class="gov-select">
              <option value="">{{ t('governanceMatrix.fields.noIssue') }}</option>
              <option v-for="issue in issuesStore.issues" :key="issue.id" :value="issue.id">
                {{ issue.title }}
              </option>
            </select>
          </div>
          <div class="flex items-end">
            <button
              class="min-h-[40px] w-full rounded-lg bg-amber-600 px-3 py-2 text-sm font-semibold text-white hover:bg-amber-700"
              @click="runSimulation"
            >
              {{ t('governanceMatrix.runSimulation') }}
            </button>
          </div>
        </div>
        <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {{ t('governanceMatrix.simulatorHint') }}
        </p>
      </div>

      <!-- Matrix -->
      <section class="mb-6 rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <header class="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 px-4 py-3 dark:border-gray-700">
          <div>
            <h2 class="text-base font-semibold text-gray-900 dark:text-white">
              {{ t('governanceMatrix.matrixTitle') }}
            </h2>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ t('governanceMatrix.cellHint') }}
            </p>
          </div>
          <div class="flex flex-wrap gap-1">
            <button
              v-for="risk in GOVERNANCE_RISK_LEVELS"
              :key="risk"
              class="rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors"
              :class="
                riskLevel === risk
                  ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              "
              @click="riskLevel = risk"
            >
              {{ t(`governanceMatrix.risk.${risk}`) }}
            </button>
          </div>
        </header>

        <div class="overflow-x-auto">
          <table class="w-full min-w-[560px] text-left text-sm">
            <thead>
              <tr class="border-b border-gray-200 text-xs uppercase text-gray-500 dark:border-gray-700">
                <th class="px-4 py-2">{{ t('governanceMatrix.fields.action') }}</th>
                <th
                  v-for="agent in GOVERNANCE_AGENT_TYPES"
                  :key="agent"
                  class="px-4 py-2 text-center"
                >
                  {{ t(`governanceMatrix.agents.${agent}`) }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="action in GOVERNANCE_ACTIONS"
                :key="action"
                class="border-b border-gray-100 last:border-b-0 dark:border-gray-700/50"
              >
                <td class="px-4 py-2.5 font-medium text-gray-800 dark:text-gray-200">
                  {{ t(`governanceMatrix.actions.${action}`) }}
                </td>
                <td v-for="agent in GOVERNANCE_AGENT_TYPES" :key="agent" class="px-4 py-2.5">
                  <button
                    class="mx-auto flex h-9 w-full max-w-[110px] items-center justify-center rounded-lg border px-2 text-xs font-bold transition-colors"
                    :class="cellClass(governanceStore.getCell(agent, riskLevel, action))"
                    :aria-label="`${t(`governanceMatrix.actions.${action}`)} / ${t(`governanceMatrix.agents.${agent}`)}`"
                    @click="governanceStore.toggleCell(agent, riskLevel, action)"
                  >
                    {{ t(`governanceMatrix.states.${governanceStore.getCell(agent, riskLevel, action)}`) }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="flex flex-wrap items-center gap-4 border-t border-gray-200 px-4 py-3 text-xs text-gray-500 dark:border-gray-700 dark:text-gray-400">
          <span class="flex items-center gap-1.5">
            <span class="h-3 w-3 rounded-full bg-emerald-500" />
            {{ t('governanceMatrix.states.auto') }}
          </span>
          <span class="flex items-center gap-1.5">
            <span class="h-3 w-3 rounded-full bg-amber-500" />
            {{ t('governanceMatrix.states.approval') }}
          </span>
          <span class="flex items-center gap-1.5">
            <span class="h-3 w-3 rounded-full bg-red-500" />
            {{ t('governanceMatrix.states.blocked') }}
          </span>
          <span class="ml-auto">{{ t('governanceMatrix.persistedHint') }}</span>
        </footer>
      </section>

      <!-- Pending approvals queue -->
      <PendingApprovalsQueue />
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useGovernanceStore } from '@/stores/governanceStore'
import { useIssuesStore } from '@/stores/issuesStore'
import { useHitlStore } from '@/stores/hitlStore'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { useToast } from '@/composables/useToast'
import PendingApprovalsQueue from '@/components/governance/PendingApprovalsQueue.vue'
import {
  GOVERNANCE_ACTIONS,
  GOVERNANCE_AGENT_TYPES,
  GOVERNANCE_RISK_LEVELS,
} from '@/types/governance'
import type { GovernanceActionId, GovernanceAgentType, GovernanceRiskLevel, PermissionState } from '@/types/governance'

const { t } = useI18n()
const governanceStore = useGovernanceStore()
const issuesStore = useIssuesStore()
const hitlStore = useHitlStore()
const notificationsStore = useNotificationsStore()
const toast = useToast()

const riskLevel = ref<GovernanceRiskLevel>('MEDIUM')
const showSimulator = ref(false)

const sim = reactive({
  agentType: 'CODING' as GovernanceAgentType,
  riskLevel: 'HIGH' as GovernanceRiskLevel,
  action: 'push_pr' as GovernanceActionId,
  issueId: '',
})

function cellClass(state: PermissionState): string {
  if (state === 'auto') {
    return 'border-emerald-300 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:border-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
  }
  if (state === 'approval') {
    return 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100 dark:border-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
  }
  return 'border-red-300 bg-red-50 text-red-700 hover:bg-red-100 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300'
}

function runSimulation() {
  const issue = issuesStore.issues.find((i) => i.id === sim.issueId)
  const alert = governanceStore.simulateRestrictedAction({
    agentType: sim.agentType,
    riskLevel: sim.riskLevel,
    action: sim.action,
    agentName: issue ? `${sim.agentType.toLowerCase()}-agent` : undefined,
    issueId: sim.issueId,
    issueTitle: issue?.title || '',
    command: issue ? `${sim.action} --issue ${issue.title}` : `${sim.action} --risk ${sim.riskLevel}`,
  })
  if (alert.resolved) {
    toast.info(t(`governanceMatrix.alert.auto_${alert.decision}`))
  } else {
    toast.warning(t('governanceMatrix.alert.pausedToast'))
    notificationsStore.addNotification({
      title: t('governanceMatrix.alert.title'),
      message: `${alert.agentName} · ${t(`governanceMatrix.actions.${alert.action}`)} · ${t(`governanceMatrix.risk.${alert.riskLevel}`)}`,
      category: 'hitl',
      requiresAction: true,
      linkTo: { name: 'GovernanceMatrix' },
    })
  }
}

function decideAlert(id: string, decision: 'approved' | 'rejected') {
  const alert = governanceStore.resolveAlert(id, decision)
  if (!alert) return
  if (decision === 'approved') {
    toast.success(t('governanceMatrix.alert.resumedToast'))
  } else {
    toast.error(t('governanceMatrix.alert.haltedToast'))
  }
}

function confirmReset() {
  governanceStore.resetMatrix()
  toast.success(t('governanceMatrix.resetDone'))
}

onMounted(() => {
  issuesStore.fetchIssues(1, 200).catch(() => undefined)
  hitlStore.fetchRequests().catch(() => undefined)
})
</script>

<style scoped>
.gov-select {
  @apply w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100;
}
</style>
