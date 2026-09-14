<template>
  <div class="rich-text-editor border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden bg-white dark:bg-gray-700">
    <div class="flex items-center gap-0.5 border-b border-gray-200 dark:border-gray-600 px-2 py-1.5 bg-gray-50 dark:bg-gray-800">
      <button
        v-for="btn in toolbarButtons"
        :key="btn.label"
        class="rounded p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-600 transition-colors"
        :title="btn.label"
        @click="insertMarkdown(btn.syntax)"
      >
        <span class="text-xs font-mono font-bold">{{ btn.icon }}</span>
      </button>
      <div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1" />
      <button
        class="rounded p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-600 transition-colors"
        :class="{ 'text-blue-500 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30': showPreview }"
        :title="t('editor.preview')"
        @click="showPreview = !showPreview"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      </button>
    </div>

    <div class="relative">
      <div
        v-if="showSlashMenu"
        class="absolute z-20 mt-1 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden"
        :style="{ top: slashMenuTop + 'px', left: slashMenuLeft + 'px' }"
      >
        <div class="px-3 py-1.5 text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
          {{ t('editor.commands') }}
        </div>
        <button
          v-for="(cmd, idx) in filteredSlashCommands"
          :key="cmd.id"
          class="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-left transition-colors"
          :class="slashMenuIndex === idx ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50'"
          @click="executeSlashCommand(cmd)"
          @mouseenter="slashMenuIndex = idx"
        >
          <span class="text-base">{{ cmd.icon }}</span>
          <div>
            <div class="font-medium">{{ cmd.label }}</div>
            <div class="text-[10px] text-gray-400 dark:text-gray-500">{{ cmd.description }}</div>
          </div>
        </button>
      </div>

      <textarea
        v-if="!showPreview"
        ref="textareaRef"
        v-model="localValue"
        :rows="rows"
        :aria-label="placeholder || 'Text editor'"
        class="w-full px-3 py-2 text-sm bg-transparent text-gray-900 dark:text-gray-100 resize-none focus:outline-none placeholder-gray-400"
        :placeholder="placeholder"
        @input="onInput"
        @keydown="onKeydown"
        @blur="onBlur"
      />
      <div v-else class="p-3 min-h-[80px]">
        <MarkdownRenderer :content="localValue" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import MarkdownRenderer from '@/components/analysis/MarkdownRenderer.vue'

