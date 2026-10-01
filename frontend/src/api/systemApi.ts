import client from './client'
import type { APIResponse, ServiceStatus, SystemHealth, SyncQueue } from '@/types'

const defaultHealth: SystemHealth = {
  status: 'unknown',
  timestamp: '',
  services: { neo4j: { status: 'unknown' }, api: { status: 'unknown' }, workers: { status: 'unknown' } },
  metrics: { total_issues: 0, blocked_issues: 0, total_components: 0, agents_working: 0, total_users: 0, total_constraints: 0, active_constraints: 0 },
}

const defaultSyncQueue: SyncQueue = { pending: 0, queue: [], last_sync_at: '', github_connected: false }

// Raw flat shape served by the real backend `GET /health` (issue #533).
interface RealHealthPayload {
  status?: string
  version?: string
  dependencies?: { neo4j?: string; redis?: string; postgres?: string; httpx?: string }
  dependency_latency_ms?: { neo4j?: number; redis?: number; postgres?: number }
}

function adaptRealHealth(payload: RealHealthPayload): SystemHealth {
  const deps = payload.dependencies ?? {}
  const latency = payload.dependency_latency_ms ?? {}
  const service = (name: 'neo4j' | 'redis' | 'postgres'): ServiceStatus => ({
    status: deps[name] ?? 'not configured',
    latency_ms: latency[name],
  })
  return {
    ...defaultHealth,
    status: payload.status ?? 'unknown',
    services: {
      neo4j: service('neo4j'),
      redis: service('redis'),
      postgres: service('postgres'),
      api: { status: 'running', version: payload.version },
      workers: defaultHealth.services.workers,
    },
    dependencies: {
      neo4j: deps.neo4j ?? 'not configured',
      redis: deps.redis ?? 'not configured',
      postgres: deps.postgres ?? 'not configured',
      httpx: deps.httpx,
    },
    dependency_latency_ms: latency,
  }
}

export async function fetchSystemHealth(): Promise<SystemHealth> {
  const { data } = await client.get<SystemHealth | { data: SystemHealth } | RealHealthPayload>('/health')
  if (data && typeof data === 'object' && 'data' in data && data.data) {
    return data.data
  }
  return adaptRealHealth(data as RealHealthPayload)
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
