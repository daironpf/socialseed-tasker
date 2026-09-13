<template>
  <div v-if="viewers.length > 0" class="flex items-center gap-2">
    <div class="flex -space-x-2">
      <div
        v-for="viewer in viewers"
        :key="viewer.id"
        class="relative group"
      >
        <div
          class="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white text-sm dark:border-gray-800 transition-transform hover:scale-110 hover:z-10"
          :class="viewer.type === 'agent' ? 'bg-purple-100 dark:bg-purple-900/40' : 'bg-blue-100 dark:bg-blue-900/40'"
        >
          {{ viewer.avatar }}
        </div>
        <span class="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white dark:border-gray-800 bg-green-400"></span>

        <!-- Tooltip -->
        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-20">
          <div class="rounded-lg bg-gray-900 dark:bg-gray-700 px-3 py-1.5 text-xs text-white whitespace-nowrap shadow-lg">
            <div class="font-medium">{{ viewer.username }}</div>
            <div v-if="viewer.viewingField" class="text-gray-400 text-[10px]">
              {{ t('presence.editing', { field: viewer.viewingField }) }}
            </div>
            <div class="text-gray-400 text-[10px]">{{ timeAgo(viewer.lastSeen) }}</div>
          </div>
        </div>
      </div>
    </div>

    <span v-if="viewers.length === 1" class="text-xs text-gray-500 dark:text-gray-400">
      {{ viewers[0].username }} {{ t('presence.isViewing') }}
    </span>
    <span v-else class="text-xs text-gray-500 dark:text-gray-400">
      {{ viewers.length }} {{ t('presence.viewing') }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { PresenceUser } from '@/composables/usePresence'

defineProps<{
  viewers: PresenceUser[]
}>()

const { t } = useI18n()

function timeAgo(ts: number): string {
  const diff = Date.now() - ts
  const secs = Math.floor(diff / 1000)
  if (secs < 10) return t('presence.justNow')
  if (secs < 60) return t('presence.secondsAgo', { n: secs })
  const mins = Math.floor(secs / 60)
  return t('presence.minutesAgo', { n: mins })
}
</script>
