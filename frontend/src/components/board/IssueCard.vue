<template>
  <div
    class="rounded-lg border bg-white p-3 shadow-sm transition-all hover:shadow-md dark:bg-gray-800 dark:border-gray-700 relative group"
    :class="{
      'border-l-4 border-l-red-500': issue.priority === 'CRITICAL',
      'border-l-4 border-l-orange-400': issue.priority === 'HIGH',
      'cursor-grab active:cursor-grabbing': true
    }"
    draggable="true"
    @dragstart="onDragStart"
    @click="onClick"
  >
    <!-- Agent working indicator with timer -->
    <div
      v-if="issue.agent_working"
      class="absolute -top-1.5 -right-1.5 flex items-center gap-1"
    >
      <span class="text-[10px] font-medium text-cyan-600 dark:text-cyan-400 bg-white dark:bg-gray-800 rounded-full px-1.5 py-0.5 shadow">
        {{ elapsed }}
      </span>
      <button
        class="bg-red-500 text-white rounded-full p-1 shadow-lg hover:bg-red-600 transition-colors opacity-0 group-hover:opacity-100"
        :title="t('agent.killSwitch')"
        @click.stop="killAgent"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
        </svg>
      </button>
    </div>
    <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 line-clamp-2">
      {{ issue.title }}
    </h4>
    <div class="mt-2 flex items-center gap-1.5 flex-wrap">
      <PriorityBadge :priority="issue.priority" />
      <span v-for="(label, idx) in issue.labels.slice(0, 3)" :key="`${label}-${idx}`" class="text-xs">
        <LabelTag :label="label" />
      </span>
      <span v-if="issue.labels.length > 3" class="text-xs text-gray-400">+{{ issue.labels.length - 3 }}</span>
    </div>
    <div class="mt-2 flex items-center justify-between text-xs text-gray-400">
      <span v-if="componentName" class="truncate max-w-[120px]">{{ componentName }}</span>
      <span v-if="issue.dependencies.length > 0" class="flex items-center gap-1">
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" />
        </svg>
        {{ issue.dependencies.length }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { Issue } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'
import { useUiStore } from '@/stores/uiStore'
import PriorityBadge from '@/components/ui/PriorityBadge.vue'
import LabelTag from '@/components/ui/LabelTag.vue'
import { useI18n } from 'vue-i18n'
import { useSoundEffects } from '@/composables/useSoundEffects'

const { t } = useI18n()
const issuesStore = useIssuesStore()
const uiStore = useUiStore()

const props = defineProps<{
  issue: Issue
  componentName?: string
}>()

const emit = defineEmits<{
  select: [issue: Issue]
}>()

const elapsed = ref('0m 0s')
let timerInterval: ReturnType<typeof setInterval> | null = null

function calculateElapsed() {
  if (!props.issue.agent_working || !props.issue.agent_working_started_at) {
    elapsed.value = '0m 0s'
    return
  }
  const start = new Date(props.issue.agent_working_started_at).getTime()
  const now = Date.now()
  const diff = Math.max(0, now - start)
  const totalSeconds = Math.floor(diff / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  if (hours > 0) {
    elapsed.value = `${hours}h ${minutes}m ${seconds}s`
  } else {
    elapsed.value = `${minutes}m ${seconds}s`
  }
}

onMounted(() => {
  if (props.issue.agent_working) {
    calculateElapsed()
    timerInterval = setInterval(calculateElapsed, 1000)
  }
})

onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
})

function killAgent() {
  issuesStore.updateIssue(props.issue.id, {
    agent_working: false,
    agent_working_started_at: null
  })
  uiStore.simulateSync()
  useSoundEffects().playAlert()
}

function onDragStart(event: DragEvent) {
  event.dataTransfer?.setData('application/json', JSON.stringify(props.issue))
  event.dataTransfer!.effectAllowed = 'move'
}

function onClick() {
  emit('select', props.issue)
}
</script>
