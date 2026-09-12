import client from './client'
import type { APIResponse, ImpactAnalysis, CausalLink, TestFailure } from '@/types'

export async function analyzeImpact(issueId: string): Promise<ImpactAnalysis> {
  const { data } = await client.get<APIResponse<ImpactAnalysis>>(`/analysis/impact/${issueId}`)
  if (!data.data) throw new Error('Failed to analyze impact')
  return data.data
}

export async function analyzeRootCause(params: {
  test_name: string
  error_message: string
  component?: string
  labels?: string[]
}): Promise<CausalLink[]> {
  const { data } = await client.post<APIResponse<CausalLink[]>>('/analysis/root-cause', params)
  return data.data || []
}

export async function fetchTestFailures(): Promise<TestFailure[]> {
  const { data } = await client.get<APIResponse<TestFailure[]>>('/test-failures')
  return data.data || []
}
