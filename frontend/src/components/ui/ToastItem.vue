<template>
  <div
    class="pointer-events-auto flex items-start gap-3 rounded-lg border p-4 shadow-lg transition-all"
    :class="variantClasses"
    role="alert"
  >
    <div class="shrink-0 mt-0.5">
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

    <p class="flex-1 text-sm font-medium">{{ toast.message }}</p>

    <button
      class="shrink-0 rounded p-0.5 opacity-60 hover:opacity-100 transition-opacity"
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
      class="absolute bottom-0 left-0 h-0.5 rounded-b-lg transition-all"
      :class="progressColor"
      :style="{ width: progressWidth + '%' }"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Toast } from '@/composables/useToast'

const { t } = useI18n()

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
  return () => cancelAnimationFrame(raf)
})

const progressWidth = computed(() => {
  if (props.toast.persistent) return 100
  return Math.min((elapsed.value / props.toast.duration) * 100, 100)
})

const variantClasses = computed(() => {
  const base = 'relative overflow-hidden '
  switch (props.toast.type) {
    case 'success': return base + 'border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-900/30 dark:text-green-300'
    case 'error': return base + 'border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300'
    case 'warning': return base + 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300'
    default: return base + 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
  }
})

const progressColor = computed(() => {
  switch (props.toast.type) {
    case 'success': return 'bg-green-400'
    case 'error': return 'bg-red-400'
    case 'warning': return 'bg-amber-400'
    default: return 'bg-blue-400'
  }
})
</script>
