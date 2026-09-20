<template>
  <div class="rounded-xl border p-4" :class="simulation.violatingEdges === 0 ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20' : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-full" :class="simulation.violatingEdges === 0 ? 'bg-green-100 dark:bg-green-800' : 'bg-red-100 dark:bg-red-800'">
          <svg v-if="simulation.violatingEdges === 0" class="h-5 w-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
          <svg v-else class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
        </div>
        <div>
          <h3 class="font-semibold" :class="simulation.violatingEdges === 0 ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'">{{ t('sandbox.simulationResult') }}</h3>
          <p class="text-sm" :class="simulation.violatingEdges === 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
            {{ simulation.totalEdgesChecked }} {{ t('sandbox.edgesChecked') }} — {{ simulation.violatingEdges }} {{ t('sandbox.violationsFound') }}
          </p>
        </div>
      </div>
      <button v-if="simulation.violatingEdges === 0 && canPromote" class="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700" @click="$emit('promote')">
        {{ t('sandbox.promoteToActive') }}
      </button>
    </div>
    <div v-if="simulation.violations.length > 0" class="mt-4 space-y-2 max-h-[300px] overflow-y-auto">
      <div v-for="(v, idx) in simulation.violations" :key="idx" class="flex items-start gap-3 rounded-lg border p-3" :class="v.severity === 'HARD' ? 'border-red-200 bg-red-100/50 dark:border-red-800 dark:bg-red-900/10' : 'border-amber-200 bg-amber-100/50 dark:border-amber-800 dark:bg-amber-900/10'">
        <span class="mt-0.5 inline-flex h-5 items-center rounded px-1.5 text-[10px] font-bold" :class="v.severity === 'HARD' ? 'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200' : 'bg-amber-200 text-amber-800 dark:bg-amber-800 dark:text-amber-200'">{{ v.severity }}</span>
        <div class="flex-1">
          <div class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white">
            <span class="font-mono text-xs text-blue-600 dark:text-blue-400">{{ v.edgeFrom }}</span>
            <svg class="h-3 w-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
            <span class="font-mono text-xs text-blue-600 dark:text-blue-400">{{ v.edgeTo }}</span>
          </div>
          <div class="mt-1 text-xs text-gray-600 dark:text-gray-400">{{ v.message }}</div>
        </div>
        <span class="rounded px-1.5 py-0.5 text-[10px] font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">{{ v.edgeType }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { SimulationResult } from '@/types/sandbox'

defineProps<{
  simulation: SimulationResult
  canPromote: boolean
}>()

defineEmits<{
  promote: []
}>()

const { t } = useI18n()
</script>
