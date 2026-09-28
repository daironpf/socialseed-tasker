<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="emit('close')" role="dialog" aria-modal="true">
    <div class="w-full max-w-2xl rounded-xl bg-white shadow-2xl dark:bg-gray-800">
      <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ rule ? t('sandbox.edit') : t('sandbox.newRule') }}</h2>
        <button class="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700" :aria-label="t('sandbox.cancel')" @click="emit('close')">
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>

      <div class="max-h-[70vh] space-y-4 overflow-y-auto px-6 py-4">
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.nameField') }} *</label>
          <input v-model="form.name" :placeholder="t('sandbox.namePlaceholder')" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.descriptionField') }}</label>
          <textarea v-model="form.description" rows="2" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
        </div>

        <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.formatField') }}</label>
            <select v-model="form.format" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" @change="onFormatChange">
              <option value="json">JSON</option>
              <option value="cypher">Cypher</option>
              <option value="yaml">YAML</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.severityField') }}</label>
            <select v-model="form.severity" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
              <option value="HARD">{{ t('sandbox.hard') }}</option>
              <option value="SOFT">{{ t('sandbox.soft') }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.scopeField') }}</label>
            <select v-model="form.scope" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
              <option value="project">project</option>
              <option value="component">component</option>
              <option value="issue">issue</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.categoryField') }}</label>
            <select v-model="form.category" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
        </div>

        <div v-if="paramsEnabled" class="space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900/40">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.ruleTypeField') }}</label>
              <select v-model="form.preset" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option value="field">{{ t('sandbox.presetFieldCondition') }}</option>
                <option value="dependencyCount">{{ t('sandbox.presetDependencyCount') }}</option>
                <option value="labelRequired">{{ t('sandbox.presetLabelRequired') }}</option>
                <option value="selfDependency">{{ t('sandbox.presetSelfDependency') }}</option>
                <option value="forbiddenPath">{{ t('sandbox.presetForbiddenPath') }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.ruleTarget') }}</label>
              <select v-model="form.kind" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option value="node">{{ t('sandbox.targetNode') }}</option>
                <option value="edge">{{ t('sandbox.targetEdge') }}</option>
              </select>
            </div>
          </div>

          <div v-if="form.preset === 'field'" class="grid grid-cols-3 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.fieldField') }}</label>
              <select v-model="form.field" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option v-for="f in availableFields" :key="f" :value="f">{{ f }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.operatorField') }}</label>
              <select v-model="form.cmp" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option v-for="op in cmpOperators" :key="op" :value="op">{{ op }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.valueField') }}</label>
              <input v-model="form.value" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
            </div>
          </div>

          <div v-if="form.preset === 'dependencyCount'" class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.operatorField') }}</label>
              <select v-model="form.cmp" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option v-for="op in countOperators" :key="op" :value="op">{{ op }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.dependencyThreshold') }}</label>
              <input v-model.number="form.maxCount" type="number" min="0" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
            </div>
          </div>

          <div v-if="form.preset === 'labelRequired'">
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.labelField') }}</label>
            <input v-model="form.label" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>

          <div v-if="form.preset === 'forbiddenPath'" class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.fromComponentField') }}</label>
              <input v-model="form.fromComponent" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.toComponentField') }}</label>
              <input v-model="form.toComponent" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.blastDepthField') }}</label>
              <input v-model.number="form.blastRadiusDepth" type="number" min="0" :max="10" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.messageField') }}</label>
              <input v-model="form.message" :placeholder="t('sandbox.messagePlaceholder')" class="w-full rounded-lg border border-gray-300 bg-white px-2 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
            </div>
          </div>
        </div>

        <div v-if="!paramsEnabled" class="rounded-lg border px-3 py-2 text-xs" :class="form.format === 'json' ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300' : 'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-300'">
          {{ form.format === 'json' ? t('sandbox.invalidJson') : t('sandbox.legacyFormatNotice') }}
        </div>

        <div>
          <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('sandbox.codeField') }}</label>
          <textarea v-model="form.code" rows="8" :placeholder="t('sandbox.codePlaceholder')" class="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 font-mono text-xs text-gray-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-200" spellcheck="false" />
        </div>

        <div class="rounded-lg border border-gray-200 p-3 dark:border-gray-700">
          <div class="flex items-center justify-between">
            <h4 class="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('sandbox.previewResult') }}</h4>
            <button class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:hover:bg-gray-700" :disabled="previewing || store.loading || !form.code.trim()" @click="runPreview">
              <span v-if="previewing || store.loading" class="flex items-center gap-1"><span class="h-3 w-3 animate-spin rounded-full border-2 border-blue-600 border-t-transparent"></span>{{ t('sandbox.running') }}</span>
              <span v-else>{{ t('sandbox.previewRun') }}</span>
            </button>
          </div>
          <div v-if="preview" class="mt-2 space-y-2">
            <div class="flex flex-wrap items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
              <span class="rounded bg-gray-100 px-1.5 py-0.5 font-bold dark:bg-gray-700" :class="preview.result.status === 'failed' ? 'text-red-600 dark:text-red-400' : ''">{{ preview.result.status === 'failed' ? t('sandbox.simulationFailed') : t('sandbox.completedLabel') }}</span>
              <span class="rounded px-1.5 py-0.5 font-bold" :class="preview.dataSource === 'api' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'">{{ preview.dataSource === 'api' ? t('sandbox.graphSourceApi') : t('sandbox.graphSourceFallback') }}</span>
              <template v-if="preview.result.status !== 'failed'">
                <span>{{ preview.result.totalNodesChecked }} {{ t('sandbox.nodesChecked') }}</span>
                <span>{{ preview.result.totalEdgesChecked }} {{ t('sandbox.edgesChecked') }}</span>
                <span class="font-semibold" :class="preview.result.violations.length > 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">{{ preview.result.violations.length }} {{ t('sandbox.violationsFound') }}</span>
                <span>{{ preview.result.matchedNodes.length }} {{ t('sandbox.matchedNodes') }}</span>
                <span v-if="preview.result.blastRadius">{{ t('sandbox.blastRadius') }}: {{ preview.result.blastRadius.total }} ({{ preview.result.blastRadius.critical }} {{ t('sandbox.blastCritical') }})</span>
              </template>
            </div>
            <p v-if="preview.result.status === 'failed'" class="text-xs text-red-600 dark:text-red-400">{{ preview.result.error === 'unrecognizedRule' ? t('sandbox.unrecognizedRule') : t('sandbox.simulationFailed') }}</p>
            <div v-else-if="preview.result.violations.length > 0" class="max-h-32 space-y-1 overflow-y-auto">
              <div v-for="(v, idx) in preview.result.violations.slice(0, 20)" :key="idx" class="flex items-center gap-2 rounded bg-red-50 px-2 py-1 text-xs text-red-700 dark:bg-red-900/20 dark:text-red-300">
                <span class="font-bold">{{ v.severity }}</span>
                <span class="truncate">{{ v.message }}</span>
              </div>
            </div>
            <p v-else class="text-xs text-green-600 dark:text-green-400">{{ t('sandbox.previewClean') }}</p>
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-2 border-t border-gray-200 px-6 py-4 dark:border-gray-700">
        <button class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700" @click="emit('close')">{{ t('sandbox.cancel') }}</button>
        <button class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50" :disabled="!form.name.trim() || saving" @click="save">
          <span v-if="saving" class="flex items-center gap-1"><span class="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"></span>{{ t('sandbox.running') }}</span>
          <span v-else>{{ rule ? t('sandbox.save') : t('sandbox.create') }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSandboxStore } from '@/stores/sandboxStore'
import type { SandboxRule, SandboxRuleFormat, SandboxRuleSeverity, SimulationDataSource } from '@/types/sandbox'
import type { Condition, EngineResult, RuleDsl, RuleOperator } from '@/utils/ruleEngine'
import { parseRuleDsl, validateRuleDsl } from '@/utils/ruleEngine'

type RulePreset = 'field' | 'dependencyCount' | 'labelRequired' | 'selfDependency' | 'forbiddenPath'

const props = defineProps<{
  open: boolean
  rule: SandboxRule | null
}>()

const emit = defineEmits<{
  close: []
  saved: [rule: SandboxRule]
}>()

const { t } = useI18n()
const store = useSandboxStore()

const categories = ['ARCHITECTURE', 'TECHNOLOGY', 'NAMING', 'PATTERNS', 'DEPENDENCIES']
const cmpOperators: RuleOperator[] = ['=', '!=', '>', '<', '>=', '<=']
const countOperators: RuleOperator[] = ['>', '>=', '=', '!=', '<', '<=']
const nodeFields = ['status', 'priority', 'component', 'title', 'id']
const edgeFields = ['from.component', 'to.component', 'from.status', 'to.status', 'from.priority', 'to.priority', 'from.title', 'to.title', 'type']

const form = reactive({
  name: '',
  description: '',
  format: 'json' as SandboxRuleFormat,
  severity: 'SOFT' as SandboxRuleSeverity,
  scope: 'project',
  category: 'ARCHITECTURE',
  kind: 'node' as 'node' | 'edge',
  preset: 'field' as RulePreset,
  field: 'status',
  cmp: '=' as RuleOperator,
  value: '',
  fromComponent: '',
  toComponent: '',
  maxCount: 5,
  label: 'priority',
  message: '',
  blastRadiusDepth: 3,
  code: '',
})

const preview = ref<{ result: EngineResult; dataSource: SimulationDataSource } | null>(null)
const previewing = ref(false)
const saving = ref(false)
const codeParseError = ref(false)
const unmappableDsl = ref(false)

const paramsEnabled = computed(() => form.format === 'json' && !codeParseError.value && !unmappableDsl.value)

const availableFields = computed(() => (form.kind === 'edge' ? edgeFields : nodeFields))

function coerceValue(raw: string): string | number {
  const trimmed = raw.trim()
  if (trimmed !== '' && !Number.isNaN(Number(trimmed))) return Number(trimmed)
  return raw
}

function buildMatch(): Condition {
  switch (form.preset) {
    case 'dependencyCount':
      return { op: 'dependencyCount', direction: 'out', cmp: form.cmp, value: Number(form.maxCount) || 0 }
    case 'labelRequired':
      return { op: 'contains', field: 'labels', value: form.label, negate: true }
    case 'selfDependency':
      return { op: 'sameNode' }
    case 'forbiddenPath':
      return {
        op: 'all',
        conditions: [
          { op: 'compare', field: 'from.component', cmp: '=', value: form.fromComponent },
          { op: 'compare', field: 'to.component', cmp: '=', value: form.toComponent },
        ],
      }
    case 'field':
    default: {
      const field = form.kind === 'edge' && !form.field.includes('.') && form.field !== 'type' ? `from.${form.field}` : form.field
      return { op: 'compare', field, cmp: form.cmp, value: coerceValue(form.value) }
    }
  }
}

function buildDsl(): RuleDsl {
  const dsl: RuleDsl = { version: 1, kind: form.kind, match: buildMatch() }
  if (form.message.trim()) dsl.message = form.message.trim()
  dsl.blastRadiusDepth = Math.min(Math.max(Number(form.blastRadiusDepth) || 0, 0), 10)
  return dsl
}

function regenerateCode(): void {
  if (form.format !== 'json' || !paramsEnabled.value) return
  form.code = JSON.stringify(buildDsl(), null, 2)
  preview.value = null
}

function applyDslToForm(dsl: RuleDsl): boolean {
  form.kind = dsl.kind
  form.message = dsl.message ?? ''
  form.blastRadiusDepth = dsl.blastRadiusDepth ?? 3
  const match = dsl.match
  if (match.op === 'sameNode') {
    form.preset = 'selfDependency'
    return true
  }
  if (match.op === 'dependencyCount') {
    form.preset = 'dependencyCount'
    form.cmp = match.cmp
    form.maxCount = match.value
    return true
  }
  if (match.op === 'contains' && match.field === 'labels') {
    form.preset = 'labelRequired'
    form.label = match.value
    return true
  }
  if (match.op === 'all' && match.conditions.length === 2) {
    const [first, second] = match.conditions
    if (first.op === 'compare' && second.op === 'compare' && first.field === 'from.component' && second.field === 'to.component') {
      form.preset = 'forbiddenPath'
      form.fromComponent = String(first.value)
      form.toComponent = String(second.value)
      return true
    }
  }
  if (match.op === 'compare') {
    form.preset = 'field'
    if (match.field.includes('.')) form.kind = 'edge'
    form.field = match.field
    form.cmp = match.cmp
    form.value = String(match.value)
    return true
  }
  return false
}

function init(): void {
  preview.value = null
  codeParseError.value = false
  unmappableDsl.value = false
  if (!props.rule) {
    Object.assign(form, {
      name: '',
      description: '',
      format: 'json' as SandboxRuleFormat,
      severity: 'SOFT' as SandboxRuleSeverity,
      scope: 'project',
      category: 'ARCHITECTURE',
      kind: 'node' as 'node' | 'edge',
      preset: 'field' as RulePreset,
      field: 'status',
      cmp: '=' as RuleOperator,
      value: 'BLOCKED',
      fromComponent: '',
      toComponent: '',
      maxCount: 5,
      label: 'priority',
      message: '',
      blastRadiusDepth: 3,
      code: '',
    })
    regenerateCode()
    return
  }
  Object.assign(form, {
    name: props.rule.name,
    description: props.rule.description,
    format: props.rule.format,
    severity: props.rule.severity,
    scope: props.rule.scope,
    category: props.rule.category,
    kind: 'node' as 'node' | 'edge',
    preset: 'field' as RulePreset,
    field: 'status',
    cmp: '=' as RuleOperator,
    value: '',
    fromComponent: '',
    toComponent: '',
    maxCount: 5,
    label: 'priority',
    message: '',
    blastRadiusDepth: 3,
    code: props.rule.code,
  })
  if (props.rule.format === 'json') {
    try {
      const dsl = validateRuleDsl(JSON.parse(props.rule.code))
      if (!dsl) codeParseError.value = true
      else if (!applyDslToForm(dsl)) unmappableDsl.value = true
    } catch {
      codeParseError.value = true
    }
  }
}

watch(
  () => [
    form.preset,
    form.kind,
    form.field,
    form.cmp,
    form.value,
    form.fromComponent,
    form.toComponent,
    form.maxCount,
    form.label,
    form.message,
    form.blastRadiusDepth,
  ],
  () => {
    regenerateCode()
  },
)

watch(
  () => form.code,
  () => {
    if (form.format !== 'json') return
    if (!form.code.trim()) return
    const parsed = parseRuleDsl(form.code, 'json')
    codeParseError.value = parsed === null
    if (parsed && unmappableDsl.value) {
      unmappableDsl.value = !applyDslToForm(parsed)
    }
    preview.value = null
  },
)

function onFormatChange(): void {
  preview.value = null
  if (form.format !== 'json') return
  codeParseError.value = false
  unmappableDsl.value = false
  try {
    const dsl = validateRuleDsl(JSON.parse(form.code))
    if (!dsl) {
      codeParseError.value = true
      return
    }
    unmappableDsl.value = !applyDslToForm(dsl)
  } catch {
    unmappableDsl.value = false
  }
  if (!codeParseError.value && !unmappableDsl.value) regenerateCode()
}

watch(() => props.open, open => { if (open) init() }, { immediate: true })

async function runPreview(): Promise<void> {
  previewing.value = true
  try {
    preview.value = await store.simulatePreview({
      name: form.name.trim() || 'preview',
      code: form.code,
      format: form.format,
      severity: form.severity,
    })
  } catch {
    preview.value = null
  } finally {
    previewing.value = false
  }
}

async function save(): Promise<void> {
  if (!form.name.trim()) return
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      description: form.description,
      format: form.format,
      severity: form.severity,
      scope: form.scope,
      category: form.category,
      code: form.code,
    }
    let saved: SandboxRule | undefined
    if (props.rule) {
      await store.updateRule(props.rule.id, payload)
      saved = store.rules.find(r => r.id === props.rule!.id)
    } else {
      saved = await store.createRule(payload)
    }
    if (saved) emit('saved', saved)
    emit('close')
  } finally {
    saving.value = false
  }
}
</script>
