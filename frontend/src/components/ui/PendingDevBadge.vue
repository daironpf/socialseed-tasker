<template>
  <span
    class="pending-dev-badge inline-flex flex-shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600 dark:bg-amber-900/60 dark:text-amber-400"
    :class="size === 'sm' ? 'h-5 w-5' : 'h-4 w-4'"
    role="img"
    :title="label"
    :aria-label="label"
  >
    <svg
      :class="size === 'sm' ? 'h-3.5 w-3.5' : 'h-2.5 w-2.5'"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      stroke-width="2.2"
      aria-hidden="true"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        d="M5 22h14M5 2h14M17 22v-4.172a2 2 0 00-.586-1.414L12 12l-4.414 4.414A2 2 0 007 17.828V22M7 2v4.172a2 2 0 00.586 1.414L12 12l4.414-4.414A2 2 0 0017 6.172V2"
      />
    </svg>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

withDefaults(defineProps<{ size?: 'xs' | 'sm' }>(), { size: 'xs' })

const { t } = useI18n()
const label = computed(() => t('common.pendingDev'))
</script>
