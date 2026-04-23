<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex flex-col">
    <AppHeader @new-issue="openNewIssue" />
    <div class="flex flex-1 overflow-hidden">
      <Sidebar />
      <RouterView />
    </div>

    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center"
      @click.self="showCreateModal = false"
    >
      <CreateIssueModal @close="showCreateModal = false" @created="onIssueCreated" />
    </div>

    <LoginScreen v-if="showLogin" @logged-in="onLoggedIn" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RouterView } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import CreateIssueModal from '@/components/issue/CreateIssueModal.vue'
import LoginScreen from '@/components/auth/LoginScreen.vue'
import { useUiStore } from '@/stores/uiStore'
import { useIssuesStore } from '@/stores/issuesStore'
import { useAuthStore } from '@/stores/authStore'

const uiStore = useUiStore()
const issuesStore = useIssuesStore()
const authStore = useAuthStore()
const showCreateModal = ref(false)

const showLogin = computed(() => !authStore.isAuthenticated)

function openNewIssue() {
  showCreateModal.value = true
}

function onIssueCreated() {
  showCreateModal.value = false
  issuesStore.fetchIssues()
}

function onLoggedIn() {
  window.location.reload()
}

onMounted(() => {
  uiStore.initDarkMode()
})
</script>
