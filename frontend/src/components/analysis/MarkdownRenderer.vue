<template>
  <div class="markdown-body prose prose-sm dark:prose-invert max-w-none" v-html="rendered"></div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import mermaid from 'mermaid'

const { t } = useI18n()

const props = defineProps<{ content: string }>()

const rendered = ref('')
const mermaidIdCounter = ref(0)

let isDark = document.documentElement.classList.contains('dark')

mermaid.initialize({
  startOnLoad: false,
  theme: isDark ? 'dark' : 'default',
  securityLevel: 'strict',
})

const darkObserver = new MutationObserver(() => {
  const newDark = document.documentElement.classList.contains('dark')
  if (newDark !== isDark) {
    isDark = newDark
    mermaid.initialize({
      startOnLoad: false,
      theme: isDark ? 'dark' : 'default',
      securityLevel: 'strict',
    })
  }
})
darkObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

onUnmounted(() => darkObserver.disconnect())

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

async function renderMermaidDiagrams(html: string): Promise<string> {
  const mermaidRegex = /<code class="language-mermaid">([\s\S]*?)<\/code>/g
  let match
  let result = html
  const diagrams: { id: string; code: string }[] = []

  while ((match = mermaidRegex.exec(html)) !== null) {
    const id = `mermaid-${++mermaidIdCounter.value}`
    diagrams.push({ id, code: match[1] })
    result = result.replace(match[0], `<div class="mermaid-container" id="${id}"></div>`)
  }

  for (const diagram of diagrams) {
    try {
      const { svg } = await mermaid.render(diagram.id, diagram.code)
      result = result.replace(
        `<div class="mermaid-container" id="${diagram.id}"></div>`,
        `<div class="mermaid-diagram my-3">${svg}</div>`
      )
    } catch {
      result = result.replace(
        `<div class="mermaid-container" id="${diagram.id}"></div>`,
        `<div class="mermaid-error rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-300 my-2">${t('analysis.invalidMermaid')}</div>`
      )
    }
  }

  return result
}

function renderMarkdown(md: string): string {
  let html = escapeHtml(md)

  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  html = html.replace(/```mermaid\n([\s\S]*?)```/g, (_m, code) => {
    return `<code class="language-mermaid">${code}</code>`
  })

  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang, code) => {
    if (lang === 'mermaid') return `<code class="language-mermaid">${code}</code>`
    return `<pre class="bg-gray-100 dark:bg-gray-800 rounded p-3 text-xs font-mono overflow-x-auto my-2"><code class="language-${lang}">${code}</code></pre>`
  })

  html = html.replace(/^- \[x\] (.+)$/gm, '<div class="flex items-center gap-2"><input type="checkbox" checked disabled class="h-4 w-4 rounded border-gray-300 text-green-600" /><span class="line-through text-gray-500">$1</span></div>')
  html = html.replace(/^- \[ \] (.+)$/gm, '<div class="flex items-center gap-2"><input type="checkbox" disabled class="h-4 w-4 rounded border-gray-300" /><span>$1</span></div>')
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul class="list-disc pl-5 space-y-1">${match}</ul>`)
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')

  html = html.replace(/^> (.+)$/gm, '<blockquote class="border-l-4 border-gray-300 dark:border-gray-600 pl-3 text-gray-600 dark:text-gray-400 italic my-2">$1</blockquote>')

  html = html.replace(/\|(.+)\|/g, (match) => {
    const cells = match.split('|').filter((c: string) => c.trim())
    if (cells.every((c: string) => /^[\s-]+$/.test(c))) {
      return ''
    }
    const cellHtml = cells.map((c: string) => `<td class="border border-gray-200 dark:border-gray-700 px-3 py-1.5">${c.trim()}</td>`).join('')
    return `<tr>${cellHtml}</tr>`
  })
  html = html.replace(/(<tr>.*<\/tr>\n?)+/g, (match) => `<table class="border-collapse border border-gray-200 dark:border-gray-700 my-2 text-sm">${match}</table>`)

  html = html.replace(/^-{3,}$/gm, '<hr class="my-3 border-gray-200 dark:border-gray-700" />')
  html = html.replace(/\n{2,}/g, '</p><p class="mt-2">')
  html = `<p>${html}</p>`
  html = html.replace(/<p><\/p>/g, '')

  return html
}

watch(
  () => props.content,
  async () => {
    const html = renderMarkdown(props.content)
    rendered.value = await renderMermaidDiagrams(html)
  },
  { immediate: true }
)
</script>

<style scoped>
.markdown-body :deep(h1) { @apply text-lg font-bold mt-4 mb-2 text-gray-900 dark:text-white; }
.markdown-body :deep(h2) { @apply text-base font-bold mt-3 mb-1.5 text-gray-900 dark:text-white; }
.markdown-body :deep(h3) { @apply text-sm font-bold mt-2 mb-1 text-gray-800 dark:text-gray-200; }
.markdown-body :deep(code) { @apply rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono text-gray-800 dark:bg-gray-800 dark:text-gray-200; }
.markdown-body :deep(pre code) { @apply bg-transparent p-0 text-gray-800 dark:text-gray-200; }
.markdown-body :deep(strong) { @apply font-semibold text-gray-900 dark:text-white; }
.markdown-body :deep(ul) { @apply my-1; }
.markdown-body :deep(li) { @apply text-sm text-gray-700 dark:text-gray-300; }
.markdown-body :deep(hr) { @apply border-gray-200 dark:border-gray-700; }
.markdown-body :deep(blockquote) { @apply border-l-4 border-gray-300 dark:border-gray-600 pl-3 text-gray-600 dark:text-gray-400 italic; }
.markdown-body :deep(table) { @apply border-collapse text-sm; }
.markdown-body :deep(td) { @apply border border-gray-200 dark:border-gray-700 px-3 py-1.5; }
.markdown-body :deep(.mermaid-diagram) { @apply my-3 overflow-x-auto; }
.markdown-body :deep(.mermaid-error) { @apply rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-300 my-2; }
</style>
