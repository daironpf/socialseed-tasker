<template>
  <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
    <div class="flex flex-wrap items-center gap-1.5 border-b border-gray-200 px-3 py-2 dark:border-gray-700">
      <span class="mr-1 text-[10px] font-semibold uppercase text-gray-400">{{ t('agentStudio.prompt.variables') }}</span>
      <button
        v-for="variable in PROMPT_VARIABLES"
        :key="variable"
        class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
        @click="insertVariable(variable)"
      >
        {{ variable }}
      </button>
      <span class="ml-auto font-mono text-[10px] text-gray-400">{{ modelValue.length }} / 2000</span>
    </div>

    <textarea
      :value="modelValue"
      rows="7"
      class="w-full resize-none bg-transparent px-3 py-2.5 font-mono text-xs text-gray-800 focus:outline-none dark:text-gray-200"
      :placeholder="t('agentStudio.prompt.placeholder')"
      @input="onInput"
    />

    <div v-if="issues.length" class="space-y-1 border-t border-gray-100 px-3 py-2 dark:border-gray-700/60">
      <div
        v-for="(issue, i) in issues"
        :key="i"
        class="flex items-start gap-1.5 text-[11px]"
        :class="issue.level === 'error' ? 'text-red-600 dark:text-red-400' : issue.level === 'warning' ? 'text-amber-600 dark:text-amber-400' : 'text-sky-600 dark:text-sky-400'"
      >
        <span class="mt-0.5">{{ issue.level === 'error' ? '✕' : issue.level === 'warning' ? '!' : 'i' }}</span>
        <span>{{ issue.message }}</span>
      </div>
    </div>
    <div v-else class="border-t border-gray-100 px-3 py-2 text-[11px] text-emerald-600 dark:border-gray-700/60 dark:text-emerald-400">
      {{ t('agentStudio.prompt.valid') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { PROMPT_VARIABLES } from '@/types/agentStudio'

const props = defineProps<{
  modelValue: string
  tools: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { t } = useI18n()

const issues = computed(() => {
  const result: Array<{ level: 'error' | 'warning' | 'info'; message: string }> = []
  const prompt = props.modelValue
  if (!prompt.trim()) {
    result.push({ level: 'error', message: t('agentStudio.prompt.needPrompt') })
    return result
  }
  if (prompt.trim().length < 80) {
    result.push({ level: 'warning', message: t('agentStudio.prompt.tooShort') })
  }
  if (prompt.length > 2000) {
    result.push({ level: 'warning', message: t('agentStudio.prompt.tooLong') })
  }
  const lower = prompt.toLowerCase()
  const missing = props.tools.filter(tool => !lower.includes(tool.split('_')[0]))
  if (props.tools.length && missing.length) {
    result.push({ level: 'info', message: t('agentStudio.prompt.toolsNotMentioned', { tools: missing.join(', ') }) })
  }
  if (!/\b(must|should|never|always|only)\b/i.test(prompt)) {
    result.push({ level: 'info', message: t('agentStudio.prompt.addRules') })
  }
  return result
})

function onInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLTextAreaElement).value)
}

function insertVariable(variable: string) {
  emit('update:modelValue', `${props.modelValue}${props.modelValue && !props.modelValue.endsWith(' ') ? ' ' : ''}${variable}`)
}
</script>
