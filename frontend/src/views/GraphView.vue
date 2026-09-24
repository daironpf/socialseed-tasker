<template>
  <div class="flex-1 overflow-auto p-4">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">{{ t('graph.title') }}</h2>
      <div class="flex items-center gap-4">
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="t('issues.search')"
          :aria-label="t('issues.search')"
          class="px-3 py-1.5 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
        />
        <select
          v-model="statusFilter"
          :aria-label="t('issues.status')"
          class="px-3 py-1.5 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
        >
          <option value="">{{ t('issues.allStatus') }}</option>
          <option value="OPEN">{{ t('issues.open') }}</option>
          <option value="IN_PROGRESS">{{ t('issues.inProgress') }}</option>
          <option value="BLOCKED">{{ t('issues.blocked') }}</option>
          <option value="CLOSED">{{ t('issues.closed') }}</option>
        </select>
        <div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-purple-500"></span> {{ t('issues.component') }}</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-blue-500"></span> {{ t('issues.open') }}</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-amber-500"></span> {{ t('issues.inProgress') }}</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-red-500"></span> {{ t('issues.blocked') }}</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-green-500"></span> {{ t('issues.closed') }}</span>
          <template v-if="codeOverlayEnabled">
            <span class="border-l border-gray-300 dark:border-gray-600 mx-1 h-3"></span>
            <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-cyan-500"></span> {{ t('codeOverlay.file') }}</span>
            <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-teal-500"></span> {{ t('codeOverlay.class') }}</span>
            <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-emerald-500"></span> {{ t('codeOverlay.function') }}</span>
            <span class="flex items-center gap-1"><span class="w-3 h-0.5 bg-pink-500"></span> {{ t('codeOverlay.affects') }}</span>
          </template>
          <template v-if="visibleTypes.includes('agent')">
            <span class="border-l border-gray-300 dark:border-gray-600 mx-1 h-3"></span>
            <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-orange-500"></span> {{ t('graphExplorer.types.agent') }}</span>
          </template>
          <template v-if="visibleTypes.includes('policy')">
            <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-pink-500"></span> {{ t('graphExplorer.types.policy') }}</span>
          </template>
          <template v-if="visibleTypes.includes('pr')">
            <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-slate-500"></span> {{ t('graphExplorer.types.pr') }}</span>
          </template>
        </div>
      </div>
    </div>

    <div class="mb-2 flex gap-2 items-center flex-wrap">
      <button
        @click="setLayout('hierarchical')"
        class="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
      >
        {{ t('graph.hierarchical') }}
      </button>
      <button
        @click="setLayout('force')"
        class="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
      >
        {{ t('graph.forceDirected') }}
      </button>
      <div class="border-l border-gray-300 dark:border-gray-600 mx-1"></div>
      <GraphFilters
        :components="componentsStore.components"
        :selected-components="selectedComponents"
        :max-hops="maxHops"
        :criticalities="CRITICALITIES"
        :selected-criticalities="criticalities"
        :node-types="nodeTypeOptions"
        :selected-node-types="visibleTypes"
        @update:selected-components="selectedComponents = $event"
        @update:max-hops="maxHops = $event"
        @update:selected-criticalities="criticalities = $event"
        @update:selected-node-types="visibleTypes = $event"
      />
      <div class="border-l border-gray-300 dark:border-gray-600 mx-1"></div>
      <button
        @click="toggleCodeOverlay"
        class="px-3 py-1 text-xs rounded flex items-center gap-1.5 transition-colors"
        :class="codeOverlayEnabled
          ? 'bg-indigo-600 text-white hover:bg-indigo-700'
          : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
        {{ codeOverlayEnabled ? t('graph.codeOverlayOn') : t('graph.codeOverlay') }}
      </button>
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

    <!-- Exploration toolbar (zoom / cluster / path tracing) -->
    <div class="mb-3 flex items-center">
      <GraphToolbar
        :clustered="clustered"
        :trace-source="traceSource"
        :trace-target="traceTarget"
        :trace-options="traceOptions"
        :trace-message="traceMessage"
        :trace-ok="traceOk"
        @zoom-in="zoomIn"
        @zoom-out="zoomOut"
        @fit="fitGraph"
        @update:clustered="toggleCluster"
        @update:trace-source="traceSource = $event"
        @update:trace-target="traceTarget = $event"
        @trace="tracePath"
        @clear-trace="clearTrace"
      />
    </div>

    <div v-if="loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
      <div v-else-if="graphData.nodes.length === 0" class="text-center py-12 text-gray-400">
        {{ t('graph.noData') }}
      </div>
    <div ref="networkContainer" role="application" :aria-label="t('graph.title')" class="w-full h-[600px] rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800" />

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

    <!-- Node / Edge inspector -->
    <NodeInspector
      :payload="inspector"
      @close="inspector = null"
      @action="onInspectorAction"
    />

    <div v-if="selectedCodeNode" class="fixed inset-0 z-40 flex justify-end bg-black/50" @click.self="selectedCodeNode = null">
      <div class="h-full w-full max-w-md overflow-y-auto bg-white shadow-2xl dark:bg-gray-800">
        <div class="sticky top-0 z-10 border-b border-gray-200 bg-white px-6 py-4 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span class="inline-flex h-10 w-10 items-center justify-center rounded-xl text-xs font-bold" :class="selectedCodeNode.type === 'File' ? 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300' : selectedCodeNode.type === 'Class' ? 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'">
                {{ selectedCodeNode.type }}
              </span>
              <div>
                <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ selectedCodeNode.name }}</h2>
                <p class="text-xs text-gray-500 font-mono">{{ selectedCodeNode.id }}</p>
              </div>
            </div>
            <button class="rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700" :aria-label="t('common.close')" @click="selectedCodeNode = null">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
        </div>
        <div class="p-6 space-y-4">
          <div><label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('codeOverlay.filePath') }}</label><p class="mt-1 text-sm font-mono text-gray-700 dark:text-gray-300">{{ selectedCodeNode.filePath }}</p></div>
          <div class="grid grid-cols-2 gap-4">
            <div><label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('codeOverlay.language') }}</label><p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedCodeNode.language }}</p></div>
            <div><label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('codeOverlay.lines') }}</label><p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedCodeNode.startLine }} — {{ selectedCodeNode.endLine }}</p></div>
          </div>
          <div><label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('codeOverlay.nodeType') }}</label><p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedCodeNode.type }}</p></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Network, DataSet } from 'vis-network/standalone'
