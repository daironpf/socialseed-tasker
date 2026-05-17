<template>
  <main class="flex-1 overflow-auto p-6">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Project Policies</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Governance constraints and architectural rules enforced on the project.
        </p>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
    </div>

    <div v-else-if="error" class="rounded-md bg-red-50 p-4 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-200">Error loading policies</h3>
          <div class="mt-2 text-sm text-red-700 dark:text-red-300">{{ error }}</div>
        </div>
      </div>
    </div>

    <div v-else-if="policies.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
      <div class="rounded-full bg-gray-100 p-4 dark:bg-gray-800">
        <svg class="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">No policies configured</h3>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400 max-w-md">
        This project currently does not have any active policies. Use the CLI to initialize or create policies.
      </p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div
        v-for="policy in policies"
        :key="policy.id"
        class="rounded-lg border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800 flex flex-col"
      >
        <div class="border-b border-gray-100 px-5 py-4 dark:border-gray-700 flex justify-between items-start">
          <h3 class="font-medium text-gray-900 dark:text-white truncate pr-2" :title="policy.name">
            {{ policy.name }}
          </h3>
          <span 
            class="inline-flex flex-shrink-0 items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
            :class="policy.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'"
          >
            {{ policy.is_active ? 'Active' : 'Inactive' }}
          </span>
        </div>
        
        <div class="p-5 flex-1 flex flex-col">
          <div class="prose prose-sm dark:prose-invert max-w-none flex-1 text-gray-600 dark:text-gray-300 mb-4 whitespace-pre-line">
            {{ policy.description || 'No description provided.' }}
          </div>
          
          <div class="mt-auto space-y-2 text-sm">
            <div class="flex justify-between border-t border-gray-100 pt-3 dark:border-gray-700">
              <span class="text-gray-500 dark:text-gray-400">Target Scope</span>
              <span class="font-medium text-gray-700 dark:text-gray-300">{{ policy.target_scope }}</span>
            </div>
            
            <div v-if="policy.rules && policy.rules.length > 0" class="flex justify-between border-t border-gray-100 pt-2 dark:border-gray-700">
              <span class="text-gray-500 dark:text-gray-400">Rules Count</span>
              <span class="font-medium text-gray-700 dark:text-gray-300">{{ policy.rules.length }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchPolicies } from '@/api/policiesApi'
import type { Policy } from '@/types'

const policies = ref<Policy[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

async function loadPolicies() {
  loading.value = true
  error.value = null
  try {
    policies.value = await fetchPolicies()
  } catch (err: any) {
    console.error('Failed to load policies:', err)
    error.value = err.message || 'Failed to load policies'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPolicies()
})
</script>
