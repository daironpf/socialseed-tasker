<template>
  <div class="flex-1 overflow-auto p-4">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">{{ t('graph.title') }}</h2>
      <div class="flex items-center gap-4">
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="t('issues.search')"
          class="px-3 py-1.5 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
        />
        <select
          v-model="statusFilter"
          class="px-3 py-1.5 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
        >
          <option value="">{{ t('issues.allStatus') }}</option>
          <option value="OPEN">{{ t('issues.open') }}</option>
          <option value="IN_PROGRESS">{{ t('issues.inProgress') }}</option>
          <option value="BLOCKED">{{ t('issues.blocked') }}</option>
          <option value="CLOSED">{{ t('issues.closed') }}</option>
        </select>
        <div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-purple-500"></span> Component</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-blue-500"></span> Open</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-amber-500"></span> In Progress</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-red-500"></span> Blocked</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-green-500"></span> Closed</span>
        </div>
      </div>
    </div>

    <div class="mb-2 flex gap-2 items-center flex-wrap">
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
      <div class="border-l border-gray-300 dark:border-gray-600 mx-1"></div>
      <GraphFilters
        :components="componentsStore.components"
        :selected-components="selectedComponents"
        :max-hops="maxHops"
        @update:selected-components="selectedComponents = $event"
        @update:max-hops="maxHops = $event"
      />
      <div class="border-l border-gray-300 dark:border-gray-600 mx-1"></div>
      <button
        @click="toggleConnectMode"
        class="px-3 py-1 text-xs rounded flex items-center gap-1.5 transition-colors"
        :class="connectMode
          ? 'bg-blue-600 text-white hover:bg-blue-700'
          : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        {{ connectMode ? t('graph.connectModeOn') : t('graph.connectMode') }}
      </button>
      <Transition
        enter-active-class="transition duration-150"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-100"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <span v-if="connectMode" class="text-xs text-blue-600 dark:text-blue-400 flex items-center">
          {{ t('graph.connectHint') }}
        </span>
      </Transition>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else-if="graphData.nodes.length === 0" class="text-center py-12 text-gray-400">
      No issues to display. Create some issues first.
    </div>
    <div ref="networkContainer" class="w-full h-[600px] rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800" />

    <div class="mt-2 flex justify-end">
      <button
        class="flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
        @click="exportGraphPNG"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        {{ t('export.downloadPNG') }}
      </button>
    </div>

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

    <RelationshipModal
      :show="showRelModal"
      :from-label="relFromLabel"
      :to-label="relToLabel"
      @close="showRelModal = false"
      @create="onCreateRelationship"
    />

    <Transition
      enter-active-class="transition duration-150"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="cycleError" class="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 rounded-lg bg-red-600 px-4 py-2 text-sm text-white shadow-lg">
        {{ cycleError }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { Network, DataSet } from 'vis-network/standalone'
import { useIssuesStore } from '@/stores/issuesStore'
import { useComponentsStore } from '@/stores/componentsStore'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import IssueDetailView from '@/views/IssueDetailView.vue'
import RelationshipModal from '@/components/ui/RelationshipModal.vue'
import GraphFilters from '@/components/ui/GraphFilters.vue'
import { wouldCreateCycle } from '@/utils/graphUtils'
import { useExport } from '@/composables/useExport'
import type { Issue, IssueUpdateRequest } from '@/types'

const { exportPNG } = useExport()

const { t } = useI18n()

const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()
const networkContainer = ref<HTMLElement | null>(null)
const searchQuery = ref('')
const statusFilter = ref('')
const selectedIssue = ref<Issue | null>(null)
const loading = ref(true)
let network: Network | null = null
let nodes: DataSet<any> | null = null
let edges: DataSet<any> | null = null
let currentLayout = 'force'

const connectMode = ref(false)
const connectFrom = ref<string | null>(null)
const showRelModal = ref(false)
const relFromLabel = ref('')
const relToLabel = ref('')
const cycleError = ref('')
const selectedComponents = ref<string[]>([])
const maxHops = ref(3)

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
  const components = componentsStore.components
  const nodeData: Array<{ id: string; label: string; color: string; shape: string; title: string; group?: string }> = []
  const edgeData: Array<{ id: string; from: string; to: string; arrows: string }> = []

  // Build adjacency list for hop calculation
  const adj = new Map<string, Set<string>>()
  for (const issue of issues) {
    if (!adj.has(issue.id)) adj.set(issue.id, new Set())
    for (const depId of issue.dependencies) {
      adj.get(issue.id)!.add(depId)
      if (!adj.has(depId)) adj.set(depId, new Set())
      adj.get(depId)!.add(issue.id)
    }
  }

  // Calculate reachable nodes within maxHops from selected components
  let visibleNodeIds: Set<string> | null = null
  if (selectedComponents.value.length > 0) {
    visibleNodeIds = new Set()
    const queue: Array<{ id: string; depth: number }> = []
    for (const comp of components) {
      if (selectedComponents.value.includes(comp.id)) {
        visibleNodeIds.add(comp.id)
        queue.push({ id: comp.id, depth: 0 })
        // Also add issues belonging to this component
        for (const issue of issues) {
          if (issue.component_id === comp.id) {
            visibleNodeIds.add(issue.id)
            queue.push({ id: issue.id, depth: 0 })
          }
        }
      }
    }
    while (queue.length > 0) {
      const { id, depth } = queue.shift()!
      if (depth >= maxHops.value) continue
      for (const neighbor of (adj.get(id) || [])) {
        if (!visibleNodeIds.has(neighbor)) {
          visibleNodeIds.add(neighbor)
          queue.push({ id: neighbor, depth: depth + 1 })
        }
      }
    }
  }

  for (const component of components) {
    if (visibleNodeIds && !visibleNodeIds.has(component.id)) continue
    nodeData.push({
      id: component.id,
      label: component.name.length > 20 ? component.name.slice(0, 20) + '...' : component.name,
      color: '#8b5cf6',
      shape: 'box',
      title: component.name,
      group: 'component',
    })
  }

  for (const issue of issues) {
    if (visibleNodeIds && !visibleNodeIds.has(issue.id)) continue
    nodeData.push({
      id: issue.id,
      label: issue.title.length > 20 ? issue.title.slice(0, 20) + '...' : issue.title,
      color: statusColors[issue.status] ?? '#6b7280',
      shape: 'dot',
      title: issue.title,
      group: 'issue',
    })

    if (issue.component_id) {
      const comp = components.find(c => c.id === issue.component_id)
      if (comp && (!visibleNodeIds || visibleNodeIds.has(comp.id))) {
        edgeData.push({
          id: `${issue.id}-${issue.component_id}`,
          from: issue.component_id,
          to: issue.id,
          arrows: 'to',
        })
      }
    }

    for (const depId of issue.dependencies) {
      if (issues.find((i) => i.id === depId) && (!visibleNodeIds || visibleNodeIds.has(depId))) {
        edgeData.push({
          id: `${issue.id}-${depId}`,
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
        enabled: true,
        type: 'continuous',
        roundness: 0.5,
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
      const nodeId = params.nodes[0]
      if (connectMode.value) {
        if (!connectFrom.value) {
          connectFrom.value = nodeId
        } else if (nodeId !== connectFrom.value) {
          const fromIssue = issuesStore.issues.find(i => i.id === connectFrom.value)
          const toIssue = issuesStore.issues.find(i => i.id === nodeId)
          if (fromIssue && toIssue) {
            const existingEdges = edges!.get().map(e => ({ from: e.from, to: e.to }))
            if (wouldCreateCycle(existingEdges, connectFrom.value, nodeId)) {
              cycleError.value = t('graph.cycleDetected')
              setTimeout(() => cycleError.value = '', 3000)
            } else {
              relFromLabel.value = fromIssue.title
              relToLabel.value = toIssue.title
              showRelModal.value = true
            }
          }
          connectFrom.value = null
        }
      } else {
        const issue = issuesStore.issues.find(i => i.id === nodeId)
        if (issue) {
          selectedIssue.value = issue
        }
      }
    } else if (connectMode.value) {
      connectFrom.value = null
    }
  })

  loading.value = false
}

function setLayout(layout: string) {
  currentLayout = layout
  buildGraph()
}

function toggleConnectMode() {
  connectMode.value = !connectMode.value
  connectFrom.value = null
  cycleError.value = ''
  if (network) {
    network.setOptions({
      interaction: {
        dragNodes: !connectMode.value,
        dragView: !connectMode.value,
      },
    })
  }
}

async function onUpdateIssue(id: string, body: IssueUpdateRequest) {
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

function onCreateRelationship(_type: string) {
  showRelModal.value = false
}

async function exportGraphPNG() {
  if (!networkContainer.value) return
  const svgEl = networkContainer.value.querySelector('svg')
  if (svgEl) {
    await exportPNG(svgEl as SVGSVGElement, 'dependency-graph')
  }
}

onMounted(async () => {
  await Promise.all([
    issuesStore.fetchIssues(1, 500),
    componentsStore.fetchComponents(),
  ])
  await nextTick()
  buildGraph()
})

onUnmounted(() => {
  if (network) {
    network.destroy()
  }
})

watch([graphData, statusFilter, searchQuery, selectedComponents, maxHops], async () => {
  await nextTick()
  buildGraph()
}, { deep: true })
</script>