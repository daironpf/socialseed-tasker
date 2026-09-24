<template>
  <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
    <!-- Toolbar -->
    <div class="flex flex-wrap items-center gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-700">
      <div class="flex items-center gap-2">
        <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <span class="text-sm font-semibold text-gray-800 dark:text-gray-200">{{ t('piiSuite.title') }}</span>
        <span
          class="rounded-full px-2 py-0.5 text-[10px] font-bold"
          :class="detections.length
            ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
            : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'"
        >
          {{ detections.length ? t('piiSuite.detections', { count: detections.length }) : t('piiSuite.clean') }}
        </span>
      </div>

      <div class="ml-auto flex flex-wrap items-center gap-2">
        <label class="flex cursor-pointer items-center gap-1.5 text-xs text-gray-600 dark:text-gray-300">
          <input v-model="maskEnabled" type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-sky-600 focus:ring-sky-500">
          {{ t('piiSuite.maskToggle') }}
        </label>
        <button
          class="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-700 dark:bg-gray-600 dark:hover:bg-gray-500"
          @click="applyMask"
        >
          {{ t('piiSuite.maskAction') }}
        </button>
        <button
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="revealed = !revealed"
        >
          {{ revealed ? t('piiSuite.hideAction') : t('piiSuite.revealAction') }}
        </button>
      </div>
    </div>

    <div class="space-y-3 p-4">
      <!-- Editable source -->
      <textarea
        v-if="editable"
        v-model="text"
        rows="4"
        class="w-full rounded-lg border border-gray-200 bg-gray-50 p-3 font-mono text-xs text-gray-800 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
        :placeholder="t('piiSuite.placeholder')"
        @input="emit('update:modelValue', text)"
      />

      <!-- Detections -->
      <div v-if="detections.length" class="space-y-1.5">
        <div class="text-[10px] font-semibold uppercase text-gray-400">{{ t('piiSuite.detectedHeader') }}</div>
        <div
          v-for="(d, i) in detections"
          :key="i"
          class="flex flex-wrap items-center gap-2 rounded-lg border px-3 py-1.5 text-xs"
          :class="getSeverityBg(d.severity)"
        >
          <span class="font-bold uppercase" :class="getSeverityColor(d.severity)">{{ t(`piiSuite.categories.${d.category}`) }}</span>
          <span class="font-mono text-gray-600 dark:text-gray-300">→ {{ d.masked }}</span>
          <span class="ml-auto truncate font-mono text-[10px] text-gray-400" :title="d.match">{{ d.match }}</span>
        </div>
      </div>

      <!-- Before / After preview -->
      <div :class="compact ? 'grid grid-cols-1 gap-3' : 'grid grid-cols-1 gap-3 md:grid-cols-2'">
        <div>
          <div class="mb-1 text-[10px] font-semibold uppercase text-gray-400">{{ t('piiSuite.before') }}</div>
          <pre class="max-h-48 overflow-y-auto whitespace-pre-wrap break-words rounded-lg bg-gray-50 p-3 font-mono text-[11px] text-gray-700 dark:bg-gray-900 dark:text-gray-300">{{ text }}</pre>
        </div>
        <div>
          <div class="mb-1 text-[10px] font-semibold uppercase text-gray-400">{{ t('piiSuite.after') }}</div>
          <pre class="max-h-48 overflow-y-auto whitespace-pre-wrap break-words rounded-lg p-3 font-mono text-[11px]"
            :class="maskEnabled && !revealed ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-300' : 'bg-gray-50 text-gray-500 dark:bg-gray-900 dark:text-gray-400'"
          >{{ previewText }}</pre>
        </div>
      </div>

      <div v-if="revealed" class="flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-2 text-[11px] text-amber-700 dark:bg-amber-900/20 dark:text-amber-300">
        <svg class="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {{ t('piiSuite.revealNotice') }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { detectPII, getSeverityBg, getSeverityColor } from '@/utils/piiDetector'

const props = withDefaults(defineProps<{
  modelValue?: string
  editable?: boolean
  compact?: boolean
}>(), {
  modelValue: undefined,
  editable: true,
  compact: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { t } = useI18n()

const SAMPLE = [
  'Contact: jane.doe@acme-corp.io for follow-up.',
  'Card 4111 1111 1111 1111 exp 12/28 cvv 321.',
  'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U',
  'API key sk-live-9f8e7d6c5b4a3210 configured for prod.',
  'Call support at +1 (415) 555-0198 if deploy fails.',
  'password: hunter2supersecret in config fallback.',
].join('\n')

const text = ref(props.modelValue ?? SAMPLE)
const maskEnabled = ref(true)
const revealed = ref(false)

watch(() => props.modelValue, value => {
  if (value !== undefined && value !== text.value) text.value = value
})

const detections = computed(() => detectPII(text.value))

const maskedText = computed(() => {
  let result = text.value
  const ordered = [...detections.value].sort((a, b) => b.start - a.start)
  for (const d of ordered) {
    result = result.slice(0, d.start) + d.masked + result.slice(d.end)
  }
  return result
})

const showMasked = computed(() => maskEnabled.value && !revealed.value)
const previewText = computed(() => (showMasked.value ? maskedText.value : text.value))

function applyMask() {
  if (!detections.value.length) return
  text.value = maskedText.value
  maskEnabled.value = true
  revealed.value = false
  emit('update:modelValue', text.value)
}
</script>
