<template>
  <div
    class="pointer-events-auto flex items-start gap-3 p-4 shadow-lg transition-all"
    :class="containerClasses"
    role="alert"
  >
    <div
      v-if="uiStore.toastTheme === 'enterprise'"
      class="absolute left-0 top-0 h-1 w-full"
      :class="stripColor"
    />

    <div class="shrink-0 mt-0.5" :class="iconColorClass">
      <svg v-if="toast.type === 'success'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <svg v-else-if="toast.type === 'error'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <svg v-else-if="toast.type === 'warning'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
      <svg v-else class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>

    <div class="min-w-0 flex-1">
      <span
        v-if="uiStore.toastTheme === 'enterprise'"
        class="mb-0.5 block font-mono text-[9px] font-bold uppercase tracking-wider"
        :class="labelColorClass"
      >
        {{ t(`toastTheme.types.${toast.type}`) }}
      </span>
      <p class="text-sm font-medium" :class="textClass">{{ toast.message }}</p>
    </div>

    <button
      class="shrink-0 rounded p-0.5 transition-opacity"
      :class="uiStore.toastTheme === 'enterprise' ? 'text-gray-400 hover:text-gray-600' : 'opacity-60 hover:opacity-100'"
      @click="$emit('dismiss', toast.id)"
      :aria-label="t('toast.dismiss')"
    >
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- Progress bar for auto-close -->
    <div
      v-if="!toast.persistent"
      class="absolute bottom-0 left-0 h-0.5 transition-all"
      :class="[progressColor, uiStore.toastTheme === 'enterprise' ? 'rounded-none' : 'rounded-b-lg']"
      :style="{ width: progressWidth + '%' }"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUiStore } from '@/stores/uiStore'
import type { Toast } from '@/composables/useToast'

const { t } = useI18n()
const uiStore = useUiStore()

const props = defineProps<{
  toast: Toast
}>()

defineEmits<{
  dismiss: [id: string]
}>()

const elapsed = ref(0)
let raf: number

onMounted(() => {
  const start = performance.now()
  function tick(now: number) {
    elapsed.value = now - start
    raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
})

onUnmounted(() => cancelAnimationFrame(raf))

const progressWidth = computed(() => {
  if (props.toast.persistent) return 100
  return Math.min((elapsed.value / props.toast.duration) * 100, 100)
})

const containerClasses = computed(() => {
  const theme = uiStore.toastTheme
  if (theme === 'minimal') {
    return 'relative overflow-hidden rounded-md border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800'
  }
  if (theme === 'enterprise') {
    return `relative overflow-hidden rounded-none border-0 border-l-4 bg-white dark:bg-gray-800 ${typeColors.value.borderLeft}`
  }
  switch (props.toast.type) {
    case 'success': return 'relative overflow-hidden rounded-lg border border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-900/30 dark:text-green-300'
    case 'error': return 'relative overflow-hidden rounded-lg border border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300'
    case 'warning': return 'relative overflow-hidden rounded-lg border border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300'
    default: return 'relative overflow-hidden rounded-lg border border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
  }
})

const typeColors = computed(() => {
  switch (props.toast.type) {
    case 'success':
      return { strip: 'bg-green-500', borderLeft: 'border-l-green-500', label: 'text-green-600 dark:text-green-400' }
    case 'error':
      return { strip: 'bg-red-500', borderLeft: 'border-l-red-500', label: 'text-red-600 dark:text-red-400' }
    case 'warning':
      return { strip: 'bg-amber-500', borderLeft: 'border-l-amber-500', label: 'text-amber-600 dark:text-amber-400' }
    default:
      return { strip: 'bg-blue-500', borderLeft: 'border-l-blue-500', label: 'text-blue-600 dark:text-blue-400' }
  }
})

const stripColor = computed(() => typeColors.value.strip)

const textClass = computed(() => {
  const theme = uiStore.toastTheme
  if (theme === 'minimal') return 'text-gray-700 dark:text-gray-200'
  if (theme === 'enterprise') return 'text-gray-900 dark:text-white'
  return ''
})

const iconColorClass = computed(() => {
  const theme = uiStore.toastTheme
  if (theme === 'minimal') return 'text-gray-400 dark:text-gray-500'
  if (theme === 'enterprise') return typeColors.value.label
  return ''
})

const labelColorClass = computed(() => typeColors.value.label)

const progressColor = computed(() => {
  if (uiStore.toastTheme === 'minimal') return 'bg-gray-300 dark:bg-gray-600'
  switch (props.toast.type) {
    case 'success': return 'bg-green-400'
    case 'error': return 'bg-red-400'
    case 'warning': return 'bg-amber-400'
    default: return 'bg-blue-400'
  }
})
</script>
