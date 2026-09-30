import client from './client'
import type { APIResponse, ImpactAnalysis, CausalLink, TestFailure } from '@/types'

export async function analyzeImpact(issueId: string): Promise<ImpactAnalysis> {
  const { data } = await client.get<APIResponse<ImpactAnalysis>>(`/analyze/impact/${issueId}`)
  if (!data.data) throw new Error('Failed to analyze impact')
  return data.data
}

export async function analyzeRootCause(params: {
  test_name: string
  error_message: string
  component?: string
  labels?: string[]
}): Promise<CausalLink[]> {
  const body = {
    test_id: `manual-${Date.now()}`,
    test_name: params.test_name,
    error_message: params.error_message,
    component: params.component,
    labels: params.labels ?? [],
  }
  const { data } = await client.post<APIResponse<CausalLink[]>>('/analyze/root-cause', body)
  return data.data || []
}

export async function fetchTestFailures(): Promise<TestFailure[]> {
  const { data } = await client.get<APIResponse<TestFailure[]>>('/test-failures')
  return data.data || []
}
