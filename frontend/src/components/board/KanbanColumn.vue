<template>
  <div
    class="flex flex-col rounded-lg bg-gray-100 dark:bg-gray-800 min-h-[200px]"
    @dragover.prevent
    @drop="onDrop"
  >
    <div class="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-700">
      <h3 class="text-sm font-semibold uppercase tracking-wider" :class="headerColor">
        {{ title }}
      </h3>
      <span class="rounded-full bg-gray-200 px-2 py-0.5 text-xs font-medium dark:bg-gray-700">
        {{ issues.length }}
      </span>
    </div>
    <div class="flex-1 p-2 space-y-2 overflow-y-auto">
      <IssueCard
        v-for="issue in sortedIssues"
        :key="issue.id"
        :issue="issue"
        :component-name="getComponentName(issue.component_id)"
        @select="$emit('openIssue', issue)"
        @dragstart="onDragStart($event, issue)"
      />
      <div v-if="sortedIssues.length === 0" class="text-center py-8 text-sm text-gray-400">
        No issues
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Issue, IssueStatus } from '@/types'
import IssueCard from './IssueCard.vue'
import { useComponentsStore } from '@/stores/componentsStore'

const props = defineProps<{
  title: string
  status: IssueStatus
  issues: Issue[]
}>()

const emit = defineEmits<{
  openIssue: [issue: Issue]
  dropIssue: [issue: Issue, newStatus: IssueStatus]
}>()

const componentsStore = useComponentsStore()

const priorityOrder: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }

const sortedIssues = computed(() =>
  [...props.issues].sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]),
)

const headerColor: Record<string, string> = {
  OPEN: 'text-blue-600 dark:text-blue-400',
  IN_PROGRESS: 'text-amber-600 dark:text-amber-400',
  BLOCKED: 'text-red-600 dark:text-red-400',
  CLOSED: 'text-green-600 dark:text-green-400',
}

function getComponentName(id: string): string {
  return componentsStore.getComponentById(id)?.name ?? ''
}

function onDragStart(event: DragEvent, issue: Issue) {
  event.dataTransfer?.setData('application/json', JSON.stringify(issue))
  event.dataTransfer!.effectAllowed = 'move'
}

function onDrop(event: DragEvent) {
  const data = event.dataTransfer?.getData('application/json')
  if (!data) return
  try {
    const issue: Issue = JSON.parse(data)
    if (issue.status !== props.status) {
      emit('dropIssue', issue, props.status)
    }
  } catch (e) {
    console.error('Failed to parse drag data', e)
  }
}
</script>
