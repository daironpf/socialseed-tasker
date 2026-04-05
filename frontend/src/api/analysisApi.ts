import client from './client'
import type { APIResponse, CausalLink, ImpactAnalysis } from '@/types'

export async function analyzeRootCause(body: {
  test_id: string
  test_name: string
  error_message: string
  stack_trace?: string
  component?: string
  labels?: string[]
}): Promise<CausalLink[]> {
  const { data } = await client.post<APIResponse<CausalLink[]>>('/analyze/root-cause', body)
  return data.data ?? []
}

export async function analyzeImpact(issueId: string): Promise<ImpactAnalysis> {
  const { data } = await client.get<APIResponse<ImpactAnalysis>>(`/analyze/impact/${issueId}`)
  if (!data.data) throw new Error('Failed to analyze impact')
  return data.data
}
