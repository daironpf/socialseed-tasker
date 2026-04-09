<template>
  <div class="flex-1 overflow-auto p-4">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Dependency Graph</h2>
      <div class="flex items-center gap-4">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search issues..."
          class="px-3 py-1.5 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
        />
        <select
          v-model="statusFilter"
          class="px-3 py-1.5 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
        >
          <option value="">All Status</option>
          <option value="OPEN">Open</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="BLOCKED">Blocked</option>
          <option value="CLOSED">Closed</option>
        </select>
        <div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-blue-500"></span> Open</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-amber-500"></span> In Progress</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-red-500"></span> Blocked</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-green-500"></span> Closed</span>
        </div>
      </div>
    </div>

    <div class="mb-2 flex gap-2">
      <button
        @click="setLayout('hierarchical')"
        class="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
      >
        Hierarchical
      </button>
      <button
        @click="setLayout('force')"
        class="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
      >
        Force Directed
      </button>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else-if="graphData.nodes.length === 0" class="text-center py-12 text-gray-400">
      No issues to display. Create some issues first.
    </div>
    <div ref="networkContainer" class="w-full h-[600px] rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800" />

    <div
      v-if="selectedIssue"
      class="fixed inset-0 z-40 bg-black/50 flex justify-end"
      @click.self="selectedIssue = null"
    >
      <IssueDetailView
        :issue="selectedIssue"
        @close="selectedIssue = null"
        @update="onUpdateIssue"
        @delete="onDeleteIssue"
        @close-issue="onCloseIssue"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Network, DataSet } from 'vis-network/standalone'
import { useIssuesStore } from '@/stores/issuesStore'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import IssueDetailView from '@/views/IssueDetailView.vue'
import type { Issue } from '@/types'

const issuesStore = useIssuesStore()
const networkContainer = ref<HTMLElement | null>(null)
const searchQuery = ref('')
const statusFilter = ref('')
const selectedIssue = ref<Issue | null>(null)
const loading = ref(true)
let network: Network | null = null
let nodes: DataSet | null = null
let edges: DataSet | null = null
let currentLayout = 'force'

const statusColors: Record<string, string> = {
  OPEN: '#3b82f6',
  IN_PROGRESS: '#f59e0b',
  BLOCKED: '#ef4444',
  CLOSED: '#22c55e',
}

const filteredIssues = computed(() => {
  let issues = issuesStore.issues
  if (statusFilter.value) {
    issues = issues.filter(i => i.status === statusFilter.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    issues = issues.filter(i => i.title.toLowerCase().includes(q))
  }
  return issues
})

const graphData = computed(() => {
  const issues = filteredIssues.value
  const nodeData: Array<{id: string, label: string, color: string, shape: string, title: string}> = []
  const edgeData: Array<{from: string, to: string, arrows: string}> = []

  for (const issue of issues) {
    nodeData.push({
      id: issue.id,
      label: issue.title.length > 20 ? issue.title.slice(0, 20) + '...' : issue.title,
      color: statusColors[issue.status] ?? '#6b7280',
      shape: 'dot',
      title: issue.title,
    })

    for (const depId of issue.dependencies) {
      if (issues.find(i => i.id === depId)) {
        edgeData.push({
          from: issue.id,
          to: depId,
          arrows: 'to',
        })
      }
    }
  }

  return { nodes: nodeData, edges: edgeData }
})

function buildGraph() {
  if (!networkContainer.value) return
  
  loading.value = true

  nodes = new DataSet(graphData.value.nodes)
  edges = new DataSet(graphData.value.edges)

  const options = {
    nodes: {
      size: 20,
      font: {
        size: 12,
        color: '#374151',
      },
      borderWidth: 2,
      shadow: true,
    },
    edges: {
      color: '#94a3b8',
      width: 1,
      smooth: {
        type: 'continuous',
      },
    },
    physics: {
      enabled: currentLayout === 'force',
      barnesHut: {
        gravitationalConstant: -2000,
        centralGravity: 0.1,
        springLength: 150,
        springConstant: 0.04,
      },
    },
    layout: currentLayout === 'hierarchical' ? {
      hierarchical: {
        enabled: true,
        direction: 'UD',
        sortMethod: 'directed',
        levelSeparation: 100,
        nodeSpacing: 150,
      },
    } : undefined,
    interaction: {
      hover: true,
      tooltipDelay: 200,
      zoomView: true,
      dragView: true,
      navigationButtons: true,
      keyboard: true,
    },
  }

  if (network) {
    network.destroy()
  }

  network = new Network(networkContainer.value, { nodes, edges }, options)

  network.on('click', (params) => {
    if (params.nodes.length > 0) {
      const issue = issuesStore.issues.find(i => i.id === params.nodes[0])
      if (issue) {
        selectedIssue.value = issue
      }
    }
  })

  loading.value = false
}

function setLayout(layout: string) {
  currentLayout = layout
  buildGraph()
}

async function onUpdateIssue(id: string, body: Record<string, unknown>) {
  await issuesStore.updateIssue(id, body)
  await nextTick()
  buildGraph()
}

async function onDeleteIssue(id: string) {
  const ok = await issuesStore.deleteIssue(id)
  if (ok) {
    selectedIssue.value = null
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

onUnmounted(() => {
  if (network) {
    network.destroy()
  }
})

watch([graphData, statusFilter, searchQuery], async () => {
  await nextTick()
  buildGraph()
}, { deep: true })
</script>