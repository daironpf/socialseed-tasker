import client from './client'
import type { APIResponse, User } from '@/types'

export async function fetchUsers(): Promise<User[]> {
  const { data } = await client.get<APIResponse<User[]>>('/users')
  return data.data || []
}

export async function updateUser(userId: string, userData: Partial<User>): Promise<User> {
  const { data } = await client.put<APIResponse<User>>(`/users/${userId}`, userData)
  if (!data.data) throw new Error('Failed to update user')
  return data.data
}
