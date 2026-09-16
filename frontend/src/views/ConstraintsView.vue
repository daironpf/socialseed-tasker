<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('constraints.title') }}</h1>
      </div>
      <div class="flex items-center gap-3">
        <button
          class="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
          @click="runValidation"
        >
          {{ t('analysis.analyze') }}
        </button>
        <button
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          @click="openCreateModal"
        >
          {{ t('constraints.newConstraint') }}
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-4 gap-4">
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ store.constraints.length }}</div>
        <div class="text-xs text-gray-500">{{ t('constraints.hard') }} / {{ t('constraints.soft') }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-red-600 dark:text-red-400">{{ store.hardCount }}</div>
        <div class="text-xs text-gray-500">{{ t('constraints.hard') }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-amber-600 dark:text-amber-400">{{ store.softCount }}</div>
        <div class="text-xs text-gray-500">{{ t('constraints.soft') }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ store.activeCount }}</div>
        <div class="text-xs text-gray-500">{{ t('constraints.active') }}</div>
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
          :placeholder="t('constraints.search')"
          :aria-label="t('constraints.search')"
          class="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800"
        />
      </div>
      <div class="flex gap-2">
        <select
          v-model="filterCategory"
          :aria-label="t('constraints.allCategories')"
          class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
        >
          <option value="">{{ t('constraints.allCategories') }}</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
        <select
          v-model="filterSeverity"
          :aria-label="t('constraints.allSeverities')"
          class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
        >
          <option value="">{{ t('constraints.allSeverities') }}</option>
          <option value="HARD">{{ t('constraints.hard') }}</option>
          <option value="SOFT">{{ t('constraints.soft') }}</option>
        </select>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="flex justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
    </div>

    <!-- Error -->
    <div v-else-if="store.error" class="rounded-md bg-red-50 p-4 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-200">{{ t('constraints.errorLoading') }}</h3>
          <div class="mt-2 text-sm text-red-700 dark:text-red-300">{{ store.error }}</div>
        </div>
      </div>
    </div>

    <!-- Validation Results Banner -->
    <div
      v-if="store.validationResult"
      class="rounded-xl border p-4"
      :class="store.validationResult.valid
        ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
        : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div
            class="flex h-10 w-10 items-center justify-center rounded-full"
            :class="store.validationResult.valid ? 'bg-green-100 dark:bg-green-800' : 'bg-red-100 dark:bg-red-800'"
          >
            <svg v-if="store.validationResult.valid" class="h-5 w-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <div>
            <h3 class="font-semibold" :class="store.validationResult.valid ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'">
              {{ store.validationResult.valid ? t('constraints.allPassed') : t('constraints.violationsDetected') }}
            </h3>
            <p class="text-sm" :class="store.validationResult.valid ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ t('constraints.checkedConstraints', { count: store.validationResult.checked_constraints }) }}
              <span v-if="!store.validationResult.valid"> — {{ t('constraints.hardViolations', { count: store.validationResult.hard_violations }) }}, {{ t('constraints.softViolations', { count: store.validationResult.soft_violations }) }}</span>
            </p>
          </div>
        </div>
        <button
          class="text-gray-400 hover:text-gray-600"
          :aria-label="t('common.close')"
          @click="store.validationResult = null"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>
      <div v-if="store.validationResult.violations.length > 0" class="mt-4 space-y-2">
        <div
          v-for="(v, idx) in store.validationResult.violations"
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
            <div class="mt-1 text-xs text-gray-500 dark:text-gray-500">{{ t('constraints.remediation') }} {{ v.remediation }}</div>
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
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('constraints.id') }}</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('constraints.name') }}</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('constraints.category') }}</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('constraints.severity') }}</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('constraints.scope') }}</th>
            <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('constraints.active') }}</th>
            <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('constraints.autoFix') }}</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('constraints.actions') }}</th>
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
              <div class="flex items-center justify-end gap-1">
                <button class="rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-blue-600 dark:hover:bg-gray-700" @click.stop="openEditModal(c)">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                </button>
                <button class="rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-red-600 dark:hover:bg-gray-700" @click.stop="deleteConstraint(c)" :title="t('issues.delete')">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredConstraints.length === 0">
            <td colspan="8" class="px-4 py-12 text-center text-sm text-gray-400">{{ t('common.noData') }}</td>
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
              <div class="text-xs text-gray-500">{{ t('constraints.category') }}</div>
              <div class="mt-1">
                <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium" :class="categoryClass(selectedConstraint.category)">
                  {{ selectedConstraint.category }}
                </span>
              </div>
            </div>
            <div>
              <div class="text-xs text-gray-500">{{ t('constraints.scope') }}</div>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedConstraint.scope }}</p>
            </div>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('constraints.description') }}</label>
            <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedConstraint.description }}</p>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('constraints.logic') }}</label>
            <div class="mt-1 rounded-lg bg-gray-50 p-3 font-mono text-sm text-gray-800 dark:bg-gray-700/50 dark:text-gray-200">
              {{ selectedConstraint.logic }}
            </div>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('constraints.ruleDefinition') }}</label>
            <pre class="mt-1 rounded-lg bg-gray-50 p-3 font-mono text-xs text-gray-800 dark:bg-gray-700/50 dark:text-gray-200 overflow-x-auto">{{ JSON.stringify(selectedConstraint.rule, null, 2) }}</pre>
          </div>

          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('constraints.remediation') }}</label>
            <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedConstraint.remediation }}</p>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('constraints.active') }}</label>
              <div class="mt-1">
                <span
                  class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="selectedConstraint.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'"
                >
                  {{ selectedConstraint.is_active ? t('constraints.active') : t('constraints.inactive') }}
                </span>
              </div>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('constraints.autoFix') }}</label>
              <div class="mt-1">
                <span
                  class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="selectedConstraint.auto_fix ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'"
                >
                  {{ selectedConstraint.auto_fix ? t('constraints.autoFixEnabled') : t('constraints.autoFixDisabled') }}
                </span>
              </div>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('constraints.updated') }}</label>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ new Date(selectedConstraint.updated_at).toLocaleDateString() }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="closeModal" role="dialog" aria-modal="true">
      <div class="w-full max-w-lg rounded-xl bg-white p-6 shadow-2xl dark:bg-gray-800">
        <h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          {{ editingConstraint ? t('issues.edit') : t('constraints.newConstraint') }}
        </h2>
        <div class="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('constraints.name') }} *</label>
            <input v-model="form.name" :placeholder="t('constraints.namePlaceholder')" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('constraints.description') }}</label>
            <textarea v-model="form.description" rows="2" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('constraints.category') }}</label>
              <select v-model="form.category" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('constraints.severity') }}</label>
              <select v-model="form.severity" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option value="HARD">{{ t('constraints.hardBlocking') }}</option>
                <option value="SOFT">{{ t('constraints.softWarning') }}</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('constraints.scope') }}</label>
              <select v-model="form.scope" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option value="project">project</option>
                <option value="component">component</option>
                <option value="issue">issue</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('constraints.autoFix') }}</label>
              <select v-model="form.auto_fix" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option :value="true">{{ t('constraints.autoFixEnabled') }}</option>
                <option :value="false">{{ t('constraints.autoFixDisabled') }}</option>
              </select>
            </div>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('constraints.logic') }}</label>
            <input v-model="form.logic" :placeholder="t('constraints.logicPlaceholder')" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('constraints.remediation') }}</label>
            <input v-model="form.remediation" :placeholder="t('constraints.remediationPlaceholder')" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>
        </div>
        <div class="mt-6 flex justify-end gap-2">
          <button class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700" @click="closeModal">{{ t('issues.cancel') }}</button>
          <button
            :disabled="!form.name"
            class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            @click="saveConstraint"
          >
            {{ editingConstraint ? t('issues.save') : t('issues.create') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteConfirm"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="showDeleteConfirm = false"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 dark:bg-gray-800">
        <div class="flex items-center gap-3 mb-4">
          <div class="flex-shrink-0 rounded-full bg-red-100 p-2 dark:bg-red-900/30">
            <svg class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('issues.delete') }}</h3>
        </div>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {{ t('constraints.deleteConfirm', { name: deleteTarget?.name }) }}
        </p>
        <div class="flex justify-end gap-3">
          <button
            type="button"
            class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
            @click="showDeleteConfirm = false"
          >
            {{ t('issues.cancel') }}
          </button>
          <button
            type="button"
            class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600"
            @click="executeDelete"
          >
            {{ t('issues.delete') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useConstraintsStore } from '@/stores/constraintsStore'
import type { Constraint, ConstraintCategory, ConstraintSeverity } from '@/types'

const { t } = useI18n()

const store = useConstraintsStore()

const search = ref('')
const filterCategory = ref('')
const filterSeverity = ref('')
const selectedConstraint = ref<Constraint | null>(null)
const showModal = ref(false)
const editingConstraint = ref<Constraint | null>(null)

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

const filteredConstraints = computed(() => {
  let result = store.constraints
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

const showDeleteConfirm = ref(false)
const deleteTarget = ref<Constraint | null>(null)

function deleteConstraint(c: Constraint) {
  deleteTarget.value = c
  showDeleteConfirm.value = true
}

async function executeDelete() {
  if (!deleteTarget.value) return
  await store.deleteConstraint(deleteTarget.value.id)
  showDeleteConfirm.value = false
  deleteTarget.value = null
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

async function saveConstraint() {
  if (!form.value.name) return
  try {
    if (editingConstraint.value) {
      await store.updateConstraint(editingConstraint.value.id, form.value)
    } else {
      await store.createConstraint(form.value)
    }
    closeModal()
  } catch (e) {
    console.error('Failed to save constraint:', e)
  }
}

async function runValidation() {
  await store.validateConstraints('project', {})
}

onMounted(() => store.fetchConstraints())
</script>