const { t } = useI18n()

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  rows?: number
}>(), {
  placeholder: '',
  rows: 6,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const localValue = ref(props.modelValue)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const showPreview = ref(false)

const showSlashMenu = ref(false)
const slashMenuTop = ref(0)
const slashMenuLeft = ref(0)
const slashMenuIndex = ref(0)
const slashQuery = ref('')

watch(() => props.modelValue, (v) => {
  if (v !== localValue.value) localValue.value = v
})

watch(localValue, (v) => {
  emit('update:modelValue', v)
})

const toolbarButtons = [
  { icon: 'B', label: 'Bold', syntax: '**' },
  { icon: 'I', label: 'Italic', syntax: '*' },
  { icon: '<>', label: 'Code', syntax: '`' },
  { icon: 'H1', label: 'Heading 1', syntax: '# ' },
  { icon: 'H2', label: 'Heading 2', syntax: '## ' },
  { icon: 'H3', label: 'Heading 3', syntax: '### ' },
  { icon: '—', label: 'Divider', syntax: '\n---\n' },
]

interface SlashCommand {
  id: string
  icon: string
  label: string
  description: string
  insert: string
}

const slashCommands: SlashCommand[] = [
  { id: 'heading1', icon: 'H1', label: 'Heading 1', description: 'Large section heading', insert: '# ' },
  { id: 'heading2', icon: 'H2', label: 'Heading 2', description: 'Medium section heading', insert: '## ' },
  { id: 'heading3', icon: 'H3', label: 'Heading 3', description: 'Small section heading', insert: '### ' },
  { id: 'bold', icon: 'B', label: 'Bold', description: 'Bold text', insert: '**text**' },
  { id: 'italic', icon: 'I', label: 'Italic', description: 'Italic text', insert: '*text*' },
  { id: 'code', icon: '<>', label: 'Code', description: 'Inline code', insert: '`code`' },
  { id: 'codeblock', icon: '{ }', label: 'Code Block', description: 'Syntax highlighted code', insert: '```\ncode\n```' },
  { id: 'mermaid', icon: '📊', label: 'Mermaid Diagram', description: 'Flowchart or diagram', insert: '```mermaid\ngraph TD\n    A-->B\n```' },
  { id: 'list', icon: '•', label: 'Bullet List', description: 'Unordered list', insert: '- ' },
  { id: 'checklist', icon: '☑', label: 'Checklist', description: 'Task checklist', insert: '- [ ] ' },
  { id: 'table', icon: '▦', label: 'Table', description: 'Markdown table', insert: '| Column | Column |\n|--------|--------|\n| Cell   | Cell   |' },
  { id: 'quote', icon: '"', label: 'Quote', description: 'Blockquote', insert: '> ' },
  { id: 'divider', icon: '—', label: 'Divider', description: 'Horizontal rule', insert: '\n---\n' },
]

const filteredSlashCommands = computed(() => {
  if (!slashQuery.value) return slashCommands
  const q = slashQuery.value.toLowerCase()
  return slashCommands.filter(
    (c) => c.label.toLowerCase().includes(q) || c.description.toLowerCase().includes(q)
  )
})

function insertMarkdown(syntax: string) {
  const ta = textareaRef.value
  if (!ta) return
  const start = ta.selectionStart
  const end = ta.selectionEnd
  const selected = localValue.value.substring(start, end)
  const before = localValue.value.substring(0, start)
  const after = localValue.value.substring(end)

  if (syntax === '**' || syntax === '*' || syntax === '`') {
    const replacement = selected ? syntax + selected + syntax : syntax + 'text' + syntax
    localValue.value = before + replacement + after
    nextTick(() => {
      ta.selectionStart = start + syntax.length
      ta.selectionEnd = start + syntax.length + (selected.length || 4)
      ta.focus()
    })
  } else if (syntax.startsWith('# ') || syntax === '\n---\n') {
    localValue.value = before + syntax + (selected || '') + after
    nextTick(() => {
      ta.selectionStart = start + syntax.length
      ta.selectionEnd = start + syntax.length + (selected?.length || 0)
      ta.focus()
    })
  } else {
    localValue.value = before + syntax + (selected || '') + after
    nextTick(() => {
      ta.selectionStart = start + syntax.length
      ta.selectionEnd = start + syntax.length + (selected?.length || 0)
      ta.focus()
    })
  }
}

function onInput() {
  const ta = textareaRef.value
  if (!ta) return
  const pos = ta.selectionStart
  const textBefore = localValue.value.substring(0, pos)
  const lastNewline = textBefore.lastIndexOf('\n')
  const currentLine = textBefore.substring(lastNewline + 1)

  if (currentLine === '/') {
    showSlashMenu.value = true
    slashQuery.value = ''
    slashMenuIndex.value = 0
    updateSlashMenuPosition(ta)
  } else if (showSlashMenu.value && currentLine.startsWith('/')) {
    slashQuery.value = currentLine.substring(1)
    slashMenuIndex.value = 0
  } else {
    showSlashMenu.value = false
  }
}

function onKeydown(e: KeyboardEvent) {
  if (showSlashMenu.value) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      slashMenuIndex.value = (slashMenuIndex.value + 1) % filteredSlashCommands.value.length
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      slashMenuIndex.value = (slashMenuIndex.value - 1 + filteredSlashCommands.value.length) % filteredSlashCommands.value.length
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const cmd = filteredSlashCommands.value[slashMenuIndex.value]
      if (cmd) executeSlashCommand(cmd)
    } else if (e.key === 'Escape') {
      e.preventDefault()
      showSlashMenu.value = false
    }
    return
  }

  if (e.key === 'Tab') {
    e.preventDefault()
    const ta = textareaRef.value
    if (!ta) return
    const start = ta.selectionStart
    localValue.value = localValue.value.substring(0, start) + '  ' + localValue.value.substring(ta.selectionEnd)
    nextTick(() => {
      ta.selectionStart = ta.selectionEnd = start + 2
    })
  }
}

function executeSlashCommand(cmd: SlashCommand) {
  const ta = textareaRef.value
  if (!ta) return
  const pos = ta.selectionStart
  const textBefore = localValue.value.substring(0, pos)
  const lastNewline = textBefore.lastIndexOf('\n')
  const lineStart = lastNewline + 1

  const before = localValue.value.substring(0, lineStart)
  const after = localValue.value.substring(pos)

  localValue.value = before + cmd.insert + after
  showSlashMenu.value = false

  nextTick(() => {
    const newPos = lineStart + cmd.insert.length
    ta.selectionStart = newPos
    ta.selectionEnd = newPos
    ta.focus()
  })
}

function updateSlashMenuPosition(ta: HTMLTextAreaElement) {
  const rect = ta.getBoundingClientRect()
  const lines = localValue.value.substring(0, ta.selectionStart).split('\n')
  const lineHeight = 20
  slashMenuTop.value = Math.min(lines.length * lineHeight + 8, rect.height - 200)
  slashMenuLeft.value = 8
}

function onBlur() {
  setTimeout(() => {
    showSlashMenu.value = false
  }, 200)
}
</script>
