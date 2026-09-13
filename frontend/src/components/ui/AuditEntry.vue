<template>
  <div class="group flex gap-3 relative">
    <!-- Timeline line -->
    <div class="absolute left-5 top-10 bottom-0 w-px bg-gray-200 dark:bg-gray-700"></div>

    <!-- Avatar -->
    <div
      class="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm border-2 border-white dark:border-gray-800"
      :class="avatarClasses"
    >
      <template v-if="entry.actorType === 'system'">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </template>
      <template v-else>
        {{ entry.actorAvatar }}
      </template>
    </div>

    <!-- Content -->
    <div class="min-w-0 flex-1 pb-6">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="font-medium text-sm text-gray-900 dark:text-white">{{ entry.actor }}</span>
        <span
          class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold"
          :class="actionClasses"
        >{{ actionLabel }}</span>
      </div>
      <p class="mt-0.5 text-sm text-gray-600 dark:text-gray-400">{{ entry.description }}</p>
      <div v-if="entry.details" class="mt-1 text-xs text-gray-500 dark:text-gray-500">
        <template v-if="entry.details.from && entry.details.to">
          <span class="line-through opacity-60">{{ entry.details.from }}</span>
          <span class="mx-1">→</span>
          <span class="font-medium">{{ entry.details.to }}</span>
        </template>
      </div>
      <span class="mt-1 block text-[11px] text-gray-400 dark:text-gray-500">{{ timeAgo }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ACTION_CONFIG, type AuditEntry } from '@/types/audit'

const { t } = useI18n()

const props = defineProps<{
  entry: AuditEntry
}>()

const avatarClasses = computed(() => {
  if (props.entry.actorType === 'agent') return 'bg-purple-100 dark:bg-purple-900/40'
  if (props.entry.actorType === 'system') return 'bg-gray-100 dark:bg-gray-700 text-gray-500'
  return 'bg-blue-100 dark:bg-blue-900/40'
})

const config = computed(() => ACTION_CONFIG[props.entry.action])

const actionClasses = computed(() => config.value.bg + ' ' + config.value.color)

const actionLabel = computed(() => {
  const key = `audit.actions.${props.entry.action}`
  return t(key)
})

const timeAgo = computed(() => {
  const diff = Date.now() - new Date(props.entry.timestamp).getTime()
  const secs = Math.floor(diff / 1000)
  if (secs < 60) return t('audit.justNow')
  const mins = Math.floor(secs / 60)
  if (mins < 60) return t('audit.minutesAgo', { n: mins })
  const hours = Math.floor(mins / 60)
  if (hours < 24) return t('audit.hoursAgo', { n: hours })
  const days = Math.floor(hours / 24)
  if (days < 7) return t('audit.daysAgo', { n: days })
  return new Date(props.entry.timestamp).toLocaleDateString()
})
</script>
