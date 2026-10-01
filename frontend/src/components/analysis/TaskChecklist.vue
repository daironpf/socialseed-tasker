<template>
  <div class="task-checklist">
    <p v-if="total > 0" class="mb-2 text-xs font-medium text-gray-500 dark:text-gray-400">
      {{ t('issues.checklistProgress', { done, total }) }}
    </p>
    <MarkdownRenderer :content="content" interactive :checked="overrides" @toggle="onToggle" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import MarkdownRenderer from '@/components/analysis/MarkdownRenderer.vue'
import { isChecklistItemChecked, parseChecklistItems } from '@/utils/checklist'

const { t } = useI18n()

const props = defineProps<{
  content: string
  checked?: Record<string, boolean>
}>()

const emit = defineEmits<{ toggle: [key: string, checked: boolean] }>()

const overrides = computed(() => props.checked ?? {})
const items = computed(() => parseChecklistItems(props.content))
const total = computed(() => items.value.length)
const done = computed(() => items.value.filter((item) => isChecklistItemChecked(item, overrides.value)).length)

function onToggle(key: string, checked: boolean) {
  emit('toggle', key, checked)
}
</script>
