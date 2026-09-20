<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('sandbox.title') }}</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('sandbox.subtitle') }}</p>
      </div>
      <button class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700" @click="openCreateModal">
        {{ t('sandbox.newRule') }}
      </button>
    </div>

    <div class="grid grid-cols-5 gap-4">
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ store.metrics.totalRules }}</div>
        <div class="text-xs text-gray-500">{{ t('sandbox.totalRules') }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-amber-600 dark:text-amber-400">{{ store.metrics.draftRules }}</div>
        <div class="text-xs text-gray-500">{{ t('sandbox.drafts') }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ store.metrics.activeRules }}</div>
        <div class="text-xs text-gray-500">{{ t('sandbox.active') }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ store.metrics.totalSimulations }}</div>
        <div class="text-xs text-gray-500">{{ t('sandbox.simulations') }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">{{ store.latestSimulation ? store.latestSimulation.violatingEdges : 0 }}</div>
        <div class="text-xs text-gray-500">{{ t('sandbox.latestViolations') }}</div>
      </div>
    </div>

    <div class="flex flex-wrap gap-3">
      <div class="relative flex-1 min-w-[200px]">
        <svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
        <input v-model="search" type="text" :placeholder="t('sandbox.search')" :aria-label="t('sandbox.search')" class="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800" />
      </div>
      <select v-model="filterStatus" :aria-label="t('sandbox.allStatus')" class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800">
        <option value="">{{ t('sandbox.allStatus') }}</option>
        <option value="draft">{{ t('sandbox.drafts') }}</option>
        <option value="active">{{ t('sandbox.active') }}</option>
      </select>
      <select v-model="filterFormat" :aria-label="t('sandbox.allFormats')" class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800">
        <option value="">{{ t('sandbox.allFormats') }}</option>
        <option value="cypher">Cypher</option>
        <option value="yaml">YAML</option>
      </select>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700">
        <div class="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('sandbox.rulesList') }}</h3>
        </div>
        <div class="max-h-[600px] overflow-y-auto divide-y divide-gray-100 dark:divide-gray-700/50">
          <div v-for="rule in filteredRules" :key="rule.id" class="cursor-pointer px-4 py-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50" :class="activeRule?.id === rule.id ? 'bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-500' : ''" @click="selectRule(rule)">
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ rule.name }}</span>
                  <span class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold" :class="rule.isDraft ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'">{{ rule.isDraft ? t('sandbox.draft') : t('sandbox.activeLabel') }}</span>
                  <span class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">{{ rule.format.toUpperCase() }}</span>
                  <span class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold" :class="rule.severity === 'HARD' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'">{{ rule.severity }}</span>
                </div>
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400 truncate">{{ rule.description }}</p>
                <div class="mt-1 flex items-center gap-3 text-[10px] text-gray-400"><span>{{ rule.category }}</span><span>{{ rule.scope }}</span></div>
              </div>
              <div class="flex items-center gap-1 ml-2">
                <button class="rounded p-1 text-gray-400 hover:bg-gray-200 hover:text-blue-600 dark:hover:bg-gray-700" :aria-label="t('sandbox.simulate')" :disabled="store.loading" @click.stop="simulateRule(rule)">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </button>
                <button class="rounded p-1 text-gray-400 hover:bg-gray-200 hover:text-green-600 dark:hover:bg-gray-700" :aria-label="t('sandbox.edit')" @click.stop="openEditModal(rule)">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                </button>
                <button class="rounded p-1 text-gray-400 hover:bg-gray-200 hover:text-red-600 dark:hover:bg-gray-700" :aria-label="t('sandbox.delete')" @click.stop="confirmDelete(rule)">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>
            </div>
          </div>
          <div v-if="filteredRules.length === 0" class="px-4 py-12 text-center text-sm text-gray-400">{{ t('sandbox.noRules') }}</div>
        </div>
      </div>

      <div class="space-y-4">
        <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700">
          <div class="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ activeRule ? t('sandbox.editor') + ' — ' + activeRule.name : t('sandbox.editor') }}</h3>
            <div v-if="activeRule" class="flex items-center gap-2">
              <span class="text-xs text-gray-500">{{ t('sandbox.format') }}:</span>
              <select v-model="editorFormat" class="rounded border border-gray-300 px-2 py-1 text-xs dark:border-gray-600 dark:bg-gray-700"><option value="cypher">Cypher</option><option value="yaml">YAML</option></select>
            </div>
          </div>
          <div class="p-4">
            <textarea v-model="editorCode" :placeholder="t('sandbox.editorPlaceholder')" :disabled="!activeRule" rows="14" class="w-full rounded-lg border border-gray-300 bg-gray-50 px-4 py-3 font-mono text-sm text-gray-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-200" spellcheck="false" />
          </div>
          <div class="flex items-center justify-between border-t border-gray-200 px-4 py-3 dark:border-gray-700">
            <div class="text-xs text-gray-500"><span v-if="activeRule">{{ lineCount }} lines</span></div>
            <div class="flex gap-2">
              <button v-if="activeRule" class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700" @click="saveRule" :disabled="store.loading">{{ t('sandbox.saveDraft') }}</button>
              <button v-if="activeRule" class="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50" @click="simulateRule(activeRule)" :disabled="store.loading || !editorCode.trim()">
                <span v-if="store.loading" class="flex items-center gap-1"><span class="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"></span>{{ t('sandbox.running') }}</span>
                <span v-else>{{ t('sandbox.simulate') }}</span>
              </button>
            </div>
          </div>
        </div>

        <ImpactReport v-if="store.currentSimulation" :simulation="store.currentSimulation" :can-promote="!!activeRule?.isDraft" @promote="promoteRule" />
      </div>
    </div>

    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="closeModal" role="dialog" aria-modal="true">
      <div class="w-full max-w-lg rounded-xl bg-white p-6 shadow-2xl dark:bg-gray-800">
        <h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">{{ editingRule ? t('sandbox.edit') : t('sandbox.newRule') }}</h2>
        <div class="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
          <div><label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.nameField') }} *</label><input v-model="form.name" :placeholder="t('sandbox.namePlaceholder')" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" /></div>
          <div><label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.descriptionField') }}</label><textarea v-model="form.description" rows="2" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" /></div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.formatField') }}</label><select v-model="form.format" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"><option value="cypher">Cypher</option><option value="yaml">YAML</option></select></div>
            <div><label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.severityField') }}</label><select v-model="form.severity" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"><option value="HARD">{{ t('sandbox.hard') }}</option><option value="SOFT">{{ t('sandbox.soft') }}</option></select></div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.scopeField') }}</label><select v-model="form.scope" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"><option value="project">project</option><option value="component">component</option><option value="issue">issue</option></select></div>
            <div><label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.categoryField') }}</label><select v-model="form.category" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"><option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option></select></div>
          </div>
          <div><label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.codeField') }}</label><textarea v-model="form.code" rows="6" :placeholder="t('sandbox.codePlaceholder')" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 font-mono text-sm dark:border-gray-600 dark:bg-gray-700" spellcheck="false" /></div>
        </div>
        <div class="mt-6 flex justify-end gap-2">
          <button class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700" @click="closeModal">{{ t('sandbox.cancel') }}</button>
          <button :disabled="!form.name" class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50" @click="saveRuleFromModal">{{ editingRule ? t('sandbox.save') : t('sandbox.create') }}</button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteConfirm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showDeleteConfirm = false" role="dialog" aria-modal="true">
      <div class="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 dark:bg-gray-800">
        <div class="flex items-center gap-3 mb-4"><div class="flex-shrink-0 rounded-full bg-red-100 p-2 dark:bg-red-900/30"><svg class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg></div><h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('sandbox.delete') }}</h3></div>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">{{ t('sandbox.deleteConfirm', { name: deleteTarget?.name }) }}</p>
        <div class="flex justify-end gap-3">
          <button class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300" @click="showDeleteConfirm = false">{{ t('sandbox.cancel') }}</button>
          <button class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600" @click="executeDelete">{{ t('sandbox.delete') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSandboxStore } from '@/stores/sandboxStore'
