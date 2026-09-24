<template>
  <div class="relative" ref="containerRef">
    <button
      class="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:bg-gray-700"
      :aria-label="t('organizations.switcher')"
      @click="open = !open"
    >
      <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
        />
      </svg>
      <span class="hidden max-w-[120px] truncate font-medium text-gray-700 dark:text-gray-300 sm:inline">
        {{ currentOrgName }}
      </span>
      <span
        v-if="store.currentWorkspace"
        class="hidden max-w-[100px] truncate text-xs text-gray-400 md:inline"
      >
        / {{ store.currentWorkspace.name }}
      </span>
      <svg
        class="h-3.5 w-3.5 text-gray-400 transition-transform"
        :class="{ 'rotate-180': open }"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
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
          class="fixed top-12 right-4 z-50 w-80 rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900"
        >
          <div class="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
              {{ t('organizations.switcher') }}
            </h3>
            <p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              {{ t('organizations.hierarchyHint') }}
            </p>
          </div>

          <div class="max-h-80 overflow-y-auto p-2">
            <div v-if="store.loading" class="px-3 py-4 text-center text-sm text-gray-500">
              {{ t('common.loading') }}
            </div>
            <div v-else-if="!store.organizations.length" class="px-3 py-4 text-center text-sm text-gray-500">
              {{ t('organizations.empty') }}
            </div>
            <template v-else>
              <div
                v-for="org in store.organizations"
                :key="org.id"
                class="mb-1"
              >
                <button
                  class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors"
                  :class="
                    org.id === store.currentOrgId
                      ? 'bg-blue-50 dark:bg-blue-900/20'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                  "
                  @click="selectOrg(org.id)"
                >
                  <div
                    class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-xs font-bold text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300"
                  >
                    {{ org.name.slice(0, 2).toUpperCase() }}
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="text-sm font-medium text-gray-900 dark:text-white">
                      {{ org.name }}
                    </div>
                    <div class="truncate text-xs text-gray-500 dark:text-gray-400">
                      {{ org.plan }} · {{ org.workspaces.length }} {{ t('organizations.workspaces') }}
                    </div>
                  </div>
                  <svg
                    v-if="org.id === store.currentOrgId"
                    class="h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </button>

                <div
                  v-if="org.id === store.currentOrgId && org.workspaces.length"
                  class="ml-6 mt-1 space-y-0.5 border-l border-gray-200 pl-2 dark:border-gray-700"
                >
                  <button
                    v-for="ws in org.workspaces"
                    :key="ws.id"
                    class="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-xs transition-colors"
                    :class="
                      ws.id === store.currentWorkspaceId
                        ? 'bg-indigo-50 font-medium text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                        : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-800'
                    "
                    @click="selectWorkspace(ws.id)"
                  >
                    <span class="truncate">{{ ws.name }}</span>
                    <span class="ml-2 shrink-0 text-[10px] text-gray-400">{{ ws.department }}</span>
                  </button>
                </div>
              </div>
            </template>
          </div>

          <div class="border-t border-gray-200 px-3 py-2 dark:border-gray-700">
            <button
              class="w-full rounded-lg px-2 py-1.5 text-left text-xs font-medium text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20"
              @click="goSettings"
            >
              {{ t('organizations.manage') }}
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useOrganizationsStore } from '@/stores/organizationsStore'

const { t } = useI18n()
const router = useRouter()
const store = useOrganizationsStore()

const open = ref(false)
const containerRef = ref<HTMLElement | null>(null)

const currentOrgName = computed(() => store.currentOrg?.name || t('organizations.none'))

function selectOrg(id: string) {
  store.setOrg(id)
}

function selectWorkspace(id: string) {
  store.setWorkspace(id)
}

function goSettings() {
  open.value = false
  router.push('/organization')
}

function handleClickOutside(e: MouseEvent) {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    open.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  store.fetchOrganizations()
})

onUnmounted(() => document.removeEventListener('click', handleClickOutside))

watch(
  () => store.currentOrgId,
  () => {
    // keep project selection aligned when org changes
  },
)
</script>
