<template>
  <div class="markdown-body prose prose-sm dark:prose-invert max-w-none" v-html="rendered"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ content: string }>()

const rendered = computed(() => renderMarkdown(props.content))

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function renderMarkdown(md: string): string {
  let html = escapeHtml(md)
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  html = html.replace(/^- \[x\] (.+)$/gm, '<div class="flex items-center gap-2"><input type="checkbox" checked disabled class="h-4 w-4 rounded border-gray-300 text-green-600" /><span class="line-through text-gray-500">$1</span></div>')
  html = html.replace(/^- \[ \] (.+)$/gm, '<div class="flex items-center gap-2"><input type="checkbox" disabled class="h-4 w-4 rounded border-gray-300" /><span>$1</span></div>')
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul class="list-disc pl-5 space-y-1">${match}</ul>`)
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
  html = html.replace(/^-{3,}$/gm, '<hr class="my-3 border-gray-200 dark:border-gray-700" />')
  html = html.replace(/\n{2,}/g, '</p><p class="mt-2">')
  html = `<p>${html}</p>`
  html = html.replace(/<p><\/p>/g, '')
  return html
}
</script>

<style scoped>
.markdown-body :deep(h1) { @apply text-lg font-bold mt-4 mb-2 text-gray-900 dark:text-white; }
.markdown-body :deep(h2) { @apply text-base font-bold mt-3 mb-1.5 text-gray-900 dark:text-white; }
.markdown-body :deep(h3) { @apply text-sm font-bold mt-2 mb-1 text-gray-800 dark:text-gray-200; }
.markdown-body :deep(code) { @apply rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono text-gray-800 dark:bg-gray-800 dark:text-gray-200; }
.markdown-body :deep(strong) { @apply font-semibold text-gray-900 dark:text-white; }
.markdown-body :deep(ul) { @apply my-1; }
.markdown-body :deep(li) { @apply text-sm text-gray-700 dark:text-gray-300; }
.markdown-body :deep(hr) { @apply border-gray-200 dark:border-gray-700; }
</style>