import type { SandboxRule, SandboxRuleFormat, SandboxRuleSeverity } from '@/types/sandbox'
import ImpactReport from '@/components/sandbox/ImpactReport.vue'

const { t } = useI18n()
const store = useSandboxStore()

const search = ref('')
const filterStatus = ref('')
const filterFormat = ref('')
const activeRule = ref<SandboxRule | null>(null)
const editorCode = ref('')
const editorFormat = ref<SandboxRuleFormat>('cypher')
const showModal = ref(false)
const editingRule = ref<SandboxRule | null>(null)
const showDeleteConfirm = ref(false)
const deleteTarget = ref<SandboxRule | null>(null)

const categories = ['ARCHITECTURE', 'TECHNOLOGY', 'NAMING', 'PATTERNS', 'DEPENDENCIES']

const form = ref({
  name: '',
  description: '',
  format: 'cypher' as SandboxRuleFormat,
  severity: 'SOFT' as SandboxRuleSeverity,
  scope: 'project',
  category: 'ARCHITECTURE',
  code: '',
})

const filteredRules = computed(() => {
  let result = store.rules
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter(r => r.name.toLowerCase().includes(q) || r.description.toLowerCase().includes(q))
  }
  if (filterStatus.value) result = result.filter(r => filterStatus.value === 'draft' ? r.isDraft : !r.isDraft)
  if (filterFormat.value) result = result.filter(r => r.format === filterFormat.value)
  return result
})