import { useIssuesStore } from '@/stores/issuesStore'
import { useComponentsStore } from '@/stores/componentsStore'
import { useCodeGraphStore } from '@/stores/codeGraphStore'
import { useUiStore } from '@/stores/uiStore'
import { useUsersStore } from '@/stores/usersStore'
import { usePoliciesStore } from '@/stores/policiesStore'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import IssueDetailView from '@/views/IssueDetailView.vue'
import RelationshipModal from '@/components/ui/RelationshipModal.vue'
import GraphFilters from '@/components/ui/GraphFilters.vue'
import GraphToolbar from '@/components/graph/GraphToolbar.vue'
import NodeInspector from '@/components/graph/NodeInspector.vue'
import { wouldCreateCycle, findPath, blastRadius } from '@/utils/graphUtils'
import { useExport } from '@/composables/useExport'
import type { Issue, IssueUpdateRequest } from '@/types'
import type { CodeNode } from '@/types/codeGraph'
import type { InspectorPayload, InspectorLink, TraceSelectOption } from '@/types/graphExplorer'

const { exportPNG } = useExport()

const { t } = useI18n()

const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()
const codeGraphStore = useCodeGraphStore()
const uiStore = useUiStore()
const usersStore = useUsersStore()
const policiesStore = usePoliciesStore()
const router = useRouter()
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
let cycleErrorTimeout: ReturnType<typeof setTimeout> | null = null
const selectedComponents = ref<string[]>([])
const maxHops = ref(3)
const codeOverlayEnabled = ref(false)
const selectedCodeNode = ref<CodeNode | null>(null)

