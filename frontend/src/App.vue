<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex flex-col">
    <Sidebar />
    <div class="ml-20 flex flex-1 flex-col transition-all duration-300 pb-8">
      <AppHeader />
      <main class="flex-1 overflow-hidden">
        <RouterView />
      </main>
    </div>
    <TeamTicker />
    <CommandPalette ref="paletteRef" />
    <KeyboardShortcutsHelp ref="shortcutsHelpRef" />
    <ToastContainer />
    <FloatingChat @openFullChat="router.push('/chat')" />

    <LoginScreen v-if="showLogin" @logged-in="onLoggedIn" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppHeader from '@/components/layout/AppHeader.vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import LoginScreen from '@/components/auth/LoginScreen.vue'
import TeamTicker from '@/components/dashboard/TeamTicker.vue'
import CommandPalette from '@/components/ui/CommandPalette.vue'
import KeyboardShortcutsHelp from '@/components/ui/KeyboardShortcutsHelp.vue'
import ToastContainer from '@/components/ui/ToastContainer.vue'
import FloatingChat from '@/components/chat/FloatingChat.vue'
import { useUiStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'
import { useKeyboardShortcuts, initKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'

const uiStore = useUiStore()
const authStore = useAuthStore()
const router = useRouter()
const { t } = useI18n()
const { register } = useKeyboardShortcuts()

const paletteRef = ref<InstanceType<typeof CommandPalette> | null>(null)
const shortcutsHelpRef = ref<InstanceType<typeof KeyboardShortcutsHelp> | null>(null)

const showLogin = computed(() => !authStore.isAuthenticated)

function onLoggedIn() {
  window.location.reload()
}

onMounted(() => {
  uiStore.initDarkMode()
  initKeyboardShortcuts()

  register({
    key: 'c',
    label: 'Create Issue',
    description: t('shortcuts.createIssue'),
    scope: 'global',
    action: () => router.push('/list'),
  })

  register({
    key: 'd',
    label: 'Toggle Dark Mode',
    description: t('shortcuts.toggleDark'),
    scope: 'global',
    action: () => uiStore.toggleDarkMode(),
  })

  register({
    key: 'g',
    label: 'Go to...',
    description: 'Navigation prefix',
    scope: 'global',
    sequence: ['g', 'i'],
    action: () => router.push('/list'),
  })

  register({
    key: 'g',
    label: 'Go to Kanban',
    description: t('shortcuts.goKanban'),
    scope: 'global',
    sequence: ['g', 'k'],
    action: () => router.push('/kanban'),
  })

  register({
    key: 'g',
    label: 'Go to Graph',
    description: t('shortcuts.goGraph'),
    scope: 'global',
    sequence: ['g', 'g'],
    action: () => router.push('/graph'),
  })

  register({
    key: 'g',
    label: 'Go to Dashboard',
    description: t('shortcuts.goDashboard'),
    scope: 'global',
    sequence: ['g', 'b'],
    action: () => router.push('/board'),
  })

  register({
    key: 'g',
    label: 'Go to Users',
    description: t('shortcuts.goUsers'),
    scope: 'global',
    sequence: ['g', 'u'],
    action: () => router.push('/users'),
  })

  register({
    key: 'g',
    label: 'Go to Components',
    description: t('shortcuts.goComponents'),
    scope: 'global',
    sequence: ['g', 'c'],
    action: () => router.push('/components'),
  })
})
</script>
