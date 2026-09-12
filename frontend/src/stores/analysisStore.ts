import { defineStore } from 'pinia'
import { ref } from 'vue'
import { analyzeImpact as apiAnalyzeImpact, analyzeRootCause as apiAnalyzeRootCause, fetchTestFailures as apiFetchTestFailures } from '@/api/mockApi'
import type { ImpactAnalysis, CausalLink, TestFailure } from '@/types'

export const useAnalysisStore = defineStore('analysis', () => {
  const impactResult = ref<ImpactAnalysis | null>(null)
  const rootCauseResults = ref<CausalLink[]>([])
  const testFailures = ref<TestFailure[]>([])
  const loadingImpact = ref(false)
  const loadingRootCause = ref(false)
  const error = ref<string | null>(null)

  async function analyzeImpact(issueId: string): Promise<ImpactAnalysis | null> {
    loadingImpact.value = true
    error.value = null
    impactResult.value = null
    try {
      impactResult.value = await apiAnalyzeImpact(issueId)
      return impactResult.value
    } catch (e) {
      error.value = (e as Error).message
      return null
    } finally {
      loadingImpact.value = false
    }
  }

  async function analyzeRootCause(params: {
    test_name: string
    error_message: string
    component?: string
    labels?: string[]
  }): Promise<CausalLink[]> {
    loadingRootCause.value = true
    error.value = null
    rootCauseResults.value = []
    try {
      rootCauseResults.value = await apiAnalyzeRootCause(params)
      return rootCauseResults.value
    } catch (e) {
      error.value = (e as Error).message
      return []
    } finally {
      loadingRootCause.value = false
    }
  }

  async function fetchTestFailures(): Promise<TestFailure[]> {
    try {
      testFailures.value = await apiFetchTestFailures()
      return testFailures.value
    } catch (e) {
      error.value = (e as Error).message
      return []
    }
  }

  function clearResults() {
    impactResult.value = null
    rootCauseResults.value = []
    error.value = null
  }

  return {
    impactResult,
    rootCauseResults,
    testFailures,
    loadingImpact,
    loadingRootCause,
    error,
    analyzeImpact,
    analyzeRootCause,
    fetchTestFailures,
    clearResults,
  }
})
