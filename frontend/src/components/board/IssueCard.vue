<template>
  <div
    class="rounded-lg border bg-white p-3 shadow-sm transition-all hover:shadow-md dark:bg-gray-800 dark:border-gray-700 relative"
    :class="{
      'border-l-4 border-l-red-500': issue.priority === 'CRITICAL',
      'border-l-4 border-l-orange-400': issue.priority === 'HIGH',
      'cursor-grab active:cursor-grabbing': true
    }"
    draggable="true"
    @dragstart="onDragStart"
    @click="onClick"
  >
    <!-- Agent working indicator -->
    <div
      v-if="issue.agent_working"
      class="absolute -top-1.5 -right-1.5 bg-cyan-500 text-white rounded-full p-1 shadow-lg animate-pulse"
      title="AI Agent is working on this issue"
    >
      <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2M7.5 13A2.5 2.5 0 005 15.5 2.5 2.5 0 007.5 18h9a2.5 2.5 0 002.5-2.5 2.5 2.5 0 00-2.5-2.5h-9z"/>
      </svg>
    </div>
    <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 line-clamp-2">
      {{ issue.title }}
    </h4>
    <div class="mt-2 flex items-center gap-1.5 flex-wrap">
      <PriorityBadge :priority="issue.priority" />
      <span v-for="label in issue.labels.slice(0, 3)" :key="label" class="text-xs">
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
import type { Issue } from '@/types'
import PriorityBadge from '@/components/ui/PriorityBadge.vue'
import LabelTag from '@/components/ui/LabelTag.vue'

const props = defineProps<{
  issue: Issue
  componentName?: string
}>()

const emit = defineEmits<{
  select: [issue: Issue]
}>()

function onDragStart(event: DragEvent) {
  event.dataTransfer?.setData('application/json', JSON.stringify(props.issue))
  event.dataTransfer!.effectAllowed = 'move'
}

function onClick() {
  emit('select', props.issue)
}
</script>
