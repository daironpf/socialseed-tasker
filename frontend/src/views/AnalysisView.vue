<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('analysis.title') }}</h1>
    </div>

    <div class="border-b border-gray-200 dark:border-gray-700">
      <nav class="-mb-px flex gap-6">
        <button
          class="border-b-2 px-1 py-3 text-sm font-medium transition-colors"
          :class="activeTab === 'impact'
            ? 'border-blue-500 text-blue-600 dark:text-blue-400'
            : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'"
          @click="activeTab = 'impact'"
        >
          {{ t('analysis.impactAnalysis') }}
        </button>
        <button
          class="border-b-2 px-1 py-3 text-sm font-medium transition-colors"
          :class="activeTab === 'rootcause'
            ? 'border-purple-500 text-purple-600 dark:text-purple-400'
            : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'"
          @click="activeTab = 'rootcause'"
        >
          {{ t('analysis.rootCause') }}
        </button>
      </nav>
    </div>

    <div v-if="activeTab === 'impact'">
      <ImpactAnalysisPanel />
    </div>
    <div v-else>
      <RootCausePanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ImpactAnalysisPanel from '@/components/analysis/ImpactAnalysisPanel.vue'
import RootCausePanel from '@/components/analysis/RootCausePanel.vue'

const { t } = useI18n()

const activeTab = ref<'impact' | 'rootcause'>('impact')
</script>
