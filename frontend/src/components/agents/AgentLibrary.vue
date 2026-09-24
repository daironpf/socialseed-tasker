<template>
  <div>
    <div class="mb-3 flex items-center gap-2">
      <h2 class="text-sm font-semibold text-gray-800 dark:text-gray-200">{{ t('agentStudio.library.title') }}</h2>
      <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-bold text-gray-500 dark:bg-gray-700 dark:text-gray-300">
        {{ profiles.length }}
      </span>
    </div>

    <div v-if="!profiles.length" class="rounded-xl border border-dashed border-gray-300 p-8 text-center text-sm text-gray-400 dark:border-gray-600">
      {{ t('agentStudio.library.empty') }}
    </div>

    <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <div
        v-for="profile in profiles"
        :key="profile.id"
        class="flex flex-col rounded-xl border bg-white p-4 transition-shadow hover:shadow-md dark:bg-gray-800"
        :class="profile.enabled
          ? 'border-emerald-300 dark:border-emerald-700'
          : 'border-gray-200 opacity-75 dark:border-gray-700'"
      >
        <div class="flex items-start gap-3">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gray-100 text-xl dark:bg-gray-700">
            {{ profile.avatar }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-1.5">
              <span class="truncate text-sm font-semibold text-gray-900 dark:text-white">{{ profile.name }}</span>
              <span
                class="rounded-full px-1.5 py-0.5 text-[9px] font-bold"
                :class="profile.enabled
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
                  : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'"
              >
                {{ profile.enabled ? t('agentStudio.library.active') : t('agentStudio.library.inactive') }}
              </span>
            </div>
            <div class="truncate text-[11px] text-gray-500 dark:text-gray-400">{{ profile.role }} · {{ profile.model }}</div>
          </div>
          <label class="flex cursor-pointer items-center" :title="t('agentStudio.library.toggle')">
            <input
              type="checkbox"
              class="peer sr-only"
              :checked="profile.enabled"
              @change="$emit('toggle', profile.id)"
            >
            <div class="h-5 w-9 rounded-full bg-gray-300 transition-colors peer-checked:bg-emerald-500 dark:bg-gray-600" />
            <div class="-ml-8 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-4" />
          </label>
        </div>

        <div class="mt-3 flex flex-wrap gap-1">
          <span
            v-for="tool in profile.tools.slice(0, 4)"
            :key="tool"
            class="rounded bg-sky-50 px-1.5 py-0.5 font-mono text-[9px] text-sky-700 dark:bg-sky-900/30 dark:text-sky-300"
          >
            {{ tool }}
          </span>
          <span v-if="profile.tools.length > 4" class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[9px] text-gray-500 dark:bg-gray-700 dark:text-gray-400">
            +{{ profile.tools.length - 4 }}
          </span>
          <span v-if="!profile.tools.length" class="text-[9px] text-gray-400">{{ t('agentStudio.library.noTools') }}</span>
        </div>

        <div class="mt-3 grid grid-cols-3 gap-1.5 border-t border-gray-100 pt-2.5 text-center dark:border-gray-700/60">
          <div>
            <div class="text-[11px] font-bold text-gray-700 dark:text-gray-300">{{ formatTokens(profile.limits.maxTokensPerRun) }}</div>
            <div class="text-[8px] uppercase text-gray-400">{{ t('agentStudio.library.tokens') }}</div>
          </div>
          <div>
            <div class="text-[11px] font-bold text-gray-700 dark:text-gray-300">{{ profile.limits.timeoutSeconds }}s</div>
            <div class="text-[8px] uppercase text-gray-400">{{ t('agentStudio.library.timeout') }}</div>
          </div>
          <div>
            <div class="text-[11px] font-bold" :class="riskClass(profile.limits.maxRisk)">{{ profile.limits.maxRisk }}</div>
            <div class="text-[8px] uppercase text-gray-400">{{ t('agentStudio.library.risk') }}</div>
          </div>
        </div>

        <div class="mt-2 text-[9px] text-gray-400">
          {{ t('agentStudio.library.lastUsed') }}: {{ profile.lastUsedAt ? formatDate(profile.lastUsedAt) : t('agentStudio.library.never') }}
        </div>

        <div class="mt-3 flex gap-1.5">
          <button
            class="flex-1 rounded-lg bg-gray-900 px-2 py-1.5 text-[11px] font-medium text-white hover:bg-gray-700 dark:bg-gray-600 dark:hover:bg-gray-500"
            @click="$emit('edit', profile.id)"
          >
            {{ t('agentStudio.library.edit') }}
          </button>
          <button
            class="rounded-lg border border-gray-300 px-2 py-1.5 text-[11px] font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="$emit('clone', profile.id)"
          >
            {{ t('agentStudio.library.clone') }}
          </button>
          <button
            class="rounded-lg border border-red-200 px-2 py-1.5 text-[11px] font-medium text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-900/20"
            @click="$emit('remove', profile.id)"
          >
            {{ t('common.delete') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { AgentProfile } from '@/types/agentStudio'

defineProps<{
  profiles: AgentProfile[]
}>()

defineEmits<{
  edit: [id: string]
  clone: [id: string]
  toggle: [id: string]
  remove: [id: string]
}>()

const { t, d } = useI18n()

function formatTokens(value: number): string {
  return value >= 1000 ? `${Math.round(value / 1000)}k` : String(value)
}

function riskClass(risk: string): string {
  if (risk === 'HIGH') return 'text-red-600 dark:text-red-400'
  if (risk === 'MEDIUM') return 'text-amber-600 dark:text-amber-400'
  return 'text-emerald-600 dark:text-emerald-400'
}

function formatDate(iso: string): string {
  try {
    return d(new Date(iso), 'short')
  } catch {
    return iso.slice(0, 10)
  }
}
</script>
