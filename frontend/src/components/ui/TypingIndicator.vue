<template>
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0 -translate-y-1"
    enter-to-class="opacity-100 translate-y-0"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100 translate-y-0"
    leave-to-class="opacity-0 -translate-y-1"
  >
    <div
      v-if="agents.length > 0"
      class="flex items-center gap-2 rounded-lg border border-purple-200 bg-purple-50 px-3 py-2 dark:border-purple-800 dark:bg-purple-900/20"
    >
      <div class="flex gap-1">
        <span class="h-1.5 w-1.5 rounded-full bg-purple-500 animate-bounce" style="animation-delay: 0ms"></span>
        <span class="h-1.5 w-1.5 rounded-full bg-purple-500 animate-bounce" style="animation-delay: 150ms"></span>
        <span class="h-1.5 w-1.5 rounded-full bg-purple-500 animate-bounce" style="animation-delay: 300ms"></span>
      </div>
      <span class="text-xs text-purple-700 dark:text-purple-300">
        <template v-if="agents.length === 1">
          {{ agents[0].avatar }} <span class="font-medium">{{ agents[0].username }}</span>
          {{ agents[0].typingMessage || t('presence.isWorking') }}
        </template>
        <template v-else>
          {{ agents.length }} {{ t('presence.agentsWorking') }}
        </template>
      </span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { PresenceUser } from '@/composables/usePresence'

defineProps<{
  agents: PresenceUser[]
}>()

const { t } = useI18n()
</script>
