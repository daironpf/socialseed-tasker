<template>
  <span
    v-if="issue.agent_working"
    class="inline-flex items-center gap-1"
    role="status"
    :title="label"
    :aria-label="label"
  >
    <svg
      class="h-3.5 w-3.5 animate-pulse text-cyan-600 dark:text-cyan-400"
      fill="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2zM9.5 13a1.5 1.5 0 100 3 1.5 1.5 0 000-3zm5 0a1.5 1.5 0 100 3 1.5 1.5 0 000-3z"
      />
    </svg>
    <span
      v-if="showTimer"
      class="rounded-full bg-white px-1.5 py-0.5 text-[10px] font-medium text-cyan-600 shadow dark:bg-gray-800 dark:text-cyan-400"
    >{{ elapsed }}</span>
  </span>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue } from '@/types'

const props = withDefaults(
  defineProps<{
    issue: Issue
    showTimer?: boolean
  }>(),
  { showTimer: false }
)

const { t } = useI18n()

const elapsed = ref('0m 0s')
let timerInterval: ReturnType<typeof setInterval> | null = null

function calculateElapsed() {
  if (!props.issue.agent_working || !props.issue.agent_working_started_at) {
    elapsed.value = '0m 0s'
    return
  }
  const start = new Date(props.issue.agent_working_started_at).getTime()
  const diff = Math.max(0, Date.now() - start)
  const totalSeconds = Math.floor(diff / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  elapsed.value = hours > 0 ? `${hours}h ${minutes}m ${seconds}s` : `${minutes}m ${seconds}s`
}

function startTimer() {
  stopTimer()
  if (props.issue.agent_working && props.issue.agent_working_started_at) {
    calculateElapsed()
    timerInterval = setInterval(calculateElapsed, 1000)
  }
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

const label = computed(() => `${t('issues.aiAgentActive')} · ${elapsed.value}`)

onMounted(startTimer)
onUnmounted(stopTimer)
watch(
  () => [props.issue.agent_working, props.issue.agent_working_started_at],
  startTimer
)
</script>
