<template>
  <div class="flex min-h-[60vh] flex-1 items-center justify-center px-4 py-8">
    <div
      class="w-full max-w-2xl rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800 sm:p-8"
    >
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {{ t('setup.title') }}
      </h1>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        {{ t(`setup.steps.${stepKeys[step - 1]}`) }}
      </p>

      <ol class="mt-6 flex items-center gap-2 sm:gap-3" data-testid="setup-steps">
        <li
          v-for="(key, index) in stepKeys"
          :key="key"
          class="flex flex-1 items-center gap-2"
        >
          <span
            class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border text-sm font-semibold transition-colors"
            :class="stepClass(index)"
            :data-testid="`setup-step-${index + 1}`"
            :aria-current="step === index + 1 ? 'step' : undefined"
          >
            {{ index + 1 }}
          </span>
          <span
            class="hidden text-xs font-medium sm:block"
            :class="step === index + 1 ? 'text-brand-700 dark:text-brand-300' : 'text-gray-500 dark:text-gray-400'"
          >
            {{ t(`setup.steps.${key}`) }}
          </span>
        </li>
      </ol>

      <!-- Step 1: administrator credentials -->
      <section v-if="step === 1" class="mt-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {{ t('setup.credentials.heading') }}
        </h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ t('setup.credentials.description') }}
        </p>
        <div class="mt-4 flex flex-col gap-4">
          <div>
            <label for="setup-admin-user" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              {{ t('setup.credentials.adminUser') }}
            </label>
            <input
              id="setup-admin-user"
              v-model="adminUser"
              type="text"
              data-testid="setup-admin-user"
              autocomplete="username"
              class="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :aria-invalid="adminUser.trim() === ''"
              :aria-describedby="adminUser.trim() === '' ? 'setup-admin-user-error' : undefined"
            />
            <p
              v-if="adminUser.trim() === ''"
              id="setup-admin-user-error"
              class="mt-1 text-xs text-red-600 dark:text-red-400"
            >
              {{ t('setup.credentials.userRequired') }}
            </p>
          </div>
          <div>
            <label for="setup-admin-password" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              {{ t('setup.credentials.adminPassword') }}
            </label>
            <div class="relative">
              <input
                id="setup-admin-password"
                v-model="adminPassword"
                :type="showPassword ? 'text' : 'password'"
                data-testid="setup-admin-password"
                autocomplete="new-password"
                class="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 pr-11 text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                :data-testid="`setup-password-toggle`"
                :aria-label="showPassword ? t('setup.credentials.hidePassword') : t('setup.credentials.showPassword')"
                :aria-pressed="showPassword"
                @click="showPassword = !showPassword"
              >
                <svg v-if="!showPassword" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Step 2: root project -->
      <section v-else-if="step === 2" class="mt-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {{ t('setup.project.heading') }}
        </h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ t('setup.project.description') }}
        </p>
        <div class="mt-4 flex flex-col gap-4">
          <div>
            <label for="setup-project-name" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              {{ t('setup.project.name') }}
            </label>
            <input
              id="setup-project-name"
              v-model="projectName"
              type="text"
              data-testid="setup-project-name"
              :placeholder="t('setup.project.namePlaceholder')"
              class="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :aria-invalid="projectName.trim() === ''"
            />
          </div>
          <div>
            <label for="setup-project-summary" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              {{ t('setup.project.summary') }}
            </label>
            <textarea
              id="setup-project-summary"
              v-model="projectSummary"
              data-testid="setup-project-summary"
              rows="3"
              :placeholder="t('setup.project.summaryPlaceholder')"
              class="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              :aria-invalid="projectSummary.trim() === ''"
            />
            <p
              v-if="!projectReady"
              class="mt-1 text-xs text-red-600 dark:text-red-400"
            >
              {{ t('setup.project.required') }}
            </p>
          </div>
        </div>
      </section>

      <!-- Step 3: governance policies -->
      <section v-else-if="step === 3" class="mt-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {{ t('setup.policies.heading') }}
        </h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ t('setup.policies.description') }}
        </p>
        <div class="mt-4 flex flex-col gap-3">
          <label
            v-for="policy in predefinedPolicies"
            :key="policy.key"
            class="flex items-start gap-3 rounded-lg border border-gray-200 p-3 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700/50"
          >
            <input
              v-model="policyState[policy.key]"
              type="checkbox"
              class="mt-1 h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
              :data-testid="`setup-policy-${policy.key}`"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">
              {{ t(policy.labelKey) }}
            </span>
          </label>
        </div>

        <div class="mt-5">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {{ t('setup.policies.customTitle') }}
          </h3>
          <div class="mt-2 flex gap-2">
            <input
              v-model="customDraft"
              type="text"
              maxlength="100"
              data-testid="setup-custom-input"
              :placeholder="t('setup.policies.customPlaceholder')"
              class="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              @keyup.enter="addCustomPolicy"
            />
            <button
              type="button"
              data-testid="setup-add-policy"
              :disabled="customDraft.trim() === ''"
              class="flex-shrink-0 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              @click="addCustomPolicy"
            >
              {{ t('setup.policies.addPolicy') }}
            </button>
          </div>
          <p v-if="customPolicies.length === 0" class="mt-2 text-xs text-gray-500 dark:text-gray-400">
            {{ t('setup.policies.none') }}
          </p>
          <ul v-else class="mt-2 flex flex-col gap-2">
            <li
              v-for="(policy, index) in customPolicies"
              :key="`${policy}-${index}`"
              data-testid="setup-custom-item"
              class="flex items-center justify-between gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:text-gray-300"
            >
              <span class="min-w-0 break-all">{{ policy }}</span>
              <button
                type="button"
                data-testid="setup-remove-policy"
                :aria-label="t('setup.policies.removePolicy')"
                class="flex-shrink-0 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                @click="removeCustomPolicy(index)"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </li>
          </ul>
        </div>
      </section>

      <!-- Step 4: confirmation -->
      <section v-else class="mt-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {{ t('setup.confirm.heading') }}
        </h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ t('setup.confirm.description') }}
        </p>
        <dl class="mt-4 flex flex-col gap-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="flex items-baseline justify-between gap-4">
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              {{ t('setup.confirm.admin') }}
            </dt>
            <dd class="text-right text-sm text-gray-900 dark:text-gray-100" data-testid="setup-summary-admin">
              {{ adminUser.trim() }}
            </dd>
          </div>
          <div class="flex items-baseline justify-between gap-4">
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              {{ t('setup.confirm.project') }}
            </dt>
            <dd class="text-right text-sm text-gray-900 dark:text-gray-100" data-testid="setup-summary-project">
              {{ projectName.trim() }}
            </dd>
          </div>
          <div class="flex items-baseline justify-between gap-4">
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              {{ t('setup.confirm.summary') }}
            </dt>
            <dd class="text-right text-sm text-gray-900 dark:text-gray-100" data-testid="setup-summary-description">
              {{ projectSummary.trim() }}
            </dd>
          </div>
          <div class="flex items-baseline justify-between gap-4">
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              {{ t('setup.confirm.policies') }}
            </dt>
            <dd class="text-right text-sm text-gray-900 dark:text-gray-100" data-testid="setup-summary-policies">
              <template v-if="selectedPolicyLabels.length > 0">
                <span v-for="label in selectedPolicyLabels" :key="label" class="block">
                  {{ label }}
                </span>
              </template>
              <span v-else>{{ t('setup.confirm.none') }}</span>
            </dd>
          </div>
          <div class="flex items-baseline justify-between gap-4">
            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
              {{ t('setup.confirm.customPolicies') }}
            </dt>
            <dd class="text-right text-sm text-gray-900 dark:text-gray-100" data-testid="setup-summary-custom">
              <template v-if="customPolicies.length > 0">
                <span v-for="policy in customPolicies" :key="policy" class="block">
                  {{ policy }}
                </span>
              </template>
              <span v-else>{{ t('setup.confirm.none') }}</span>
            </dd>
          </div>
        </dl>
      </section>

      <div class="mt-8 flex items-center justify-between gap-3">
        <button
          v-if="step > 1"
          type="button"
          data-testid="setup-back"
          :disabled="submitting"
          class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="step -= 1"
        >
          {{ t('setup.actions.back') }}
        </button>
        <span v-else />
        <button
          v-if="step < TOTAL_STEPS"
          type="button"
          data-testid="setup-next"
          :disabled="!canNext"
          class="rounded-lg bg-cyan-600 px-5 py-2 text-sm font-semibold text-white hover:bg-cyan-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-cyan-500 dark:hover:bg-cyan-600"
          @click="nextStep"
        >
          {{ t('setup.actions.next') }}
        </button>
        <button
          v-else
          type="button"
          data-testid="setup-submit"
          :disabled="submitting"
          class="flex items-center gap-2 rounded-lg bg-cyan-600 px-5 py-2 text-sm font-semibold text-white hover:bg-cyan-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-cyan-500 dark:hover:bg-cyan-600"
          @click="submit"
        >
          <svg
            v-if="submitting"
            class="h-4 w-4 animate-spin"
            :aria-hidden="true"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          {{ submitting ? t('setup.actions.initializing') : t('setup.actions.initialize') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { postSetupInitialize } from '@/api/setupApi'
import { setApiMode } from '@/api/client'
import { useUiStore } from '@/stores/uiStore'
import { useToast } from '@/composables/useToast'

const TOTAL_STEPS = 4
const stepKeys = ['credentials', 'project', 'policies', 'confirm'] as const

const predefinedPolicies = [
  { key: 'prevent_circular_dependencies', labelKey: 'setup.policies.circular' },
  { key: 'require_solution_summary', labelKey: 'setup.policies.solutionSummary' },
  { key: 'require_human_approval_core', labelKey: 'setup.policies.humanApproval' },
] as const

const { t } = useI18n()
const router = useRouter()
const uiStore = useUiStore()
const toast = useToast()

const step = ref(1)
const adminUser = ref('admin')
const adminPassword = ref('admin')
const showPassword = ref(false)
const projectName = ref('')
const projectSummary = ref('')
const policyState = ref<Record<string, boolean>>({
  prevent_circular_dependencies: true,
  require_solution_summary: true,
  require_human_approval_core: false,
})
const customDraft = ref('')
const customPolicies = ref<string[]>([])
const submitting = ref(false)

const projectReady = computed(
  () => projectName.value.trim() !== '' && projectSummary.value.trim() !== '',
)

const canNext = computed(() => {
  if (step.value === 1) return adminUser.value.trim() !== ''
  if (step.value === 2) return projectReady.value
  return true
})

const selectedPolicyLabels = computed(() =>
  predefinedPolicies
    .filter((policy) => policyState.value[policy.key])
    .map((policy) => t(policy.labelKey)),
)

function stepClass(index: number): string {
  if (step.value > index + 1) {
    return 'border-brand-600 bg-brand-600 text-white'
  }
  if (step.value === index + 1) {
    return 'border-brand-600 bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
  }
  return 'border-gray-300 bg-white text-gray-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400'
}

function nextStep() {
  if (canNext.value && step.value < TOTAL_STEPS) {
    step.value += 1
  }
}

function addCustomPolicy() {
  const value = customDraft.value.trim()
  if (!value) return
  customPolicies.value.push(value.slice(0, 100))
  customDraft.value = ''
}

function removeCustomPolicy(index: number) {
  customPolicies.value.splice(index, 1)
}

async function submit() {
  if (submitting.value) return
  submitting.value = true
  try {
    await postSetupInitialize({
      admin_user: adminUser.value.trim(),
      admin_password: adminPassword.value,
      project_name: projectName.value.trim(),
      project_summary: projectSummary.value.trim(),
      policies: predefinedPolicies
        .filter((policy) => policyState.value[policy.key])
        .map((policy) => policy.key),
      custom_policies: [...customPolicies.value],
    })
    // The guard caches isInstalled=false from the entry navigation; flip it
    // before pushing so /board is not bounced back to /setup.
    uiStore.isInstalled = true
    // A freshly installed system runs against real data only (issue #545).
    setApiMode('real')
    router.push('/board')
  } catch (err) {
    const status = (err as { status?: number }).status
    if (status === 403) {
      uiStore.isInstalled = true
      setApiMode('real')
      toast.error(t('setup.errors.alreadyInstalled'))
      router.push('/board')
    } else {
      toast.error(t('setup.errors.initializeFailed'))
    }
  } finally {
    submitting.value = false
  }
}
</script>
