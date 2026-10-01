<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    @click.self="$emit('close')"
  >
    <div class="w-full max-w-sm bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
      <div class="border-b border-gray-200 dark:border-gray-700 p-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('graph.createRelationship') }}</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ fromLabel }} → {{ toLabel }}
        </p>
      </div>

      <div class="p-4 space-y-3">
        <button
          v-for="type in relationshipTypes"
          :key="type.value"
          class="w-full flex items-center gap-3 rounded-lg border p-3 text-left transition-colors"
          :class="selectedType === type.value
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'"
          @click="selectedType = type.value"
        >
          <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg" :class="type.bg">
            <span class="text-sm">{{ type.icon }}</span>
          </div>
          <div>
            <div class="text-sm font-medium text-gray-900 dark:text-white">{{ type.label }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">{{ type.description }}</div>
          </div>
        </button>

        <div
          v-if="error"
          data-testid="violation-panel"
          role="alert"
          class="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-200"
        >
          <div class="flex items-center gap-2 font-semibold">
            <span>{{ violationTitle }}</span>
            <span
              v-if="error.severity"
              class="rounded px-1.5 py-0.5 text-xs font-bold"
              :class="error.severity === 'hard'
                ? 'bg-red-600 text-white'
                : 'bg-amber-500 text-white'"
            >{{ severityLabel }}</span>
          </div>
          <p class="mt-1" data-testid="violation-message">{{ error.message }}</p>
          <p v-if="violationResource" class="mt-1">
            <span class="font-medium">{{ violationResource.label }}: </span>{{ violationResource.value }}
          </p>
          <p v-if="error.suggestion" class="mt-1" data-testid="violation-suggestion">
            <span class="font-medium">{{ t('graph.violationSuggestion') }}: </span>{{ error.suggestion }}
          </p>
        </div>
      </div>

      <div class="flex items-center justify-between border-t border-gray-200 dark:border-gray-700 p-4">
        <button
          class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="$emit('close')"
        >{{ t('graph.cancel') }}</button>
        <button
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          :disabled="!selectedType"
          @click="confirm"
        >{{ t('graph.create') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { PolicyViolationDetail } from '@/types'

const { t } = useI18n()

const props = defineProps<{
  show: boolean
  fromLabel: string
  toLabel: string
  error?: PolicyViolationDetail | null
}>()

const emit = defineEmits<{
  close: []
  create: [type: string]
}>()

const selectedType = ref('DEPENDS_ON')

const violationTitle = computed(() => {
  if (!props.error) return ''
  if (props.error.code === 'CIRCULAR_DEPENDENCY') return t('graph.cycleDetected')
  return t('graph.policyViolation')
})

const violationResource = computed(() => {
  if (!props.error) return null
  if (props.error.constraint) return { label: t('graph.violationConstraint'), value: props.error.constraint }
  if (props.error.policy_name) return { label: t('graph.violationPolicy'), value: props.error.policy_name }
  return null
})

const severityLabel = computed(() => (props.error?.severity ?? '').toUpperCase())

const relationshipTypes = computed(() => [
  {
    value: 'BLOCKS',
    label: t('graph.blockedBy'),
    description: t('graph.blockedByDesc'),
    icon: '🛑',
    bg: 'bg-red-100 dark:bg-red-900/30',
  },
  {
    value: 'DEPENDS_ON',
    label: t('graph.dependsOn'),
    description: t('graph.dependsOnDesc'),
    icon: '🔗',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
  },
])

function confirm() {
  if (selectedType.value) {
    emit('create', selectedType.value)
  }
}
</script>
