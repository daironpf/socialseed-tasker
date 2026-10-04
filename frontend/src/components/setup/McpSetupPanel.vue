<template>
  <section data-testid="setup-ai-panel">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
      {{ t('setup.ai.heading') }}
    </h2>
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
      {{ t('setup.ai.description') }}
    </p>

    <div class="mt-4">
      <span class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
        {{ t('setup.ai.keyLabel') }}
      </span>
      <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <code
          class="min-w-0 flex-1 break-all rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
          data-testid="setup-ai-key"
        >{{ apiKey }}</code>
        <button
          type="button"
          data-testid="setup-copy-key"
          class="flex-shrink-0 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          :aria-pressed="copiedKey"
          @click="copyKey"
        >
          {{ copiedKey ? t('setup.ai.copiedKey') : t('setup.ai.copyKey') }}
        </button>
      </div>
      <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
        {{ t('setup.ai.keyHint') }}
      </p>
    </div>

    <div class="mt-4">
      <label for="setup-panel-mcp-port" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
        {{ t('setup.ai.portLabel') }}
      </label>
      <input
        id="setup-panel-mcp-port"
        v-model="portDraft"
        type="number"
        min="0"
        max="65535"
        data-testid="setup-panel-mcp-port"
        :placeholder="t('setup.ai.portPlaceholder')"
        :aria-label="t('setup.ai.portLabel')"
        class="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 sm:w-48"
      />
      <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
        {{ t('setup.ai.portHint') }}
      </p>
    </div>

    <div class="mt-5">
      <div class="flex items-center justify-between gap-3">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
          {{ t('setup.ai.snippetTitle') }}
        </h3>
        <button
          type="button"
          data-testid="setup-copy-snippet"
          class="flex-shrink-0 rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          :aria-pressed="copiedSnippet"
          @click="copySnippet"
        >
          {{ copiedSnippet ? t('setup.ai.copiedSnippet') : t('setup.ai.copySnippet') }}
        </button>
      </div>
      <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
        {{ t('setup.ai.snippetHint') }}
      </p>
      <pre
        data-testid="setup-mcp-snippet"
        class="mt-2 max-h-64 overflow-auto rounded-lg border border-gray-200 bg-gray-950 p-3 text-xs leading-relaxed text-gray-100 dark:border-gray-700"
      ><code>{{ snippet }}</code></pre>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  apiKey: string
  mcpPort: number
}>()

const { t } = useI18n()

const portDraft = ref(props.mcpPort > 0 ? String(props.mcpPort) : '')
const copiedKey = ref(false)
const copiedSnippet = ref(false)

watch(
  () => props.mcpPort,
  (value) => {
    portDraft.value = value > 0 ? String(value) : ''
  },
)

const snippet = computed(() => {
  const env = import.meta.env
  const apiBase =
    (window as unknown as { __API_URL__?: string }).__API_URL__ ||
    env.VITE_API_URL ||
    '/api/v1'
  const base = new URL(apiBase, window.location.origin)
  const port = String(portDraft.value).trim()
  const host = port ? `${base.hostname}:${port}` : base.host
  const url = `${base.protocol}//${host}/mcp`
  return JSON.stringify(
    {
      mcpServers: {
        tasker: {
          url,
          headers: { 'X-API-Key': props.apiKey },
        },
      },
    },
    null,
    2,
  )
})

async function copyText(text: string, done: { value: boolean }): Promise<void> {
  try {
    await navigator.clipboard.writeText(text)
    done.value = true
    window.setTimeout(() => {
      done.value = false
    }, 2000)
  } catch {
    done.value = false
  }
}

function copyKey() {
  void copyText(props.apiKey, copiedKey)
}

function copySnippet() {
  void copyText(snippet.value, copiedSnippet)
}
</script>