// Exploration state (#511)
const CRITICALITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
const clustered = ref(false)
const criticalities = ref<string[]>([])
const visibleTypes = ref<string[]>(['issue', 'component', 'agent', 'policy', 'pr'])
const traceSource = ref('')
const traceTarget = ref('')
const traceMessage = ref('')
const traceOk = ref(false)
const tracedPath = ref<string[]>([])
const inspector = ref<InspectorPayload | null>(null)

function showType(type: string): boolean {
  return visibleTypes.value.includes(type)
}

const codeNodeColors: Record<string, string> = {
  File: '#06b6d4',
  Class: '#14b8a6',
  Function: '#10b981',
}

async function toggleCodeOverlay() {
  codeOverlayEnabled.value = !codeOverlayEnabled.value
  if (codeOverlayEnabled.value && codeGraphStore.nodes.length === 0) {
    await codeGraphStore.fetchCodeStructure()
  }
  await nextTick()
  buildGraph()
}

const statusColors: Record<string, string> = {
  OPEN: '#3b82f6',
  IN_PROGRESS: '#f59e0b',
  BLOCKED: '#ef4444',
  CLOSED: '#22c55e',
}

const filteredIssues = computed(() => {
  let issues = issuesStore.filteredIssues
  if (statusFilter.value) {
    issues = issues.filter(i => i.status === statusFilter.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    issues = issues.filter(i => i.title.toLowerCase().includes(q))
  }
  if (criticalities.value.length > 0) {
    issues = issues.filter(i => criticalities.value.includes(i.priority))
  }
  return issues
})

const nodeTypeOptions = computed(() => [
  { id: 'issue', label: t('graphExplorer.types.issue'), dotClass: 'bg-blue-500' },
  { id: 'component', label: t('graphExplorer.types.component'), dotClass: 'bg-purple-500' },
  { id: 'agent', label: t('graphExplorer.types.agent'), dotClass: 'bg-orange-500' },
  { id: 'policy', label: t('graphExplorer.types.policy'), dotClass: 'bg-pink-500' },
  { id: 'pr', label: t('graphExplorer.types.pr'), dotClass: 'bg-slate-500' },
])

const traceOptions = computed<TraceSelectOption[]>(() =>
  filteredIssues.value.slice(0, 300).map(i => ({
    id: i.id,
    label: i.title.length > 40 ? i.title.slice(0, 40) + '...' : i.title,
  })),
)

const graphData = computed(() => {
  const issues = filteredIssues.value
  const components = componentsStore.components
  const nodeData: Array<{ id: string; label: string; color: string; shape: string; title: string; group?: string; componentId?: string; priority?: string }> = []
  const edgeData: Array<{ id: string; from: string; to: string; arrows: string; relation: string }> = []

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
    if (!showType('component')) break
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
    if (!showType('issue')) break
    if (visibleNodeIds && !visibleNodeIds.has(issue.id)) continue
    nodeData.push({
      id: issue.id,
      label: issue.title.length > 20 ? issue.title.slice(0, 20) + '...' : issue.title,
      color: statusColors[issue.status] ?? '#6b7280',
      shape: 'dot',
      title: issue.title,
      group: 'issue',
      componentId: issue.component_id || undefined,
      priority: issue.priority,
    })

    if (issue.component_id && showType('component')) {
      const comp = components.find(c => c.id === issue.component_id)
      if (comp && (!visibleNodeIds || visibleNodeIds.has(comp.id))) {
        edgeData.push({
          id: `${issue.id}-${issue.component_id}`,
          from: issue.component_id,
          to: issue.id,
          arrows: 'to',
          relation: 'component',
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
          relation: 'dependency',
        })
      }
    }
  }

  // Agents linked to their assigned issues (#511)
  if (showType('agent')) {
    const agentUsers = usersStore.users.filter(u => u.type === 'agent' || u.role?.includes('agent'))
    const visibleIssueIds = new Set(nodeData.filter(n => n.group === 'issue').map(n => n.id))
    for (const agent of agentUsers) {
      const agentId = `agent-${agent.id}`
      nodeData.push({
        id: agentId,
        label: agent.username,
        color: '#f97316',
        shape: 'diamond',
        title: `${agent.username}\n${agent.role || ''}`,
        group: 'agent',
      })
      for (const issue of issuesStore.issues) {
        if (issue.assignee === agent.id && visibleIssueIds.has(issue.id)) {
          edgeData.push({
            id: `${agentId}-${issue.id}`,
            from: agentId,
            to: issue.id,
            arrows: 'to',
            relation: 'agent',
          })
        }
      }
    }
  }

  // Policies as standalone governance nodes (#511)
  if (showType('policy')) {
    for (const policy of policiesStore.policies) {
      nodeData.push({
        id: `policy-${policy.id}`,
        label: policy.name,
        color: '#ec4899',
        shape: 'star',
        title: `${policy.name}\n${policy.target_scope}`,
        group: 'policy',
      })
    }
  }

  // GitHub PRs linked to issues (#511)
  if (showType('pr') && showType('issue')) {
    const visibleIssueIds = new Set(nodeData.filter(n => n.group === 'issue').map(n => n.id))
    for (const issue of issuesStore.issues) {
      if (!issue.github_sync || !visibleIssueIds.has(issue.id)) continue
      const prId = `pr-${issue.id}`
      nodeData.push({
        id: prId,
        label: `#${issue.github_sync.issue_number}`,
        color: '#475569',
        shape: 'square',
        title: `${issue.github_sync.github_url}`,
        group: 'pr',
      })
      edgeData.push({
        id: `pr-edge-${issue.id}`,
        from: issue.id,
        to: prId,
        arrows: 'to',
        relation: 'pr',
      })
    }
  }

  if (codeOverlayEnabled.value && codeGraphStore.nodes.length > 0) {
    const codeNodes = codeGraphStore.nodes
    const codeEdgesList = codeGraphStore.codeEdges

    for (const cn of codeNodes) {
      const shapeMap: Record<string, string> = { File: 'database', Class: 'diamond', Function: 'triangle' }
      nodeData.push({
        id: cn.id,
        label: cn.name.length > 18 ? cn.name.slice(0, 18) + '...' : cn.name,
        color: codeNodeColors[cn.type] || '#6b7280',
        shape: shapeMap[cn.type] || 'dot',
        title: `${cn.type}: ${cn.name}\n${cn.filePath}:${cn.startLine}-${cn.endLine}\n${cn.language}`,
        group: 'code',
      })
    }

    for (const ce of codeEdgesList) {
      if (ce.type === 'AFFECTS') {
        edgeData.push({
          id: `code-${ce.from}-${ce.to}`,
          from: ce.from,
          to: ce.to,
          arrows: 'to',
          relation: 'code',
        })
      } else {
        edgeData.push({
          id: `code-${ce.from}-${ce.to}`,
          from: ce.from,
          to: ce.to,
          arrows: 'to',
          relation: 'code',
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
          const fromIssue = filteredIssues.value.find(i => i.id === connectFrom.value)
          const toIssue = filteredIssues.value.find(i => i.id === nodeId)
          if (fromIssue && toIssue) {
            const existingEdges = edges!.get().map(e => ({ from: e.from, to: e.to }))
            if (wouldCreateCycle(existingEdges, connectFrom.value, nodeId)) {
              cycleError.value = t('graph.cycleDetected')
              if (cycleErrorTimeout) clearTimeout(cycleErrorTimeout)
              cycleErrorTimeout = setTimeout(() => cycleError.value = '', 3000)
            } else {
              relFromLabel.value = fromIssue.title
              relToLabel.value = toIssue.title
              showRelModal.value = true
            }
          }
          connectFrom.value = null
        }
      } else if (nodeId.startsWith('cluster-')) {
        try {
          network?.openCluster(nodeId)
        } catch {
          // cluster already removed
        }
      } else {
        const issue = filteredIssues.value.find(i => i.id === nodeId)
        if (issue) {
          selectedIssue.value = issue
          inspector.value = null
          return
        }
        const codeNode = codeOverlayEnabled.value
          ? codeGraphStore.nodes.find(n => n.id === nodeId)
          : undefined
        if (codeNode) {
          selectedCodeNode.value = codeNode
          inspector.value = null
          return
        }
        const payload = buildNodeInspector(nodeId)
        if (payload) inspector.value = payload
      }
    } else if (params.edges.length > 0 && !connectMode.value) {
      const payload = buildEdgeInspector(params.edges[0])
      if (payload) inspector.value = payload
    } else if (connectMode.value) {
      connectFrom.value = null
    } else {
      inspector.value = null
    }
  })

  if (clustered.value) applyClusters()
  if (tracedPath.value.length) applyTraceHighlight()

  loading.value = false
}

function setLayout(layout: string) {
  currentLayout = layout
  buildGraph()
}

// ---- Exploration controls (#511) ----

function zoomIn() {
  if (!network) return
  const scale = Math.min(network.getScale() * 1.3, 4)
  network.moveTo({ scale, animation: true })
}

function zoomOut() {
  if (!network) return
  const scale = Math.max(network.getScale() / 1.3, 0.05)
  network.moveTo({ scale, animation: true })
}

function fitGraph() {
  network?.fit({ animation: true })
}

function toggleCluster(value?: boolean) {
  clustered.value = value ?? !clustered.value
  buildGraph()
}

function applyClusters() {
  if (!network) return
  const grouped = new Map<string, string[]>()
  for (const node of nodes?.get() ?? []) {
    if (node.group !== 'issue' || !node.componentId) continue
    if (!grouped.has(node.componentId)) grouped.set(node.componentId, [])
    grouped.get(node.componentId)!.push(String(node.id))
  }
  for (const [compId, members] of grouped) {
    if (members.length < 2) continue
    const memberSet = new Set(members)
    const compName = componentsStore.components.find(c => c.id === compId)?.name || compId
    network.cluster({
      joinCondition: (options: { id?: string | number }) => memberSet.has(String(options.id)),
      processProperties: (clusterOptions: Record<string, unknown>, childNodes: unknown[]) => ({
        ...clusterOptions,
        id: `cluster-${compId}`,
        label: `${compName} (${childNodes.length})`,
        shape: 'box',
        color: '#6d28d9',
        font: { color: '#ffffff', size: 12 },
      }),
    } as never)
  }
}

function tracePath() {
  if (!traceSource.value || !traceTarget.value || traceSource.value === traceTarget.value) {
    traceOk.value = false
    traceMessage.value = t('graphExplorer.traceSelectBoth')
    return
  }
  const path = findPath(graphData.value.edges, traceSource.value, traceTarget.value)
  if (!path) {
    tracedPath.value = []
    traceOk.value = false
    traceMessage.value = t('graphExplorer.traceNoPath')
    buildGraph()
    return
  }
  tracedPath.value = path
  traceOk.value = true
  traceMessage.value = t('graphExplorer.traceFound', { count: path.length })
  applyTraceHighlight()
}

function clearTrace() {
  tracedPath.value = []
  traceMessage.value = ''
  traceOk.value = false
  buildGraph()
}

function applyTraceHighlight() {
  if (!nodes || !edges || tracedPath.value.length === 0) return
  const pathSet = new Set(tracedPath.value)
  const originalColors = new Map(graphData.value.nodes.map(n => [n.id, n.color]))
  nodes.update(graphData.value.nodes.map(n => ({
    id: n.id,
    color: pathSet.has(n.id) ? originalColors.get(n.id) ?? n.color : '#e5e7eb',
    font: { color: pathSet.has(n.id) ? '#111827' : '#9ca3af' },
  })))
  const pairs = new Set<string>()
  for (let i = 0; i < tracedPath.value.length - 1; i++) {
    const a = tracedPath.value[i]
    const b = tracedPath.value[i + 1]
    pairs.add(`${a}|${b}`)
    pairs.add(`${b}|${a}`)
  }
  edges.update(edges.get().map(e => pairs.has(`${e.from}|${e.to}`)
    ? { id: e.id, color: '#f59e0b', width: 3 }
    : { id: e.id, color: '#e5e7eb', width: 1 }))
}

// ---- Inspector builders (#511) ----

function nodeLabel(id: string): string {
  const node = graphData.value.nodes.find(n => n.id === id)
  return node?.title || node?.label || id
}

function buildNodeInspector(id: string): InspectorPayload | null {
  const issue = filteredIssues.value.find(i => i.id === id)
  if (issue) {
    const comp = componentsStore.components.find(c => c.id === issue.component_id)
    const assignee = usersStore.users.find(u => u.id === issue.assignee)
    return {
      kind: 'node',
      type: 'issue',
      title: issue.title,
      subtitle: `${issue.status} · ${comp?.name || ''}`,
      badge: issue.priority,
      fields: [
        { label: t('issues.status'), value: issue.status },
        { label: t('issues.priority'), value: issue.priority },
        { label: t('issues.component'), value: comp?.name || '-' },
        { label: t('graphExplorer.fields.assignee'), value: assignee?.username || '-' },
        { label: t('issues.labels'), value: issue.labels?.length ? issue.labels.join(', ') : '-' },
        { label: t('graphExplorer.fields.dependencies'), value: String(issue.dependencies?.length || 0) },
      ],
      blast: blastRadius(graphData.value.edges, id, 5, nid =>
        graphData.value.nodes.find(n => n.id === nid)?.priority),
      links: [
        { label: t('graphExplorer.links.openIssue'), kind: 'issue', value: issue.id },
        { label: t('graphExplorer.links.viewList'), kind: 'route', value: '/list' },
      ],
    }
  }

  const comp = componentsStore.components.find(c => c.id === id)
  if (comp) {
    const compIssues = issuesStore.issues.filter(i => i.component_id === comp.id)
    return {
      kind: 'node',
      type: 'component',
      title: comp.name,
      subtitle: comp.project,
      fields: [
        { label: t('graphExplorer.fields.issues'), value: String(compIssues.length) },
        { label: t('issues.open'), value: String(compIssues.filter(i => i.status === 'OPEN').length) },
        { label: t('issues.inProgress'), value: String(compIssues.filter(i => i.status === 'IN_PROGRESS').length) },
        { label: t('graphExplorer.fields.description'), value: comp.description || '-' },
      ],
      blast: blastRadius(graphData.value.edges, id, 5, nid =>
        graphData.value.nodes.find(n => n.id === nid)?.priority),
      links: [
        { label: t('graphExplorer.links.viewComponents'), kind: 'route', value: '/components' },
        { label: t('graphExplorer.links.viewList'), kind: 'route', value: '/list' },
      ],
    }
  }

  if (id.startsWith('agent-')) {
    const user = usersStore.users.find(u => u.id === id.slice('agent-'.length))
    if (!user) return null
    return {
      kind: 'node',
      type: 'agent',
      title: user.username,
      subtitle: user.role,
      badge: undefined,
      fields: [
        { label: t('graphExplorer.fields.email'), value: user.email },
        { label: t('graphExplorer.fields.model'), value: user.model || '-' },
        { label: t('graphExplorer.fields.skills'), value: user.skills?.length ? user.skills.join(', ') : '-' },
        { label: t('graphExplorer.fields.assignedIssues'), value: String(user.issues_assigned ?? 0) },
        { label: t('graphExplorer.fields.active'), value: user.is_active === false ? t('graphExplorer.no') : t('graphExplorer.yes') },
      ],
      links: [
        { label: t('graphExplorer.links.viewAgents'), kind: 'route', value: '/agents' },
        { label: t('graphExplorer.links.viewList'), kind: 'route', value: '/list' },
      ],
    }
  }

  if (id.startsWith('policy-')) {
    const policy = policiesStore.policies.find(p => `policy-${p.id}` === id)
    if (!policy) return null
    return {
      kind: 'node',
      type: 'policy',
      title: policy.name,
      subtitle: policy.target_scope,
      fields: [
        { label: t('graphExplorer.fields.scope'), value: policy.target_scope },
        { label: t('graphExplorer.fields.description'), value: policy.description || '-' },
        { label: t('graphExplorer.fields.rules'), value: String(policy.rules?.length || 0) },
        { label: t('graphExplorer.fields.active'), value: policy.is_active ? t('graphExplorer.yes') : t('graphExplorer.no') },
      ],
      links: [
        { label: t('graphExplorer.links.viewPolicies'), kind: 'route', value: '/policies' },
      ],
    }
  }

  if (id.startsWith('pr-')) {
    const linked = issuesStore.issues.find(i => i.id === id.slice('pr-'.length))
    if (!linked?.github_sync) return null
    return {
      kind: 'node',
      type: 'pr',
      title: `#${linked.github_sync.issue_number}`,
      subtitle: linked.title,
      badge: linked.github_sync.sync_status,
      fields: [
        { label: t('graphExplorer.fields.syncStatus'), value: linked.github_sync.sync_status },
        { label: t('graphExplorer.fields.lastSync'), value: linked.github_sync.last_synced_at },
        { label: t('graphExplorer.fields.linkedIssue'), value: linked.title },
      ],
      links: [
        { label: t('graphExplorer.links.openPR'), kind: 'url', value: linked.github_sync.github_url },
        { label: t('graphExplorer.links.openIssue'), kind: 'issue', value: linked.id },
      ],
    }
  }

  return null
}

function buildEdgeInspector(edgeId: string): InspectorPayload | null {
  if (!edges || !nodes) return null
  const edge = edges.get(edgeId)
  if (!edge) return null
  const fromNode = nodes.get(edge.from) as { title?: string; label?: string } | undefined
  const toNode = nodes.get(edge.to) as { title?: string; label?: string } | undefined
  const otherEdges = edges.get()
    .filter(e => String(e.id) !== String(edgeId))
    .map(e => ({ from: String(e.from), to: String(e.to) }))
  const inCycle = findPath(otherEdges, String(edge.to), String(edge.from)) !== null
  return {
    kind: 'edge',
    type: 'edge',
    title: `${nodeLabel(String(edge.from))} → ${nodeLabel(String(edge.to))}`,
    subtitle: t('graphExplorer.inspector.relationship'),
    fields: [],
    edge: {
      relation: edge.relation || 'dependency',
      fromLabel: fromNode?.title || fromNode?.label || String(edge.from),
      toLabel: toNode?.title || toNode?.label || String(edge.to),
      weight: 1,
      inCycle,
    },
    links: [],
  }
}

function onInspectorAction(link: InspectorLink) {
  if (link.kind === 'issue') {
    const issue = issuesStore.issues.find(i => i.id === link.value)
      ?? filteredIssues.value.find(i => i.id === link.value)
    if (issue) {
      inspector.value = null
      selectedIssue.value = issue
      return
    }
  } else if (link.kind === 'route') {
    inspector.value = null
    router.push(link.value)
    return
  } else if (link.kind === 'url') {
    window.open(link.value, '_blank', 'noopener')
  }
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
  uiStore.simulateSync()
  await nextTick()
  buildGraph()
}

async function onDeleteIssue(id: string) {
  const ok = await issuesStore.deleteIssue(id)
  if (ok) {
    uiStore.simulateSync()
    selectedIssue.value = null
    await nextTick()
    buildGraph()
  }
}

async function onCloseIssue(id: string) {
  await issuesStore.closeIssue(id)
  uiStore.simulateSync()
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
    usersStore.fetchUsers(),
    policiesStore.fetchPolicies(),
  ])
  await nextTick()
  buildGraph()
})

onUnmounted(() => {
  if (cycleErrorTimeout) clearTimeout(cycleErrorTimeout)
  if (network) {
    network.destroy()
  }
})

watch([graphData, statusFilter, searchQuery, selectedComponents, maxHops], async () => {
  await nextTick()
  buildGraph()
}, { deep: true })
</script>