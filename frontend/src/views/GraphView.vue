<template>
  <div class="flex-1 overflow-auto p-4">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Dependency Graph</h2>
      <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
        <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-blue-500"></span> Open</span>
        <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-amber-500"></span> In Progress</span>
        <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-red-500"></span> Blocked</span>
        <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-green-500"></span> Closed</span>
      </div>
    </div>

    <div v-if="issuesStore.loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else-if="issuesStore.issues.length === 0" class="text-center py-12 text-gray-400">
      No issues to display. Create some issues first.
    </div>
    <div v-else ref="graphContainer" class="w-full h-[600px] rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800" />

    <div
      v-if="selectedIssue"
      class="fixed inset-0 z-40 bg-black/50 flex justify-end"
      @click.self="uiStore.setSelectedIssue(null)"
    >
      <IssueDetailView
        :issue="selectedIssue"
        @close="uiStore.setSelectedIssue(null)"
        @update="onUpdateIssue"
        @delete="onDeleteIssue"
        @close-issue="onCloseIssue"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useIssuesStore } from '@/stores/issuesStore'
import { useUiStore } from '@/stores/uiStore'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import IssueDetailView from '@/views/IssueDetailView.vue'

const issuesStore = useIssuesStore()
const uiStore = useUiStore()
const graphContainer = ref<HTMLElement | null>(null)

const selectedIssue = computed(() => {
  if (!uiStore.selectedIssueId) return null
  return issuesStore.issues.find((i) => i.id === uiStore.selectedIssueId) ?? null
})

const statusColors: Record<string, string> = {
  OPEN: '#3b82f6',
  IN_PROGRESS: '#f59e0b',
  BLOCKED: '#ef4444',
  CLOSED: '#22c55e',
}

function buildGraph() {
  if (!graphContainer.value || issuesStore.issues.length === 0) return

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('width', '100%')
  svg.setAttribute('height', '100%')
  svg.style.width = '100%'
  svg.style.height = '100%'

  const issues = issuesStore.issues
  const width = graphContainer.value.clientWidth
  const height = graphContainer.value.clientHeight
  const cx = width / 2
  const cy = height / 2
  const radius = Math.min(width, height) * 0.35

  const positions = new Map<string, { x: number; y: number }>()

  issues.forEach((issue, i) => {
    const angle = (2 * Math.PI * i) / issues.length - Math.PI / 2
    positions.set(issue.id, {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    })
  })

  const edgesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g')
  const nodesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g')

  issues.forEach((issue) => {
    issue.dependencies.forEach((depId) => {
      const from = positions.get(issue.id)
      const to = positions.get(depId)
      if (!from || !to) return

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
      line.setAttribute('x1', String(from.x))
      line.setAttribute('y1', String(from.y))
      line.setAttribute('x2', String(to.x))
      line.setAttribute('y2', String(to.y))
      line.setAttribute('stroke', '#94a3b8')
      line.setAttribute('stroke-width', '2')
      line.setAttribute('marker-end', 'url(#arrowhead)')
      edgesGroup.appendChild(line)
    })
  })

  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs')
  const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker')
  marker.setAttribute('id', 'arrowhead')
  marker.setAttribute('markerWidth', '10')
  marker.setAttribute('markerHeight', '7')
  marker.setAttribute('refX', '28')
  marker.setAttribute('refY', '3.5')
  marker.setAttribute('orient', 'auto')
  const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
  polygon.setAttribute('points', '0 0, 10 3.5, 0 7')
  polygon.setAttribute('fill', '#94a3b8')
  marker.appendChild(polygon)
  defs.appendChild(marker)
  svg.appendChild(defs)

  issues.forEach((issue) => {
    const pos = positions.get(issue.id)
    if (!pos) return

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g')
    g.style.cursor = 'pointer'
    g.addEventListener('click', () => {
      uiStore.setSelectedIssue(issue.id)
    })

    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
    circle.setAttribute('cx', String(pos.x))
    circle.setAttribute('cy', String(pos.y))
    circle.setAttribute('r', '24')
    circle.setAttribute('fill', statusColors[issue.status] ?? '#6b7280')
    circle.setAttribute('stroke', '#1f2937')
    circle.setAttribute('stroke-width', '2')
    g.appendChild(circle)

    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text')
    text.setAttribute('x', String(pos.x))
    text.setAttribute('y', String(pos.y + 4))
    text.setAttribute('text-anchor', 'middle')
    text.setAttribute('fill', 'white')
    text.setAttribute('font-size', '10')
    text.setAttribute('font-weight', '600')
    text.textContent = issue.title.slice(0, 6)
    g.appendChild(text)

    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text')
    label.setAttribute('x', String(pos.x))
    label.setAttribute('y', String(pos.y + 40))
    label.setAttribute('text-anchor', 'middle')
    label.setAttribute('fill', document.documentElement.classList.contains('dark') ? '#d1d5db' : '#374151')
    label.setAttribute('font-size', '11')
    label.textContent = issue.title.length > 25 ? issue.title.slice(0, 25) + '...' : issue.title
    g.appendChild(label)

    nodesGroup.appendChild(g)
  })

  svg.appendChild(edgesGroup)
  svg.appendChild(nodesGroup)
  graphContainer.value.innerHTML = ''
  graphContainer.value.appendChild(svg)
}

async function onUpdateIssue(id: string, body: Record<string, unknown>) {
  await issuesStore.updateIssue(id, body)
  await nextTick()
  buildGraph()
}

async function onDeleteIssue(id: string) {
  const ok = await issuesStore.deleteIssue(id)
  if (ok) {
    uiStore.setSelectedIssue(null)
    await nextTick()
    buildGraph()
  }
}

async function onCloseIssue(id: string) {
  await issuesStore.closeIssue(id)
  await nextTick()
  buildGraph()
}

onMounted(async () => {
  await issuesStore.fetchIssues()
  await nextTick()
  buildGraph()
})

watch(() => issuesStore.issues.length, async () => {
  await nextTick()
  buildGraph()
})
</script>
