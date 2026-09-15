<template>
  <div class="relative" ref="menuRef">
    <button
      @click="isOpen = !isOpen"
      aria-label="User menu"
      class="flex items-center gap-2 rounded-lg p-2 text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
    >
      <div class="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-sm font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">
        {{ initials }}
      </div>
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="scale-95 opacity-0"
      enter-to-class="scale-100 opacity-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="scale-100 opacity-100"
      leave-to-class="scale-95 opacity-0"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 top-full z-50 mt-2 w-64 rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-800"
      >
        <!-- User Info - Clickable -->
        <button
          @click="navigateToProfile"
          class="w-full border-b border-gray-100 px-4 py-3 text-left transition-colors hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700/50"
        >
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">
              {{ initials }}
            </div>
            <div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">{{ username }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">admin</div>
            </div>
            <svg class="ml-auto h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>

        <!-- Theme Toggle -->
        <div class="border-b border-gray-100 px-2 py-2 dark:border-gray-700">
          <button
            @click="uiStore.toggleDarkMode()"
            class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            <svg v-if="uiStore.darkMode" class="h-4 w-4 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else class="h-4 w-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
            <span>{{ darkLabel }}</span>
          </button>
        </div>

        <!-- Language Selector -->
        <div class="border-b border-gray-100 px-2 py-2 dark:border-gray-700">
          <div class="px-3 py-1 text-xs font-medium text-gray-400 dark:text-gray-500">{{ t('menu.language') }}</div>
          <div class="flex gap-1 px-2 py-1">
            <button
              @click="switchLocale('en')"
              class="flex-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
              :class="uiStore.locale === 'en' ? 'bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400' : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'"
            >
              🇺🇸 English
            </button>
            <button
              @click="switchLocale('es')"
              class="flex-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
              :class="uiStore.locale === 'es' ? 'bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400' : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'"
            >
              🇪🇸 Español
            </button>
          </div>
        </div>

        <!-- Logout -->
        <div class="px-2 py-2">
          <button
            @click="handleLogout"
            class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span>{{ t('menu.logout') }}</span>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useUiStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'

const { t, locale } = useI18n()
const router = useRouter()
const uiStore = useUiStore()
const authStore = useAuthStore()

const isOpen = ref(false)
const menuRef = ref<HTMLElement | null>(null)

const username = computed(() => 'admin')
const initials = computed(() => 'A')

const darkLabel = computed(() => uiStore.darkMode ? t('menu.lightMode') : t('menu.darkMode'))

function switchLocale(newLocale: 'en' | 'es') {
  locale.value = newLocale
  uiStore.setLocale(newLocale)
  localStorage.setItem('locale', newLocale)
}

function handleLogout() {
  authStore.clearApiKey()
  window.location.reload()
}

function navigateToProfile() {
  isOpen.value = false
  router.push({ name: 'Profile' })
}

function handleClickOutside(event: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
