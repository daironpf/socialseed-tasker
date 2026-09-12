import client from './client'
import type { APIResponse, Constraint, ConstraintCreateRequest, ValidationResult } from '@/types'

export async function fetchConstraints(): Promise<Constraint[]> {
  const { data } = await client.get<APIResponse<Constraint[]>>('/constraints')
  return data.data || []
}

export async function createConstraint(body: ConstraintCreateRequest): Promise<Constraint> {
  const { data } = await client.post<APIResponse<Constraint>>('/constraints', body)
  if (!data.data) throw new Error('Failed to create constraint')
  return data.data
}

export async function updateConstraint(id: string, body: Partial<ConstraintCreateRequest>): Promise<Constraint> {
  const { data } = await client.patch<APIResponse<Constraint>>(`/constraints/${id}`, body)
  if (!data.data) throw new Error('Failed to update constraint')
  return data.data
}

export async function validateConstraints(entityType: string = 'project', entityData: Record<string, unknown> = {}): Promise<ValidationResult> {
  const { data } = await client.post<APIResponse<ValidationResult>>('/constraints/validate', { entity_type: entityType, entity_data: entityData })
  if (!data.data) throw new Error('Failed to validate constraints')
  return data.data
}
