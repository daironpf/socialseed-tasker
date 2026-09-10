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

    <LoginScreen v-if="showLogin" @logged-in="onLoggedIn" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { RouterView } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import LoginScreen from '@/components/auth/LoginScreen.vue'
import TeamTicker from '@/components/dashboard/TeamTicker.vue'
import { useUiStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'

const uiStore = useUiStore()
const authStore = useAuthStore()

const showLogin = computed(() => !authStore.isAuthenticated)

function onLoggedIn() {
  window.location.reload()
}

onMounted(() => {
  uiStore.initDarkMode()
})
</script>
