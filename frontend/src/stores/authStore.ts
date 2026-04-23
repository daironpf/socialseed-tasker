import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { API_KEY } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const storedKey = ref(localStorage.getItem('tasker_api_key') || '')
  const isAuthenticated = computed(() => !!storedKey.value || !!API_KEY)

  function setApiKey(key: string) {
    localStorage.setItem('tasker_api_key', key)
    storedKey.value = key
  }

  function clearApiKey() {
    localStorage.removeItem('tasker_api_key')
    storedKey.value = ''
  }

  function getApiKey() {
    return storedKey.value || API_KEY
  }

  return {
    storedKey,
    isAuthenticated,
    setApiKey,
    clearApiKey,
    getApiKey,
  }
})