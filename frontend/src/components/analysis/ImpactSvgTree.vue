<template>
  <div class="w-full overflow-x-auto">
    <svg
      :width="svgWidth"
      :height="svgHeight"
      class="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900"
    >
      <defs>
        <marker :id="`arrowhead-${uid}`" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
        </marker>
        <marker :id="`arrowhead-red-${uid}`" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#ef4444" />
        </marker>
      </defs>

      <g v-for="(edge, i) in svgEdges" :key="'e-' + i">
        <line
          :x1="edge.x1"
          :y1="edge.y1"
          :x2="edge.x2"
          :y2="edge.y2"
          :stroke="edge.color"
          :stroke-width="edge.width"
          :stroke-dasharray="edge.dashed ? '6,4' : undefined"
          :marker-end="edge.dashed ? `url(#arrowhead-${uid})` : `url(#arrowhead-red-${uid})`"
        />
      </g>

      <g v-for="(node, i) in svgNodes" :key="'n-' + i">
        <rect
          :x="node.x - node.w / 2"
          :y="node.y - node.h / 2"
          :width="node.w"
          :height="node.h"
          :rx="node.isRoot ? 12 : 8"
          :fill="node.fill"
          :stroke="node.stroke"
          :stroke-width="node.isRoot ? 3 : 2"
          class="cursor-pointer"
          @click="$emit('selectIssue', node.id)"
        />
        <text
          :x="node.x"
          :y="node.y - 4"
          text-anchor="middle"
          :font-size="node.isRoot ? 13 : 11"
          font-weight="600"
          :fill="node.textColor"
        >
          {{ truncate(node.id, 10) }}
        </text>
        <text
          :x="node.x"
          :y="node.y + 12"
          text-anchor="middle"
          :font-size="node.isRoot ? 10 : 9"
          :fill="node.textColor"
          opacity="0.8"
        >
          {{ truncate(node.label, 18) }}
        </text>
        <circle
          :cx="node.x + node.w / 2 - 4"
          :cy="node.y - node.h / 2 + 4"
          r="5"
          :fill="statusColor(node.status)"
          stroke="white"
          stroke-width="1.5"
        />
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const uid = Math.random().toString(36).slice(2, 8)

interface TreeNode {
  id: string
  title: string
  status: string
  level: number
}

const props = defineProps<{
  rootId: string
  rootTitle: string
  rootStatus: string
  directDeps: TreeNode[]
  transitiveDeps: TreeNode[]
}>()

defineEmits<{
  selectIssue: [id: string]
}>()

const NODE_W = 130
const NODE_H = 44
const H_GAP = 40
const V_GAP = 70
const PADDING = 30

const statusColor = (status: string) => {
  const map: Record<string, string> = {
    OPEN: '#3b82f6',
    IN_PROGRESS: '#f59e0b',
    BLOCKED: '#ef4444',
    CLOSED: '#22c55e',
  }
  return map[status] || '#6b7280'
}

const statusFill = (status: string) => {
  const map: Record<string, string> = {
    OPEN: '#eff6ff',
    IN_PROGRESS: '#fefce8',
    BLOCKED: '#fef2f2',
    CLOSED: '#f0fdf4',
  }
  return map[status] || '#f9fafb'
}

const statusTextColor = (status: string) => {
  const map: Record<string, string> = {
    OPEN: '#1e40af',
    IN_PROGRESS: '#92400e',
    BLOCKED: '#991b1b',
    CLOSED: '#166534',
  }
  return map[status] || '#374151'
}

const levels = computed(() => {
  const map = new Map<number, TreeNode[]>()
  for (const d of props.directDeps) {
    const list = map.get(1) || []
    list.push({ ...d, level: 1 })
    map.set(1, list)
  }
  for (const t of props.transitiveDeps) {
    const lvl = t.level || 2
    const list = map.get(lvl) || []
    list.push({ ...t, level: lvl })
    map.set(lvl, list)
  }
  return map
})

const svgWidth = computed(() => {
  const maxPerLevel = Math.max(
    1,
    ...Array.from(levels.value.values()).map(l => l.length)
  )
  return Math.max(400, maxPerLevel * (NODE_W + H_GAP) + PADDING * 2)
})

const svgHeight = computed(() => {
  const numLevels = levels.value.size
  return (numLevels + 1) * (NODE_H + V_GAP) + PADDING * 2
})

const svgNodes = computed(() => {
  const nodes: any[] = []
  const rootX = svgWidth.value / 2
  const rootY = PADDING + NODE_H / 2

  nodes.push({
    id: props.rootId,
    label: props.rootTitle,
    status: props.rootStatus,
    x: rootX,
    y: rootY,
    w: NODE_W + 20,
    h: NODE_H + 8,
    fill: statusFill(props.rootStatus),
    stroke: statusColor(props.rootStatus),
    textColor: statusTextColor(props.rootStatus),
    isRoot: true,
    level: 0,
  })

  const sortedLevels = Array.from(levels.value.entries()).sort((a, b) => a[0] - b[0])
  for (const [level, items] of sortedLevels) {
    const totalWidth = items.length * (NODE_W + H_GAP) - H_GAP
    const startX = (svgWidth.value - totalWidth) / 2 + NODE_W / 2
    const y = PADDING + level * (NODE_H + V_GAP) + NODE_H / 2

    items.forEach((item, i) => {
      nodes.push({
        id: item.id,
        label: item.title,
        status: item.status,
        x: startX + i * (NODE_W + H_GAP),
        y,
        w: NODE_W,
        h: NODE_H,
        fill: statusFill(item.status),
        stroke: statusColor(item.status),
        textColor: statusTextColor(item.status),
        isRoot: false,
        level,
      })
    })
  }
  return nodes
})

const svgEdges = computed(() => {
  const edges: any[] = []
  const rootX = svgWidth.value / 2
  const rootY = PADDING + NODE_H / 2

  for (const node of svgNodes.value) {
    if (node.isRoot) continue
    const isDirect = node.level === 1
    edges.push({
      x1: rootX,
      y1: rootY + (NODE_H + 8) / 2,
      x2: node.x,
      y2: node.y - node.h / 2,
      color: isDirect ? '#ef4444' : '#94a3b8',
      width: isDirect ? 2.5 : 1.5,
      dashed: !isDirect,
    })
  }
  return edges
})

function truncate(text: string, max: number) {
  return text.length > max ? text.slice(0, max) + '...' : text
}
</script>
