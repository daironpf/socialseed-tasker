import client from './client'
import type { APIResponse } from '@/types'
import type { AppNotification, NotificationCategory } from '@/types/notifications'

type Wire = Record<string, unknown>

const CATEGORIES: NotificationCategory[] = [
  'mention',
  'hitl',
  'constraint_violation',
  'agent_failure',
  'sla',
  'welcome',
]

export interface NotificationQuery {
  read?: boolean
  category?: NotificationCategory
  limit?: number
  offset?: number
}

/** Backend wire (camelCase, #548) -> `AppNotification`. */
export function normalizeNotification(raw: Wire): AppNotification {
  const category = String(raw.category ?? '')
  const linkTo = raw.linkTo
  const hitlRequestId = raw.hitlRequestId
  return {
    id: String(raw.id ?? ''),
    title: String(raw.title ?? ''),
    message: String(raw.message ?? ''),
    category: (CATEGORIES.includes(category as NotificationCategory)
      ? category
      : 'mention') as NotificationCategory,
    read: Boolean(raw.read),
    requiresAction: Boolean(raw.requiresAction),
    linkTo: typeof linkTo === 'string' && linkTo ? { path: linkTo } : undefined,
    hitlRequestId:
      typeof hitlRequestId === 'string' && hitlRequestId ? hitlRequestId : undefined,
    createdAt: String(raw.createdAt ?? new Date().toISOString()),
  }
}

export async function fetchNotifications(
  query: NotificationQuery = {},
): Promise<AppNotification[]> {
  const { data } = await client.get<APIResponse<Wire[]>>('/notifications', {
    params: query,
  })
  return (data.data ?? []).map(normalizeNotification)
}

export async function markAsRead(id: string): Promise<AppNotification | null> {
  const { data } = await client.patch<APIResponse<Wire>>(`/notifications/${id}/read`)
  return data.data ? normalizeNotification(data.data) : null
}

export async function markAllAsRead(): Promise<number> {
  const { data } = await client.post<APIResponse<{ matchedCount: number }>>(
    '/notifications/mark-all-read',
  )
  return data.data?.matchedCount ?? 0
}

export async function deleteNotification(id: string): Promise<void> {
  await client.delete(`/notifications/${id}`)
}

export async function clearAll(onlyRead = false): Promise<number> {
  const { data } = await client.post<APIResponse<{ deletedCount: number }>>(
    `/notifications/clear-all${onlyRead ? '?onlyRead=true' : ''}`,
  )
  return data.data?.deletedCount ?? 0
}
