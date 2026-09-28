<template>
  <div class="rounded-xl border p-4" :class="borderClass">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-full" :class="iconBgClass">
          <svg v-if="!hasViolations && simulation.status !== 'failed'" class="h-5 w-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
          <svg v-else class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="font-semibold" :class="titleClass">{{ t('sandbox.simulationResult') }}</h3>
            <span class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold" :class="sourceBadgeClass">{{ sourceLabel }}</span>
          </div>
          <p class="text-sm" :class="textClass">
            <template v-if="simulation.status === 'failed'">{{ t('sandbox.simulationFailed') }}</template>
            <template v-else>
              {{ simulation.totalNodesChecked }} {{ t('sandbox.nodesChecked') }} —
              {{ simulation.totalEdgesChecked }} {{ t('sandbox.edgesChecked') }} —
              {{ simulation.violatingEdges }} {{ t('sandbox.violationsFound') }}
            </template>
          </p>
        </div>
      </div>
      <button v-if="canPromote" class="rounded-lg px-4 py-2 text-sm font-medium text-white" :class="hasViolations ? 'bg-amber-500 hover:bg-amber-600' : 'bg-green-600 hover:bg-green-700'" @click="$emit('promote')">
        {{ t('sandbox.promoteToActive') }}
      </button>
    </div>

    <p v-if="simulation.status === 'failed'" class="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
      {{ simulation.error === 'unrecognizedRule' ? t('sandbox.unrecognizedRule') : (simulation.error || t('sandbox.simulationFailed')) }}
    </p>

    <div v-if="simulation.status !== 'failed' && simulation.truncated" class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-300">
      {{ t('sandbox.truncatedWarning') }}
    </div>

    <div v-if="simulation.status !== 'failed' && hasViolations" class="mt-4 space-y-2 max-h-[300px] overflow-y-auto">
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

    <div v-if="simulation.status !== 'failed' && simulation.matchedNodes.length > 0" class="mt-4">
      <h4 class="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('sandbox.matchedNodes') }} ({{ simulation.matchedNodes.length }})</h4>
      <div class="mt-2 flex flex-wrap gap-2">
        <span v-for="node in simulation.matchedNodes" :key="node.id" class="inline-flex items-center gap-1.5 rounded-md border border-purple-200 bg-purple-50 px-2 py-1 text-xs text-purple-800 dark:border-purple-800 dark:bg-purple-900/20 dark:text-purple-300">
          <span class="font-medium">{{ node.title }}</span>
          <span v-if="node.component" class="text-[10px] text-purple-500 dark:text-purple-400">{{ node.component }}</span>
          <span v-if="node.status" class="text-[10px] text-purple-400 dark:text-purple-500">{{ node.status }}</span>
        </span>
      </div>
    </div>

    <div v-if="simulation.status !== 'failed' && simulation.blastRadius" class="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900/40">
      <h4 class="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('sandbox.blastRadius') }}</h4>
      <div class="mt-2 grid grid-cols-5 gap-2 text-center">
        <div>
          <div class="text-lg font-bold text-gray-900 dark:text-white">{{ simulation.blastRadius.direct }}</div>
          <div class="text-[10px] text-gray-500">{{ t('sandbox.blastDirect') }}</div>
        </div>
        <div>
          <div class="text-lg font-bold text-gray-900 dark:text-white">{{ simulation.blastRadius.total }}</div>
          <div class="text-[10px] text-gray-500">{{ t('sandbox.blastTotal') }}</div>
        </div>
        <div>
          <div class="text-lg font-bold text-red-600 dark:text-red-400">{{ simulation.blastRadius.critical }}</div>
          <div class="text-[10px] text-gray-500">{{ t('sandbox.blastCritical') }}</div>
        </div>
        <div>
          <div class="text-lg font-bold text-amber-600 dark:text-amber-400">{{ simulation.blastRadius.high }}</div>
          <div class="text-[10px] text-gray-500">{{ t('sandbox.blastHigh') }}</div>
        </div>
        <div>
          <div class="text-lg font-bold text-gray-900 dark:text-white">{{ simulation.blastRadius.maxDepth }}</div>
          <div class="text-[10px] text-gray-500">{{ t('sandbox.blastDepth') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { SimulationResult } from '@/types/sandbox'

const props = defineProps<{
  simulation: SimulationResult
  canPromote: boolean
}>()

defineEmits<{
  promote: []
}>()

const { t } = useI18n()

const hasViolations = computed(() => props.simulation.violatingEdges > 0)

const sourceLabel = computed(() =>
  props.simulation.dataSource === 'api' ? t('sandbox.graphSourceApi') : t('sandbox.graphSourceFallback')
)

const sourceBadgeClass = computed(() =>
  props.simulation.dataSource === 'api'
    ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
    : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
)

const borderClass = computed(() => {
  if (props.simulation.status === 'failed') return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
  return hasViolations.value
    ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
    : 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
})

const iconBgClass = computed(() => {
  if (props.simulation.status === 'failed' || hasViolations.value) return 'bg-red-100 dark:bg-red-800'
  return 'bg-green-100 dark:bg-green-800'
})

const titleClass = computed(() => {
  if (props.simulation.status === 'failed' || hasViolations.value) return 'text-red-800 dark:text-red-200'
  return 'text-green-800 dark:text-green-200'
})

const textClass = computed(() => {
  if (props.simulation.status === 'failed' || hasViolations.value) return 'text-red-600 dark:text-red-400'
  return 'text-green-600 dark:text-green-400'
})
</script>
