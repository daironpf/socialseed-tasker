<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Constraints</h1>
        <p class="text-sm text-gray-500">Architectural rules and validation engine</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          class="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
          @click="runValidation"
        >
          Validate All
        </button>
        <button
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          @click="openCreateModal"
        >
          + New Constraint
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-4 gap-4">
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ constraints.length }}</div>
        <div class="text-xs text-gray-500">Total Rules</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-red-600 dark:text-red-400">{{ hardCount }}</div>
        <div class="text-xs text-gray-500">HARD (blocking)</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-amber-600 dark:text-amber-400">{{ softCount }}</div>
        <div class="text-xs text-gray-500">SOFT (warning)</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ activeCount }}</div>
        <div class="text-xs text-gray-500">Active</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3">
      <div class="relative flex-1 min-w-[200px]">
        <svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="search"
          type="text"
          placeholder="Search constraints..."
          class="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800"
        />
      </div>
      <div class="flex gap-2">
        <select
          v-model="filterCategory"
          class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
        >
          <option value="">All Categories</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
        <select
          v-model="filterSeverity"
          class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
        >
          <option value="">All Severities</option>
          <option value="HARD">HARD</option>
          <option value="SOFT">SOFT</option>
        </select>
      </div>
    </div>

    <!-- Validation Results Banner -->
    <div
      v-if="validationResult"
      class="rounded-xl border p-4"
      :class="validationResult.valid
        ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
        : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div
            class="flex h-10 w-10 items-center justify-center rounded-full"
            :class="validationResult.valid ? 'bg-green-100 dark:bg-green-800' : 'bg-red-100 dark:bg-red-800'"
          >
            <svg v-if="validationResult.valid" class="h-5 w-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <div>
            <h3 class="font-semibold" :class="validationResult.valid ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'">
              {{ validationResult.valid ? 'All constraints passed' : 'Constraint violations detected' }}
            </h3>
            <p class="text-sm" :class="validationResult.valid ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              Checked {{ validationResult.checked_constraints }} active constraints
              <span v-if="!validationResult.valid"> — {{ validationResult.hard_violations }} hard, {{ validationResult.soft_violations }} soft violations</span>
            </p>
          </div>
        </div>
        <button
          class="text-gray-400 hover:text-gray-600"
          @click="validationResult = null"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>
      <div v-if="validationResult.violations.length > 0" class="mt-4 space-y-2">
        <div
          v-for="(v, idx) in validationResult.violations"
          :key="idx"
          class="flex items-start gap-3 rounded-lg border p-3"
          :class="v.severity === 'HARD'
            ? 'border-red-200 bg-red-100/50 dark:border-red-800 dark:bg-red-900/10'
            : 'border-amber-200 bg-amber-100/50 dark:border-amber-800 dark:bg-amber-900/10'"
        >
          <span
            class="mt-0.5 inline-flex h-5 items-center rounded px-1.5 text-[10px] font-bold"
            :class="v.severity === 'HARD'
              ? 'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200'
              : 'bg-amber-200 text-amber-800 dark:bg-amber-800 dark:text-amber-200'"
          >{{ v.severity }}</span>
          <div class="flex-1">
            <div class="text-sm font-medium text-gray-900 dark:text-white">{{ v.constraint_name }}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400">{{ v.message }}</div>
            <div class="mt-1 text-xs text-gray-500 dark:text-gray-500">Remediation: {{ v.remediation }}</div>
          </div>
          <span class="rounded px-1.5 py-0.5 text-[10px] font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">{{ v.category }}</span>
        </div>
      </div>
    </div>

    <!-- Constraints Table -->
    <div class="rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Category</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Severity</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Scope</th>
            <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Active</th>
            <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Auto-fix</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
          <tr
            v-for="c in filteredConstraints"
            :key="c.id"
            class="cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
            @click="openDetail(c)"
          >
            <td class="px-4 py-3 font-mono text-xs font-bold text-gray-500">{{ c.id }}</td>
            <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ c.name }}</td>
            <td class="px-4 py-3">
              <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" :class="categoryClass(c.category)">
                {{ c.category }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-bold" :class="severityClass(c.severity)">
                {{ c.severity }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{{ c.scope }}</td>
            <td class="px-4 py-3 text-center">
              <span v-if="c.is_active" class="inline-flex h-2 w-2 rounded-full bg-green-500"></span>
              <span v-else class="inline-flex h-2 w-2 rounded-full bg-gray-300"></span>
            </td>
            <td class="px-4 py-3 text-center">
              <svg v-if="c.auto_fix" class="mx-auto h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <span v-else class="text-xs text-gray-400">—</span>
            </td>
            <td class="px-4 py-3 text-right">
              <button class="rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-blue-600 dark:hover:bg-gray-700" @click.stop="openEditModal(c)">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
              </button>
            </td>
          </tr>
          <tr v-if="filteredConstraints.length === 0">
            <td colspan="8" class="px-4 py-12 text-center text-sm text-gray-400">No constraints found</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detail Panel -->
    <div
      v-if="selectedConstraint"
      class="fixed inset-0 z-50 flex justify-end bg-black/50"
      @click.self="selectedConstraint = null"
    >
      <div class="h-full w-full max-w-2xl overflow-y-auto bg-white shadow-2xl dark:bg-gray-800">
        <div class="sticky top-0 z-10 border-b border-gray-200 bg-white px-6 py-4 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span class="inline-flex h-10 w-10 items-center justify-center rounded-xl text-xs font-bold" :class="severityClass(selectedConstraint.severity)">
                {{ selectedConstraint.severity }}
              </span>
              <div>
                <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ selectedConstraint.name }}</h2>
                <p class="text-xs text-gray-500 font-mono">{{ selectedConstraint.id }}</p>
              </div>
            </div>
            <button class="text-gray-400 hover:text-gray-600" @click="selectedConstraint = null">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
        </div>

        <div class="p-6 space-y-6">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Category</label>
              <div class="mt-1">
                <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium" :class="categoryClass(selectedConstraint.category)">
                  {{ selectedConstraint.category }}
                </span>
              </div>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Scope</label>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedConstraint.scope }}</p>
            </div>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Description</label>
            <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedConstraint.description }}</p>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Logic</label>
            <div class="mt-1 rounded-lg bg-gray-50 p-3 font-mono text-sm text-gray-800 dark:bg-gray-700/50 dark:text-gray-200">
              {{ selectedConstraint.logic }}
            </div>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Rule Definition</label>
            <pre class="mt-1 rounded-lg bg-gray-50 p-3 font-mono text-xs text-gray-800 dark:bg-gray-700/50 dark:text-gray-200 overflow-x-auto">{{ JSON.stringify(selectedConstraint.rule, null, 2) }}</pre>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Remediation</label>
            <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedConstraint.remediation }}</p>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Active</label>
              <div class="mt-1">
                <span
                  class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="selectedConstraint.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'"
                >
                  {{ selectedConstraint.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Auto-fix</label>
              <div class="mt-1">
                <span
                  class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="selectedConstraint.auto_fix ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'"
                >
                  {{ selectedConstraint.auto_fix ? 'Enabled' : 'Disabled' }}
                </span>
              </div>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Updated</label>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ new Date(selectedConstraint.updated_at).toLocaleDateString() }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="closeModal">
      <div class="w-full max-w-lg rounded-xl bg-white p-6 shadow-2xl dark:bg-gray-800">
        <h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          {{ editingConstraint ? 'Edit Constraint' : 'New Constraint' }}
        </h2>
        <div class="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Name *</label>
            <input v-model="form.name" placeholder="e.g., no-circular-deps" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Description</label>
            <textarea v-model="form.description" rows="2" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Category</label>
              <select v-model="form.category" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Severity</label>
              <select v-model="form.severity" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option value="HARD">HARD (blocking)</option>
                <option value="SOFT">SOFT (warning)</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Scope</label>
              <select v-model="form.scope" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option value="project">project</option>
                <option value="component">component</option>
                <option value="issue">issue</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Auto-fix</label>
              <select v-model="form.auto_fix" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option :value="true">Enabled</option>
                <option :value="false">Disabled</option>
              </select>
            </div>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Logic</label>
            <input v-model="form.logic" placeholder="e.g., IF issue.labels.length < 1 THEN WARN" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Remediation</label>
            <input v-model="form.remediation" placeholder="How to fix violations" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>
        </div>
        <div class="mt-6 flex justify-end gap-2">
          <button class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700" @click="closeModal">Cancel</button>
          <button
            :disabled="!form.name"
            class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            @click="saveConstraint"
          >
            {{ editingConstraint ? 'Save' : 'Create' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Constraint, ConstraintCategory, ConstraintSeverity, ValidationResult } from '@/types'

const API = import.meta.env.VITE_API_URL || ''
const MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const constraints = ref<Constraint[]>([])
const search = ref('')
const filterCategory = ref('')
const filterSeverity = ref('')
const selectedConstraint = ref<Constraint | null>(null)
const showModal = ref(false)
const editingConstraint = ref<Constraint | null>(null)
const validationResult = ref<ValidationResult | null>(null)

const categories: ConstraintCategory[] = ['ARCHITECTURE', 'TECHNOLOGY', 'NAMING', 'PATTERNS', 'DEPENDENCIES']

const form = ref({
  name: '',
  description: '',
  category: 'ARCHITECTURE' as ConstraintCategory,
  severity: 'SOFT' as ConstraintSeverity,
  scope: 'project',
  logic: '',
  remediation: '',
  auto_fix: false,
})

const hardCount = computed(() => constraints.value.filter(c => c.severity === 'HARD').length)
const softCount = computed(() => constraints.value.filter(c => c.severity === 'SOFT').length)
const activeCount = computed(() => constraints.value.filter(c => c.is_active).length)

const filteredConstraints = computed(() => {
  let result = constraints.value
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter(c => c.name.toLowerCase().includes(q) || c.id.toLowerCase().includes(q) || c.description.toLowerCase().includes(q))
  }
  if (filterCategory.value) result = result.filter(c => c.category === filterCategory.value)
  if (filterSeverity.value) result = result.filter(c => c.severity === filterSeverity.value)
  return result
})

function categoryClass(cat: string) {
  const m: Record<string, string> = {
    ARCHITECTURE: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    TECHNOLOGY: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    NAMING: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300',
    PATTERNS: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
    DEPENDENCIES: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  }
  return m[cat] || 'bg-gray-100 text-gray-700'
}

function severityClass(sev: string) {
  return sev === 'HARD'
    ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
    : 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300'
}

function openDetail(c: Constraint) { selectedConstraint.value = c }

function openCreateModal() {
  editingConstraint.value = null
  form.value = { name: '', description: '', category: 'ARCHITECTURE', severity: 'SOFT', scope: 'project', logic: '', remediation: '', auto_fix: false }
  showModal.value = true
}

function openEditModal(c: Constraint) {
  editingConstraint.value = c
  form.value = {
    name: c.name,
    description: c.description,
    category: c.category,
    severity: c.severity,
    scope: c.scope,
    logic: c.logic,
    remediation: c.remediation,
    auto_fix: c.auto_fix,
  }
  showModal.value = true
}

function closeModal() { showModal.value = false; editingConstraint.value = null }

async function fetchConstraints() {
  try {
    const base = MOCK ? '/mock-api/mock' : `${API}/v1`
    const res = await fetch(`${base}/constraints`)
    const json = await res.json()
    constraints.value = json.data || []
  } catch (e) {
    console.error('Failed to load constraints:', e)
  }
}

async function saveConstraint() {
  if (!form.value.name) return
  try {
    const base = MOCK ? '/mock-api/mock' : `${API}/v1`
    if (editingConstraint.value) {
      constraints.value = constraints.value.map(c =>
        c.id === editingConstraint.value!.id ? { ...c, ...form.value, updated_at: new Date().toISOString() } : c
      )
    } else {
      const res = await fetch(`${base}/constraints`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
      const json = await res.json()
      if (json.data) constraints.value.push(json.data)
    }
  } catch (e) { console.error('Save failed:', e) }
  closeModal()
}

async function runValidation() {
  try {
    const base = MOCK ? '/mock-api/mock' : `${API}/v1`
    const res = await fetch(`${base}/constraints/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_type: 'project', entity_data: {} }),
    })
    const json = await res.json()
    validationResult.value = json.data
  } catch (e) { console.error('Validation failed:', e) }
}

onMounted(fetchConstraints)
</script>
