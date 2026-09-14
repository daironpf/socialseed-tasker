<template>
  <div class="blast-radius-slider space-y-3">
    <div class="flex items-center justify-between">
      <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('analysis.blastRadius') }}</label>
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-500 dark:text-gray-400">{{ t('analysis.depth') }}</span>
        <span class="rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
          {{ modelValue }}
        </span>
      </div>
    </div>

    <div class="relative">
      <input
        :value="modelValue"
        type="range"
        min="1"
        max="5"
        step="1"
        :aria-label="t('analysis.blastRadius')"
        class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 accent-blue-600"
        @input="onInput"
      />
      <div class="flex justify-between mt-1">
        <span
          v-for="i in 5"
          :key="i"
          class="text-[10px] w-4 text-center"
          :class="i <= modelValue ? 'text-blue-600 dark:text-blue-400 font-bold' : 'text-gray-400'"
        >{{ i }}</span>
      </div>
    </div>

    <div v-if="affectedPercent !== null" class="flex items-center gap-3 rounded-lg bg-gray-50 dark:bg-gray-800 px-3 py-2">
      <div class="flex-1">
        <div class="text-xs text-gray-500 dark:text-gray-400">{{ t('analysis.systemAffected') }}</div>
        <div class="flex items-center gap-2 mt-1">
          <div class="h-2 flex-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-300"
              :class="affectedPercent > 60 ? 'bg-red-500' : affectedPercent > 30 ? 'bg-amber-500' : 'bg-green-500'"
              :style="{ width: affectedPercent + '%' }"
            />
          </div>
          <span class="text-sm font-bold" :class="affectedPercent > 60 ? 'text-red-600 dark:text-red-400' : affectedPercent > 30 ? 'text-amber-600 dark:text-amber-400' : 'text-green-600 dark:text-green-400'">
            {{ affectedPercent.toFixed(1) }}%
          </span>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <span
        v-for="marker in depthMarkers"
        :key="marker.level"
        class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium"
        :class="marker.active ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500'"
      >
        <span class="h-1.5 w-1.5 rounded-full" :class="marker.active ? 'bg-blue-500' : 'bg-gray-300'"></span>
        L{{ marker.level }}: {{ marker.count }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  modelValue: number
  totalComponents: number
  affectedCount: number
  depthCounts?: Record<number, number>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function onInput(e: Event) {
  const val = Number((e.target as HTMLInputElement).value)
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    emit('update:modelValue', val)
  }, 200)
}

const affectedPercent = computed(() => {
  if (!props.totalComponents) return null
  return (props.affectedCount / props.totalComponents) * 100
})

const depthMarkers = computed(() => {
  const counts = props.depthCounts || {}
  return Array.from({ length: 5 }, (_, i) => ({
    level: i + 1,
    count: counts[i + 1] || 0,
    active: i + 1 <= props.modelValue,
  }))
})
</script>
