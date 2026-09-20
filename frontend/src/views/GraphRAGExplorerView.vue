<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('rag.title') }}</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('rag.subtitle') }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div class="lg:col-span-2 space-y-4">
        <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex gap-3">
            <div class="relative flex-1">
              <svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
              <input v-model="query" type="text" :placeholder="t('rag.searchPlaceholder')" :aria-label="t('rag.searchPlaceholder')" class="w-full rounded-lg border border-gray-300 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700" @keydown.enter="doSearch" />
            </div>
            <button class="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50" :disabled="store.loading || !query.trim()" @click="doSearch">
              <span v-if="store.loading" class="flex items-center gap-1"><span class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>{{ t('rag.searching') }}</span>
              <span v-else>{{ t('rag.search') }}</span>
            </button>
          </div>
          <div class="mt-3 flex items-center gap-4">
            <div class="flex items-center gap-2">
              <label class="text-xs text-gray-500">{{ t('rag.similarityThreshold') }}:</label>
              <input v-model="threshold" type="range" min="0" max="100" step="5" class="h-1.5 w-24 cursor-pointer accent-blue-600" />
              <span class="text-xs font-medium text-gray-700 dark:text-gray-300 w-8">{{ threshold }}%</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="text-xs text-gray-500">{{ t('rag.maxResults') }}:</label>
              <select v-model="maxResults" class="rounded border border-gray-300 px-2 py-1 text-xs dark:border-gray-600 dark:bg-gray-700">
                <option :value="5">5</option>
                <option :value="10">10</option>
                <option :value="20">20</option>
              </select>
            </div>
          </div>
        </div>

        <div v-if="store.searchResponse" class="text-xs text-gray-500">
          {{ t('rag.totalMatches', { count: store.searchResponse.totalMatches, time: store.searchResponse.searchTimeMs }) }}
          <span class="ml-2 text-gray-400">{{ t('rag.embeddingModel') }}: {{ store.searchResponse.embeddingModel }}</span>
        </div>

        <div class="space-y-3">
          <div v-for="(r, idx) in store.results" :key="r.id" class="cursor-pointer rounded-xl border p-4 transition-all" :class="store.selectedResult?.id === r.id ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500 dark:bg-blue-900/20' : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800'" @click="selectResult(r)">
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-mono text-gray-400">#{{ idx + 1 }}</span>
                  <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ r.issueTitle }}</span>
                  <span class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold" :class="similarityClass(r.similarity)">{{ (r.similarity * 100).toFixed(0) }}%</span>
                </div>
                <p class="mt-1.5 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">{{ r.solutionSummary }}</p>
                <div class="mt-2 flex items-center gap-3 text-[10px] text-gray-400">
                  <span>{{ r.issueId }}</span>
                  <span>{{ r.component }}</span>
                  <span>{{ formatDate(r.solutionDate) }}</span>
                  <span class="rounded bg-gray-100 px-1.5 py-0.5 dark:bg-gray-700">{{ r.contextNodes.length }} {{ t('rag.nodes') }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="store.results.length === 0 && !store.loading && store.lastQuery" class="rounded-xl border border-gray-200 bg-white p-12 text-center dark:border-gray-700 dark:bg-gray-800">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            <p class="mt-2 text-sm text-gray-500">{{ t('rag.noResults') }}</p>
            <p class="text-xs text-gray-400">{{ t('rag.noResultsHint') }}</p>
          </div>
          <div v-if="!store.lastQuery && store.results.length === 0" class="rounded-xl border border-gray-200 bg-white p-12 text-center dark:border-gray-700 dark:bg-gray-800">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
            <p class="mt-2 text-sm text-gray-500">{{ t('rag.noResultsDescription') }}</p>
          </div>
        </div>
      </div>

      <div class="space-y-4">
        <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <h3 class="mb-3 text-sm font-semibold text-gray-900 dark:text-white">{{ t('rag.topComponents') }}</h3>
          <div class="space-y-2">
            <div v-for="c in store.metrics.topComponents" :key="c.name" class="flex items-center justify-between">
              <span class="text-xs text-gray-700 dark:text-gray-300">{{ c.name }}</span>
              <span class="text-xs text-gray-400">{{ c.count }}</span>
            </div>
          </div>
          <div class="mt-3 border-t border-gray-100 pt-3 dark:border-gray-700">
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-500">{{ t('rag.totalEmbeddings') }}</span>
              <span class="font-medium text-gray-900 dark:text-white">{{ store.metrics.totalEmbeddings }}</span>
            </div>
            <div class="mt-1 flex items-center justify-between text-xs">
              <span class="text-gray-500">{{ t('rag.lastIndexed') }}</span>
              <span class="text-gray-700 dark:text-gray-300">{{ store.metrics.lastIndexedAt ? new Date(store.metrics.lastIndexedAt).toLocaleDateString() : '-' }}</span>
            </div>
          </div>
        </div>

        <div v-if="store.selectedResult" class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <div class="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('rag.subGraph') }}</h3>
            <p class="text-xs text-gray-500">{{ store.selectedResult.contextNodes.length }} {{ t('rag.nodes') }}, {{ store.selectedResult.contextEdges.length }} {{ t('rag.edges') }}</p>
          </div>
          <div class="p-4">
            <svg :viewBox="`0 0 ${svgWidth} ${svgHeight}`" class="w-full" :style="{ height: svgHeight + 'px' }">
              <defs>
                <marker id="rag-arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                  <polygon points="0 0, 8 3, 0 6" fill="currentColor" class="text-gray-400 dark:text-gray-500" />
                </marker>
              </defs>
              <g v-for="edge in layoutEdges" :key="edge.from + '-' + edge.to">
                <line :x1="edge.x1" :y1="edge.y1" :x2="edge.x2" :y2="edge.y2" class="stroke-gray-300 dark:stroke-gray-600" stroke-width="1.5" marker-end="url(#rag-arrow)" />
                <text :x="(edge.x1 + edge.x2) / 2" :y="(edge.y1 + edge.y2) / 2 - 5" text-anchor="middle" class="fill-gray-400 dark:fill-gray-500" font-size="8">{{ edge.type }}</text>
              </g>
              <g v-for="node in layoutNodes" :key="node.id">
                <circle :cx="node.x" :cy="node.y" :r="nodeR" :class="nodeColorClass(node.type)" stroke-width="2" />
                <text :x="node.x" :y="node.y + nodeR + 12" text-anchor="middle" class="fill-gray-700 dark:fill-gray-300" font-size="9" font-weight="500">{{ node.label }}</text>
              </g>
            </svg>
          </div>
        </div>
        <div v-else class="rounded-xl border border-gray-200 bg-white p-8 text-center dark:border-gray-700 dark:bg-gray-800">
          <p class="text-sm text-gray-400">{{ t('rag.clickResult') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRagStore } from '@/stores/ragStore'
import type { RAGResult } from '@/types/rag'

const { t } = useI18n()
const store = useRagStore()

const query = ref('')
const threshold = ref(50)
const maxResults = ref(10)

const svgWidth = 400
const svgHeight = 280
const nodeR = 16

function similarityClass(sim: number) {
  if (sim >= 0.9) return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
  if (sim >= 0.8) return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
  if (sim >= 0.7) return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300'
  return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
}

function nodeColorClass(type: string) {
  const m: Record<string, string> = {
    Issue: 'fill-red-200 stroke-red-400 dark:fill-red-900/40 dark:stroke-red-500',
    Component: 'fill-blue-200 stroke-blue-400 dark:fill-blue-900/40 dark:stroke-blue-500',
    Function: 'fill-green-200 stroke-green-400 dark:fill-green-900/40 dark:stroke-green-500',
    Class: 'fill-purple-200 stroke-purple-400 dark:fill-purple-900/40 dark:stroke-purple-500',
    Module: 'fill-amber-200 stroke-amber-400 dark:fill-amber-900/40 dark:stroke-amber-500',
    Interface: 'fill-teal-200 stroke-teal-400 dark:fill-teal-900/40 dark:stroke-teal-500',
  }
  return m[type] || m.Module
}

const layoutNodes = computed(() => {
  if (!store.selectedResult) return []
  const nodes = store.selectedResult.contextNodes
  const cx = svgWidth / 2
  const cy = svgHeight / 2
  const radius = 90
  return nodes.map((n, i) => {
    const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2
    return { ...n, x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) }
  })
})

const layoutEdges = computed(() => {
  if (!store.selectedResult) return []
  const nodeMap = new Map(layoutNodes.value.map(n => [n.id, n]))
  return store.selectedResult.contextEdges
    .filter(e => nodeMap.has(e.from) && nodeMap.has(e.to))
    .map(e => {
      const from = nodeMap.get(e.from)!
      const to = nodeMap.get(e.to)!
      return { ...e, x1: from.x, y1: from.y, x2: to.x, y2: to.y }
    })
})

async function doSearch() {
  if (!query.value.trim()) return
  await store.search(query.value, threshold.value / 100, maxResults.value)
}

function selectResult(r: RAGResult) {
  store.selectResult(r)
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString()
}
</script>