const lineCount = computed(() => editorCode.value.split('\n').length)

function selectRule(rule: SandboxRule) {
  activeRule.value = rule
  editorCode.value = rule.code
  editorFormat.value = rule.format
}

function openCreateModal() {
  editingRule.value = null
  form.value = { name: '', description: '', format: 'cypher', severity: 'SOFT', scope: 'project', category: 'ARCHITECTURE', code: '' }
  showModal.value = true
}

function openEditModal(rule: SandboxRule) {
  editingRule.value = rule
  form.value = { name: rule.name, description: rule.description, format: rule.format, severity: rule.severity, scope: rule.scope, category: rule.category, code: rule.code }
  showModal.value = true
}

function closeModal() { showModal.value = false; editingRule.value = null }

function confirmDelete(rule: SandboxRule) { deleteTarget.value = rule; showDeleteConfirm.value = true }

async function executeDelete() {
  if (!deleteTarget.value) return
  await store.deleteRule(deleteTarget.value.id)
  if (activeRule.value?.id === deleteTarget.value.id) { activeRule.value = null; editorCode.value = '' }
  showDeleteConfirm.value = false
  deleteTarget.value = null
}

async function saveRule() {
  if (!activeRule.value) return
  await store.updateRule(activeRule.value.id, { code: editorCode.value, format: editorFormat.value })
}

async function saveRuleFromModal() {
  if (!form.value.name) return
  if (editingRule.value) {
    await store.updateRule(editingRule.value.id, form.value)
  } else {
    const newRule = await store.createRule(form.value)
    selectRule(newRule)
  }
  closeModal()
}

async function simulateRule(rule: SandboxRule) {
  if (!activeRule.value || activeRule.value.id !== rule.id) selectRule(rule)
  await store.simulateRule(rule.id)
}

async function promoteRule() {
  if (!activeRule.value) return
  await store.promoteRule(activeRule.value.id)
  activeRule.value = { ...activeRule.value, isDraft: false }
}

onMounted(() => store.fetchRules?.())
</script>
