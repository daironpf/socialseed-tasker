<template>
  <div
    v-if="payload"
    class="fixed inset-0 z-40 flex justify-end bg-black/50"
    role="dialog"
    aria-modal="true"
    @click.self="$emit('close')"
  >
    <div class="h-full w-full max-w-md overflow-y-auto bg-white shadow-2xl dark:bg-gray-800">
      <header class="sticky top-0 z-10 border-b border-gray-200 bg-white px-6 py-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="mb-1 flex items-center gap-2">
              <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-bold uppercase text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                {{ typeLabel }}
              </span>
              <span
                v-if="payload.badge"
                class="rounded-full px-2 py-0.5 text-[10px] font-bold"
                :class="badgeClass"
              >
                {{ payload.badge }}
              </span>
            </div>
            <h2 class="truncate text-lg font-semibold text-gray-900 dark:text-white">
              {{ payload.title }}
            </h2>
            <p v-if="payload.subtitle" class="truncate text-xs text-gray-500 dark:text-gray-400">
              {{ payload.subtitle }}
            </p>
          </div>
          <button
            class="rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
            :aria-label="t('common.close')"
            @click="$emit('close')"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </header>

      <div class="space-y-5 p-6">
        <!-- Edge details -->
        <section v-if="payload.edge">
          <h3 class="mb-2 text-xs font-semibold uppercase text-gray-400">
            {{ t('graphExplorer.inspector.relationship') }}
          </h3>
          <div class="space-y-2 rounded-lg bg-gray-50 p-3 text-sm dark:bg-gray-900/40">
            <div class="flex justify-between gap-3">
              <span class="text-gray-500 dark:text-gray-400">{{ t('graphExplorer.inspector.relation') }}</span>
              <span class="font-medium text-gray-800 dark:text-gray-200">
                {{ t(`graphExplorer.relations.${payload.edge.relation}`) }}
              </span>
            </div>
            <div class="flex justify-between gap-3">
              <span class="text-gray-500 dark:text-gray-400">{{ t('graphExplorer.inspector.direction') }}</span>
              <span class="truncate font-medium text-gray-800 dark:text-gray-200">
                {{ payload.edge.fromLabel }} → {{ payload.edge.toLabel }}
              </span>
            </div>
            <div class="flex justify-between gap-3">
              <span class="text-gray-500 dark:text-gray-400">{{ t('graphExplorer.inspector.weight') }}</span>
              <span class="font-medium text-gray-800 dark:text-gray-200">{{ payload.edge.weight }}</span>
            </div>
            <div class="flex justify-between gap-3">
              <span class="text-gray-500 dark:text-gray-400">{{ t('graphExplorer.inspector.cycle') }}</span>
              <span
                class="font-medium"
                :class="payload.edge.inCycle ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'"
              >
                {{ payload.edge.inCycle ? t('graphExplorer.inspector.cycleYes') : t('graphExplorer.inspector.cycleNo') }}
              </span>
            </div>
          </div>
        </section>

        <!-- Metadata -->
        <section v-if="payload.fields.length">
          <h3 class="mb-2 text-xs font-semibold uppercase text-gray-400">
            {{ t('graphExplorer.inspector.metadata') }}
          </h3>
          <dl class="space-y-2">
            <div v-for="field in payload.fields" :key="field.label" class="flex justify-between gap-3 text-sm">
              <dt class="shrink-0 text-gray-500 dark:text-gray-400">{{ field.label }}</dt>
              <dd class="truncate text-right font-medium text-gray-800 dark:text-gray-200" :title="field.value">
                {{ field.value }}
              </dd>
            </div>
          </dl>
        </section>

        <!-- Blast radius -->
        <section v-if="payload.blast">
          <h3 class="mb-2 text-xs font-semibold uppercase text-gray-400">
            {{ t('graphExplorer.inspector.blastRadius') }}
          </h3>
          <div class="grid grid-cols-3 gap-2">
            <div class="rounded-lg bg-gray-50 p-2 text-center dark:bg-gray-900/40">
              <div class="text-sm font-bold text-gray-900 dark:text-white">{{ payload.blast.total }}</div>
              <div class="text-[10px] uppercase text-gray-500">{{ t('graphExplorer.inspector.total') }}</div>
            </div>
            <div class="rounded-lg bg-gray-50 p-2 text-center dark:bg-gray-900/40">
              <div class="text-sm font-bold text-gray-900 dark:text-white">{{ payload.blast.direct }}</div>
              <div class="text-[10px] uppercase text-gray-500">{{ t('graphExplorer.inspector.direct') }}</div>
            </div>
            <div class="rounded-lg bg-gray-50 p-2 text-center dark:bg-gray-900/40">
              <div class="text-sm font-bold text-gray-900 dark:text-white">{{ payload.blast.maxDepth }}</div>
              <div class="text-[10px] uppercase text-gray-500">{{ t('graphExplorer.inspector.depth') }}</div>
            </div>
            <div class="rounded-lg bg-red-50 p-2 text-center dark:bg-red-900/20">
              <div class="text-sm font-bold text-red-600 dark:text-red-400">{{ payload.blast.critical }}</div>
              <div class="text-[10px] uppercase text-red-500">{{ t('issues.critical') }}</div>
            </div>
            <div class="rounded-lg bg-amber-50 p-2 text-center dark:bg-amber-900/20">
              <div class="text-sm font-bold text-amber-600 dark:text-amber-400">{{ payload.blast.high }}</div>
              <div class="text-[10px] uppercase text-amber-500">{{ t('issues.high') }}</div>
            </div>
          </div>
        </section>

        <!-- Quick links -->
        <section v-if="payload.links.length">
          <h3 class="mb-2 text-xs font-semibold uppercase text-gray-400">
            {{ t('graphExplorer.inspector.links') }}
          </h3>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="link in payload.links"
              :key="link.label"
              class="flex min-h-[36px] items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              @click="$emit('action', link)"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              {{ link.label }}
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { InspectorPayload, InspectorLink } from '@/types/graphExplorer'

const props = defineProps<{
  payload: InspectorPayload | null
}>()

defineEmits<{
  close: []
  action: [link: InspectorLink]
}>()

const { t } = useI18n()

const typeLabel = computed(() => {
  if (!props.payload) return ''
  const key = `graphExplorer.types.${props.payload.type}`
  const translated = t(key)
  return translated === key ? props.payload.type : translated
})

const badgeClass = computed(() => {
  const badge = props.payload?.badge || ''
  if (badge === 'CRITICAL') return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
  if (badge === 'HIGH') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
  if (badge === 'MEDIUM') return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300'
  if (badge === 'LOW') return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
  return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
})
</script>
