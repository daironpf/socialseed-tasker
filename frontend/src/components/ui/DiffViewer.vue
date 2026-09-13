<template>
  <div class="diff-viewer rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
    <div class="flex items-center justify-between bg-gray-50 dark:bg-gray-800 px-3 py-2 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center gap-2">
        <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span class="text-xs font-medium text-gray-600 dark:text-gray-300">{{ filename }}</span>
        <span v-if="stats" class="text-[10px] text-gray-400">
          <span class="text-green-600 dark:text-green-400">+{{ stats.added }}</span>
          <span class="mx-0.5">/</span>
          <span class="text-red-600 dark:text-red-400">-{{ stats.removed }}</span>
        </span>
      </div>
      <div class="flex items-center gap-1">
        <button
          class="rounded px-2 py-1 text-[10px] font-medium transition-colors"
          :class="viewMode === 'unified' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700'"
          @click="viewMode = 'unified'"
        >
          {{ t('diff.unified') }}
        </button>
        <button
          class="rounded px-2 py-1 text-[10px] font-medium transition-colors"
          :class="viewMode === 'split' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700'"
          @click="viewMode = 'split'"
        >
          {{ t('diff.split') }}
        </button>
        <div class="w-px h-4 bg-gray-300 dark:bg-gray-600 mx-1" />
        <button
          class="rounded p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 dark:hover:text-gray-300 dark:hover:bg-gray-700 transition-colors"
          :title="t('diff.copy')"
          @click="copyDiff"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
        <button
          class="rounded p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 dark:hover:text-gray-300 dark:hover:bg-gray-700 transition-colors"
          :title="t('diff.download')"
          @click="downloadPatch"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </button>
      </div>
    </div>

    <div v-if="viewMode === 'unified'" class="overflow-x-auto">
      <table class="w-full text-xs font-mono">
        <tbody>
          <tr
            v-for="(line, idx) in parsedLines"
            :key="idx"
            class="border-b border-gray-100 dark:border-gray-800"
            :class="{
              'bg-green-50 dark:bg-green-900/10': line.type === 'add',
              'bg-red-50 dark:bg-red-900/10': line.type === 'remove',
              'bg-amber-50 dark:bg-amber-900/10': line.type === 'context',
            }"
          >
            <td class="w-12 px-2 py-0.5 text-right text-gray-400 select-none border-r border-gray-200 dark:border-gray-700">
              {{ line.oldLine ?? '' }}
            </td>
            <td class="w-12 px-2 py-0.5 text-right text-gray-400 select-none border-r border-gray-200 dark:border-gray-700">
              {{ line.newLine ?? '' }}
            </td>
            <td class="w-6 px-1 py-0.5 text-center select-none"
              :class="{
                'text-green-600 dark:text-green-400': line.type === 'add',
                'text-red-600 dark:text-red-400': line.type === 'remove',
                'text-gray-400': line.type === 'context',
              }"
            >
              {{ line.type === 'add' ? '+' : line.type === 'remove' ? '-' : ' ' }}
            </td>
            <td class="px-2 py-0.5 whitespace-pre"
              :class="{
                'text-green-800 dark:text-green-300': line.type === 'add',
                'text-red-800 dark:text-red-300': line.type === 'remove',
                'text-gray-700 dark:text-gray-300': line.type === 'context',
              }"
            >{{ line.content }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="overflow-x-auto">
      <div class="grid grid-cols-2 divide-x divide-gray-200 dark:divide-gray-700">
        <div>
          <div class="bg-gray-50 dark:bg-gray-800 px-3 py-1 text-[10px] font-medium text-gray-500 border-b border-gray-200 dark:border-gray-700">
            {{ t('diff.original') }}
          </div>
          <table class="w-full text-xs font-mono">
            <tbody>
              <tr
                v-for="(line, idx) in leftLines"
                :key="'l-' + idx"
                class="border-b border-gray-100 dark:border-gray-800"
                :class="{
                  'bg-red-50 dark:bg-red-900/10': line.type === 'remove',
                  'bg-gray-50 dark:bg-gray-800/50': line.type === 'empty',
                }"
              >
                <td class="w-10 px-2 py-0.5 text-right text-gray-400 select-none border-r border-gray-200 dark:border-gray-700">
                  {{ line.line ?? '' }}
                </td>
                <td class="w-5 px-1 py-0.5 text-center text-red-600 dark:text-red-400 select-none">
                  {{ line.type === 'remove' ? '-' : ' ' }}
                </td>
                <td class="px-2 py-0.5 whitespace-pre"
                  :class="{
                    'text-red-800 dark:text-red-300': line.type === 'remove',
                    'text-gray-300 dark:text-gray-600': line.type === 'empty',
                    'text-gray-700 dark:text-gray-300': line.type === 'context',
                  }"
                >{{ line.content }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div>
          <div class="bg-gray-50 dark:bg-gray-800 px-3 py-1 text-[10px] font-medium text-gray-500 border-b border-gray-200 dark:border-gray-700">
            {{ t('diff.modified') }}
          </div>
          <table class="w-full text-xs font-mono">
            <tbody>
              <tr
                v-for="(line, idx) in rightLines"
                :key="'r-' + idx"
                class="border-b border-gray-100 dark:border-gray-800"
                :class="{
                  'bg-green-50 dark:bg-green-900/10': line.type === 'add',
                  'bg-gray-50 dark:bg-gray-800/50': line.type === 'empty',
                }"
              >
                <td class="w-10 px-2 py-0.5 text-right text-gray-400 select-none border-r border-gray-200 dark:border-gray-700">
                  {{ line.line ?? '' }}
                </td>
                <td class="w-5 px-1 py-0.5 text-center text-green-600 dark:text-green-400 select-none">
                  {{ line.type === 'add' ? '+' : ' ' }}
                </td>
                <td class="px-2 py-0.5 whitespace-pre"
                  :class="{
                    'text-green-800 dark:text-green-300': line.type === 'add',
                    'text-gray-300 dark:text-gray-600': line.type === 'empty',
                    'text-gray-700 dark:text-gray-300': line.type === 'context',
                  }"
                >{{ line.content }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="copied" class="absolute top-2 right-2 rounded bg-green-600 px-2 py-1 text-xs text-white shadow-lg">
      {{ t('diff.copied') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  content: string
  filename?: string
}>()

const viewMode = ref<'unified' | 'split'>('unified')
const copied = ref(false)

interface ParsedLine {
  type: 'add' | 'remove' | 'context' | 'empty'
  content: string
  oldLine: number | null
  newLine: number | null
  line?: number | null
}

const parsedLines = computed<ParsedLine[]>(() => {
  const lines = props.content.split('\n')
  const result: ParsedLine[] = []
  let oldLine = 0
  let newLine = 0

  for (const line of lines) {
    if (line.startsWith('@@')) {
      const match = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/)
      if (match) {
        oldLine = parseInt(match[1]) - 1
        newLine = parseInt(match[2]) - 1
      }
      continue
    }
    if (line.startsWith('---') || line.startsWith('+++') || line.startsWith('diff ')) continue

    if (line.startsWith('+')) {
      newLine++
      result.push({ type: 'add', content: line.substring(1), oldLine: null, newLine })
    } else if (line.startsWith('-')) {
      oldLine++
      result.push({ type: 'remove', content: line.substring(1), oldLine, newLine: null })
    } else {
      oldLine++
      newLine++
      result.push({ type: 'context', content: line.startsWith(' ') ? line.substring(1) : line, oldLine, newLine })
    }
  }

  return result
})

const stats = computed(() => {
  let added = 0
  let removed = 0
  for (const line of parsedLines.value) {
    if (line.type === 'add') added++
    if (line.type === 'remove') removed++
  }
  return { added, removed }
})

const leftLines = computed(() => {
  const result: { type: string; content: string; line: number | null }[] = []
  for (const line of parsedLines.value) {
    if (line.type === 'add') {
      result.push({ type: 'empty', content: '', line: null })
    } else {
      result.push({ type: line.type, content: line.content, line: line.oldLine })
    }
  }
  return result
})

const rightLines = computed(() => {
  const result: { type: string; content: string; line: number | null }[] = []
  for (const line of parsedLines.value) {
    if (line.type === 'remove') {
      result.push({ type: 'empty', content: '', line: null })
    } else {
      result.push({ type: line.type, content: line.content, line: line.newLine })
    }
  }
  return result
})

async function copyDiff() {
  try {
    await navigator.clipboard.writeText(props.content)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback
  }
}

function downloadPatch() {
  const blob = new Blob([props.content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = props.filename ? `${props.filename}.patch` : 'changes.patch'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.diff-viewer {
  @apply relative;
}
</style>
