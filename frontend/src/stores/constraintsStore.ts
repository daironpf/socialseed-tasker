import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/constraintsApi'
import type { Constraint, ConstraintCreateRequest, ConstraintCategory, ConstraintSeverity, ValidationResult } from '@/types'

export const useConstraintsStore = defineStore('constraints', () => {
  const constraints = ref<Constraint[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const validationResult = ref<ValidationResult | null>(null)

  const hardCount = computed(() => constraints.value.filter(c => c.severity === 'HARD').length)
  const softCount = computed(() => constraints.value.filter(c => c.severity === 'SOFT').length)
  const activeCount = computed(() => constraints.value.filter(c => c.is_active).length)

  function byCategory(cat: ConstraintCategory): Constraint[] {
    return constraints.value.filter(c => c.category === cat)
  }

  function bySeverity(sev: ConstraintSeverity): Constraint[] {
    return constraints.value.filter(c => c.severity === sev)
  }

  async function fetchConstraints() {
    loading.value = true
    error.value = null
    try {
      constraints.value = await api.fetchConstraints()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function createConstraint(body: ConstraintCreateRequest): Promise<Constraint | null> {
    try {
      const created = await api.createConstraint(body)
      constraints.value.push(created)
      return created
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function updateConstraint(id: string, body: Partial<ConstraintCreateRequest>): Promise<Constraint | null> {
    try {
      const updated = await api.updateConstraint(id, body)
      const idx = constraints.value.findIndex(c => c.id === id)
      if (idx !== -1) constraints.value[idx] = updated
      return updated
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function validateConstraints(entityType: string = 'project', entityData: Record<string, unknown> = {}): Promise<ValidationResult | null> {
    try {
      validationResult.value = await api.validateConstraints(entityType, entityData)
      return validationResult.value
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  return {
    constraints,
    loading,
    error,
    validationResult,
    hardCount,
    softCount,
    activeCount,
    byCategory,
    bySeverity,
    fetchConstraints,
    createConstraint,
    updateConstraint,
    validateConstraints,
  }
})
