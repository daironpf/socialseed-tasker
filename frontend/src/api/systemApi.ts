import client from './client'
import type { APIResponse, SystemHealth, SyncQueue } from '@/types'

const defaultHealth: SystemHealth = {
  status: 'unknown',
  timestamp: '',
  services: { neo4j: { status: 'unknown' }, api: { status: 'unknown' }, workers: { status: 'unknown' } },
  metrics: { total_issues: 0, blocked_issues: 0, total_components: 0, agents_working: 0, total_users: 0, total_constraints: 0, active_constraints: 0 },
}

const defaultSyncQueue: SyncQueue = { pending: 0, queue: [], last_sync_at: '', github_connected: false }

export async function fetchSystemHealth(): Promise<SystemHealth> {
  const { data } = await client.get<APIResponse<SystemHealth>>('/health')
  return data.data || defaultHealth
}

export async function fetchSyncQueue(): Promise<SyncQueue> {
  const { data } = await client.get<APIResponse<SyncQueue>>('/sync-queue')
  return data.data || defaultSyncQueue
}

export async function adminSeed(seedType: string = 'full', resetFirst: boolean = false): Promise<any> {
  const { data } = await client.post<APIResponse<any>>('/admin/seed', { seed_type: seedType, reset_first: resetFirst })
  return data.data
}

export async function adminReset(): Promise<any> {
  const { data } = await client.post<APIResponse<any>>('/admin/reset')
  return data.data
}
