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

export interface UserCreateRequest {
  username: string
  email: string
  role?: string
  type?: string
  avatar?: string
  skills?: string[]
  specialization?: string
}

export async function createUser(userData: UserCreateRequest): Promise<User> {
  const { data } = await client.post<APIResponse<User>>('/users', userData)
  if (!data.data) throw new Error('Failed to create user')
  return data.data
}

export async function deleteUser(userId: string): Promise<void> {
  await client.delete(`/users/${userId}`)
}
