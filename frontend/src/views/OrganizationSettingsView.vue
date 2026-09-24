<template>
  <div class="flex-1 overflow-auto p-4 sm:p-6">
    <div class="mx-auto max-w-4xl">
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white sm:text-2xl">
            {{ t('organizations.settingsTitle') }}
          </h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ t('organizations.settingsSubtitle') }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs font-medium text-gray-500 dark:text-gray-400">
            {{ t('organizations.activeRole') }}
          </label>
          <select
            :value="store.activeRole"
            class="rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            @change="onRoleChange"
          >
            <option v-for="r in roles" :key="r" :value="r">
              {{ t(`organizations.roles.${r}`) }}
            </option>
          </select>
        </div>
      </div>

      <div v-if="store.loading" class="rounded-xl border border-gray-200 bg-white p-8 text-center text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-800">
        {{ t('common.loading') }}
      </div>
      <div v-else-if="!store.currentOrg" class="rounded-xl border border-gray-200 bg-white p-8 text-center text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-800">
        {{ t('organizations.empty') }}
      </div>

      <template v-else>
        <!-- Org overview -->
        <div class="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ store.currentOrg.name }}
              </h2>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ store.currentOrg.industry }} · {{ store.currentOrg.plan }}
              </p>
            </div>
            <span
              class="rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300"
            >
              {{ t(`organizations.roles.${store.activeRole}`) }}
            </span>
          </div>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div
              v-for="item in quotaCards"
              :key="item.key"
              class="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/40"
            >
              <div class="mb-1 flex items-center justify-between">
                <span class="text-xs font-medium text-gray-500 dark:text-gray-400">
                  {{ t(`organizations.quota.${item.key}`) }}
                </span>
                <span
                  class="text-xs font-bold"
                  :class="item.percent >= 90 ? 'text-red-600' : item.percent >= 70 ? 'text-amber-600' : 'text-emerald-600'"
                >
                  {{ item.percent }}%
                </span>
              </div>
              <div class="mb-2 h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  class="h-full rounded-full transition-all"
                  :class="item.percent >= 90 ? 'bg-red-500' : item.percent >= 70 ? 'bg-amber-500' : 'bg-emerald-500'"
                  :style="{ width: Math.min(item.percent, 100) + '%' }"
                />
              </div>
              <div class="text-xs text-gray-600 dark:text-gray-300">
                {{ item.used }} / {{ item.limit }}
              </div>
            </div>
          </div>
        </div>

        <!-- Retention -->
        <div class="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
            {{ t('organizations.retention.title') }}
          </h2>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                {{ t('organizations.retention.days') }}
              </label>
              <input
                v-model.number="retentionDraft.days"
                type="number"
                min="7"
                max="3650"
                :disabled="!store.canEdit"
                class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              />
            </div>
            <label class="flex items-center gap-2 pt-6 text-sm text-gray-700 dark:text-gray-300">
              <input v-model="retentionDraft.autoDelete" type="checkbox" :disabled="!store.canEdit" class="h-4 w-4" />
              {{ t('organizations.retention.autoDelete') }}
            </label>
            <label class="flex items-center gap-2 pt-6 text-sm text-gray-700 dark:text-gray-300">
              <input v-model="retentionDraft.exportBeforeDelete" type="checkbox" :disabled="!store.canEdit" class="h-4 w-4" />
              {{ t('organizations.retention.exportBeforeDelete') }}
            </label>
          </div>
          <div class="mt-4 flex justify-end">
            <button
              :disabled="!store.canEdit"
              class="min-h-[44px] rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              @click="saveRetention"
            >
              {{ t('common.save') }}
            </button>
          </div>
          <p v-if="!store.canEdit" class="mt-2 text-xs text-amber-600 dark:text-amber-400">
            {{ t('organizations.readOnlyHint') }}
          </p>
        </div>

        <!-- Accounts -->
        <div class="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div class="mb-4 flex items-center justify-between gap-3">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ t('organizations.accounts.title') }}
            </h2>
            <button
              :disabled="!store.canManage"
              class="min-h-[40px] rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              @click="showAccountForm = !showAccountForm"
            >
              {{ t('organizations.accounts.add') }}
            </button>
          </div>

          <div v-if="showAccountForm" class="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-300">
                  {{ t('organizations.accounts.name') }}
                </label>
                <input
                  v-model="accountDraft.name"
                  type="text"
                  class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                />
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-300">
                  {{ t('organizations.accounts.email') }}
                </label>
                <input
                  v-model="accountDraft.email"
                  type="email"
                  class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                />
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-300">
                  {{ t('organizations.accounts.role') }}
                </label>
                <select
                  v-model="accountDraft.role"
                  class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                >
                  <option v-for="r in roles" :key="r" :value="r">
                    {{ t(`organizations.roles.${r}`) }}
                  </option>
                </select>
              </div>
              <div class="flex items-end">
                <button
                  class="min-h-[40px] w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  @click="addAccount"
                >
                  {{ t('common.create') }}
                </button>
              </div>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full min-w-[480px] text-left text-sm">
              <thead>
                <tr class="border-b border-gray-200 text-xs uppercase text-gray-500 dark:border-gray-700">
                  <th class="px-2 py-2">{{ t('organizations.accounts.name') }}</th>
                  <th class="px-2 py-2">{{ t('organizations.accounts.email') }}</th>
                  <th class="px-2 py-2">{{ t('organizations.accounts.role') }}</th>
                  <th class="px-2 py-2">{{ t('components.actions') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="acc in store.currentOrg.accounts"
                  :key="acc.id"
                  class="border-b border-gray-100 dark:border-gray-700/50"
                >
                  <td class="px-2 py-3 font-medium text-gray-900 dark:text-white">
                    {{ acc.avatar }} {{ acc.name }}
                  </td>
                  <td class="px-2 py-3 text-gray-500 dark:text-gray-400">{{ acc.email }}</td>
                  <td class="px-2 py-3">
                    <span class="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium dark:bg-gray-700">
                      {{ t(`organizations.roles.${acc.role}`) }}
                    </span>
                  </td>
                  <td class="px-2 py-3">
                    <button
                      :disabled="!store.canManage"
                      class="text-xs text-red-600 hover:underline disabled:opacity-40 dark:text-red-400"
                      @click="store.removeAccount(store.currentOrg!.id, acc.id)"
                    >
                      {{ t('common.delete') }}
                    </button>
                  </td>
                </tr>
                <tr v-if="!store.currentOrg.accounts.length">
                  <td colspan="4" class="px-2 py-4 text-center text-gray-500">
                    {{ t('organizations.accounts.empty') }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Workspaces -->
        <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
            {{ t('organizations.workspacesTitle') }}
          </h2>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <button
              v-for="ws in store.currentOrg.workspaces"
              :key="ws.id"
              class="rounded-lg border p-4 text-left transition-colors"
              :class="
                ws.id === store.currentWorkspaceId
                  ? 'border-indigo-400 bg-indigo-50 dark:border-indigo-600 dark:bg-indigo-900/20'
                  : 'border-gray-200 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700/50'
              "
              @click="store.setWorkspace(ws.id)"
            >
              <div class="mb-1 flex items-center justify-between">
                <span class="font-medium text-gray-900 dark:text-white">{{ ws.name }}</span>
                <span class="text-xs text-gray-400">{{ ws.department }}</span>
              </div>
              <p class="mb-2 text-xs text-gray-500 dark:text-gray-400">{{ ws.description }}</p>
              <div class="flex gap-3 text-xs text-gray-500 dark:text-gray-400">
                <span>{{ ws.members }} {{ t('organizations.members') }}</span>
                <span>{{ ws.activeIssues }} {{ t('organizations.activeIssues') }}</span>
              </div>
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useOrganizationsStore } from '@/stores/organizationsStore'
import { useToast } from '@/composables/useToast'
import type { EnterpriseRole, EnterpriseAccount, DataRetentionPolicy } from '@/types/organizations'

const { t } = useI18n()
const store = useOrganizationsStore()
const toast = useToast()

const roles: EnterpriseRole[] = [
  'ENTERPRISE_ADMIN',
  'SECURITY_MANAGER',
  'DEVELOPER',
  'AUDITOR',
]

const showAccountForm = ref(false)
const accountDraft = reactive({
  name: '',
  email: '',
  role: 'DEVELOPER' as EnterpriseRole,
})

const retentionDraft = reactive<DataRetentionPolicy>({
  days: 365,
  autoDelete: true,
  exportBeforeDelete: true,
})

const quotaCards = computed(() => {
  const org = store.currentOrg
  if (!org) return []
  return [
    {
      key: 'compute',
      percent: store.quotaUsage.compute,
      used: formatNumber(org.quota.computeUsed),
      limit: formatNumber(org.quota.computeLimit),
    },
    {
      key: 'storage',
      percent: store.quotaUsage.storage,
      used: `${org.quota.storageUsedGb} GB`,
      limit: `${org.quota.storageLimitGb} GB`,
    },
    {
      key: 'tokens',
      percent: store.quotaUsage.tokens,
      used: formatNumber(org.quota.tokenUsed),
      limit: formatNumber(org.quota.tokenLimit),
    },
  ]
})

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return String(n)
}

function onRoleChange(e: Event) {
  store.setActiveRole((e.target as HTMLSelectElement).value as EnterpriseRole)
}

async function saveRetention() {
  if (!store.currentOrg) return
  const updated = await store.updateOrganization(store.currentOrg.id, {
    retention: { ...retentionDraft },
  })
  if (updated) toast.success(t('organizations.retention.saved'))
  else toast.error(store.error || t('common.error'))
}

function addAccount() {
  if (!store.currentOrg || !accountDraft.name.trim() || !accountDraft.email.trim()) return
  const account: EnterpriseAccount = {
    id: `acc-${Date.now()}`,
    name: accountDraft.name.trim(),
    email: accountDraft.email.trim(),
    role: accountDraft.role,
    avatar: '👤',
    isActive: true,
  }
  store.upsertAccount(store.currentOrg.id, account)
  accountDraft.name = ''
  accountDraft.email = ''
  accountDraft.role = 'DEVELOPER'
  showAccountForm.value = false
  toast.success(t('organizations.accounts.added'))
}

watch(
  () => store.currentOrg?.retention,
  (r) => {
    if (r) {
      retentionDraft.days = r.days
      retentionDraft.autoDelete = r.autoDelete
      retentionDraft.exportBeforeDelete = r.exportBeforeDelete
    }
  },
  { immediate: true, deep: true },
)

onMounted(() => {
  store.fetchOrganizations()
})
</script>
