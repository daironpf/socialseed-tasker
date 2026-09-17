<template>
  <div class="flex items-center gap-3 flex-wrap">
    <!-- Component Multi-Select -->
    <div class="relative" ref="dropdownRef">
      <button
        class="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:bg-gray-700"
        @click="open = !open"
      >
        <svg class="h-3.5 w-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        {{ selectedCount > 0 ? t('graph.componentsSelected', { n: selectedCount }) : t('graph.allComponents') }}
        <svg class="h-3.5 w-3.5 text-gray-400 transition-transform" :class="{ 'rotate-180': open }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <Teleport to="body">
        <Transition
          enter-active-class="transition duration-150 ease-out"
          enter-from-class="scale-95 opacity-0"
          enter-to-class="scale-100 opacity-100"
          leave-active-class="transition duration-100 ease-in"
          leave-from-class="scale-100 opacity-100"
          leave-to-class="scale-95 opacity-0"
        >
          <div
            v-if="open"
            class="fixed z-50 w-56 rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900"
            :style="{ top: dropdownPos.top, left: dropdownPos.left }"
          >
            <div class="border-b border-gray-200 px-3 py-2 dark:border-gray-700">
              <div class="flex items-center justify-between">
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ t('graph.filterComponents') }}</span>
                <button
                  v-if="selectedComponents.length > 0"
                  class="text-[10px] text-blue-600 hover:text-blue-700 dark:text-blue-400"
                  @click="$emit('update:selectedComponents', [])"
                >{{ t('graph.clearAll') }}</button>
              </div>
            </div>
            <div class="max-h-48 overflow-y-auto p-1">
              <label
                v-for="comp in components"
                :key="comp.id"
                class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <input
                  type="checkbox"
                  :checked="selectedComponents.includes(comp.id)"
                  class="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                  @change="toggleComponent(comp.id)"
                />
                <span class="text-gray-700 dark:text-gray-300">{{ comp.name }}</span>
              </label>
            </div>
          </div>
        </Transition>
      </Teleport>
    </div>

    <!-- Max Hops Slider -->
    <div class="flex items-center gap-2">
      <label class="text-xs text-gray-500 dark:text-gray-400">{{ t('graph.maxHops') }}</label>
      <input
        :value="maxHops"
        type="range"
        min="1"
        max="5"
        class="h-1.5 w-20 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 accent-blue-600"
        @input="$emit('update:maxHops', Number(($event.target as HTMLInputElement).value))"
      />
      <span class="text-xs font-mono text-gray-700 dark:text-gray-300 w-4">{{ maxHops }}</span>
    </div>

    <!-- Reset -->
    <button
      v-if="selectedComponents.length > 0 || maxHops !== 3"
      class="flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 transition-colors"
      @click="$emit('update:selectedComponents', []); $emit('update:maxHops', 3)"
    >
      <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      {{ t('graph.reset') }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  components: Array<{ id: string; name: string }>
  selectedComponents: string[]
  maxHops: number
}>()

const emit = defineEmits<{
  'update:selectedComponents': [value: string[]]
  'update:maxHops': [value: number]
}>()

const open = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const selectedCount = computed(() => props.selectedComponents.length)

const dropdownPos = computed(() => ({
  top: '40px',
  left: '0px',
}))

function toggleComponent(id: string) {
  const current = [...props.selectedComponents]
  const idx = current.indexOf(id)
  if (idx >= 0) current.splice(idx, 1)
  else current.push(id)
  emit('update:selectedComponents', current)
}

function handleClickOutside(e: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>
