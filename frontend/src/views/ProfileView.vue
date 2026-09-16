<template>
  <div class="flex-1 overflow-auto p-6">
    <div class="mx-auto max-w-2xl">
      <h1 class="mb-6 text-2xl font-bold text-gray-900 dark:text-white">{{ t('profile.title') }}</h1>

      <!-- Avatar Section -->
      <div class="mb-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div class="flex items-center gap-6">
          <div class="relative">
            <div class="flex h-20 w-20 items-center justify-center rounded-full bg-brand-100 text-2xl font-bold text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">
              {{ initials }}
            </div>
            <button class="absolute bottom-0 right-0 rounded-full bg-blue-600 p-1.5 text-white shadow-sm hover:bg-blue-700">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
          <div>
            <div class="text-lg font-semibold text-gray-900 dark:text-white">{{ username }}</div>
            <div class="text-sm text-gray-500 dark:text-gray-400">{{ t(`profile.roles.${form.role}`) }}</div>
          </div>
        </div>
      </div>

      <!-- Personal Information -->
      <div class="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">{{ t('profile.personalInfo') }}</h2>
        <form @submit.prevent="saveProfile" class="space-y-4">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('profile.firstName') }}</label>
              <input
                v-model="form.firstName"
                type="text"
                class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('profile.lastName') }}</label>
              <input
                v-model="form.lastName"
                type="text"
                class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              />
            </div>
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('profile.email') }}</label>
            <input
              v-model="form.email"
              type="email"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('profile.role') }}</label>
            <select
              v-model="form.role"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="admin">{{ t('profile.roles.admin') }}</option>
              <option value="developer">{{ t('profile.roles.developer') }}</option>
              <option value="viewer">{{ t('profile.roles.viewer') }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('profile.timezone') }}</label>
            <select
              v-model="form.timezone"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">Eastern Time</option>
              <option value="America/Chicago">Central Time</option>
              <option value="America/Denver">Mountain Time</option>
              <option value="America/Los_Angeles">Pacific Time</option>
              <option value="Europe/London">London</option>
              <option value="Europe/Madrid">Madrid</option>
            </select>
          </div>
          <div class="flex justify-end">
            <button
              type="submit"
              class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              {{ t('profile.save') }}
            </button>
          </div>
        </form>
      </div>

      <!-- Password Section -->
      <div class="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">{{ t('profile.changePassword') }}</h2>
        <form @submit.prevent="changePassword" class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('profile.currentPassword') }}</label>
            <input
              v-model="passwordForm.current"
              type="password"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('profile.newPassword') }}</label>
            <input
              v-model="passwordForm.newPassword"
              type="password"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('profile.confirmPassword') }}</label>
            <input
              v-model="passwordForm.confirm"
              type="password"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            />
          </div>
          <div class="flex justify-end">
            <button
              type="submit"
              class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              {{ t('profile.updatePassword') }}
            </button>
          </div>
        </form>
      </div>

      <!-- Notifications Preferences -->
      <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">{{ t('profile.preferences') }}</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">{{ t('profile.emailNotifications') }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ t('profile.emailNotificationsDesc') }}</div>
            </div>
            <button
              role="switch"
              :aria-checked="preferences.emailNotifications"
              @click="preferences.emailNotifications = !preferences.emailNotifications"
              @keydown.enter.prevent="preferences.emailNotifications = !preferences.emailNotifications"
              @keydown.space.prevent="preferences.emailNotifications = !preferences.emailNotifications"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
              :class="preferences.emailNotifications ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'"
            >
              <span
                class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                :class="preferences.emailNotifications ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">{{ t('profile.pushNotifications') }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ t('profile.pushNotificationsDesc') }}</div>
            </div>
            <button
              role="switch"
              :aria-checked="preferences.pushNotifications"
              @click="preferences.pushNotifications = !preferences.pushNotifications"
              @keydown.enter.prevent="preferences.pushNotifications = !preferences.pushNotifications"
              @keydown.space.prevent="preferences.pushNotifications = !preferences.pushNotifications"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
              :class="preferences.pushNotifications ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'"
            >
              <span
                class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                :class="preferences.pushNotifications ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">{{ t('profile.agentAlerts') }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ t('profile.agentAlertsDesc') }}</div>
            </div>
            <button
              role="switch"
              :aria-checked="preferences.agentAlerts"
              @click="preferences.agentAlerts = !preferences.agentAlerts"
              @keydown.enter.prevent="preferences.agentAlerts = !preferences.agentAlerts"
              @keydown.space.prevent="preferences.agentAlerts = !preferences.agentAlerts"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
              :class="preferences.agentAlerts ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'"
            >
              <span
                class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                :class="preferences.agentAlerts ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>
        </div>
      </div>

      <!-- Success Toast -->
      <Transition
        enter-active-class="transition duration-300 ease-out"
        enter-from-class="translate-y-2 opacity-0"
        enter-to-class="translate-y-0 opacity-100"
        leave-active-class="transition duration-200 ease-in"
        leave-from-class="translate-y-0 opacity-100"
        leave-to-class="translate-y-2 opacity-0"
      >
        <div
          v-if="showSuccess"
          class="fixed bottom-4 right-4 z-50 rounded-lg bg-green-600 px-4 py-3 text-sm font-medium text-white shadow-lg"
        >
          {{ t('profile.saved') }}
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'

const { t } = useI18n()
const toast = useToast()

const username = computed(() => 'admin')
const initials = computed(() => 'AD')

const form = ref({
  firstName: 'Admin',
  lastName: 'User',
  email: 'admin@socialseed.dev',
  role: 'admin',
  timezone: 'UTC',
})

const passwordForm = ref({
  current: '',
  newPassword: '',
  confirm: '',
})

const preferences = ref({
  emailNotifications: true,
  pushNotifications: true,
  agentAlerts: true,
})

const showSuccess = ref(false)

function showSavedMessage() {
  showSuccess.value = true
  setTimeout(() => { showSuccess.value = false }, 2000)
}

function saveProfile() {
  showSavedMessage()
  toast.success(t('profile.saved'))
}

function changePassword() {
  if (passwordForm.value.newPassword !== passwordForm.value.confirm) {
    toast.error(t('profile.passwordMismatch'))
    return
  }
  if (passwordForm.value.newPassword.length < 8) {
    toast.error(t('profile.passwordTooShort'))
    return
  }
  passwordForm.value = { current: '', newPassword: '', confirm: '' }
  showSavedMessage()
  toast.success(t('profile.passwordUpdated'))
}
</script>
