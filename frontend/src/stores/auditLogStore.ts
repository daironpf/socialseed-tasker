import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  AuditLogEntry,
  AuditLogEventType,
  AuditLogFilters,
  AuditLogSeverity,
  AuditChainBlock,
} from '@/types/auditLog'
import { AUDIT_EVENT_TYPES, AUDIT_SEVERITIES } from '@/types/auditLog'

const HUMAN_ACTORS = ['alice', 'bob', 'carol', 'dave', 'erin']
const AGENT_ACTORS = ['deploy-agent', 'data-agent', 'ops-agent']
const RESOURCES = [
  'ISS-1042', 'ISS-1043', 'ISS-1051', 'ISS-1067', 'ISS-1088',
  'CMP-auth-service', 'CMP-data-pipeline', 'POL-gdpr-export', 'ORG-main',
]
const IPS = ['10.0.1.42', '10.0.1.77', '192.168.5.10', '172.16.0.8', '10.0.2.15']

const EVENT_WEIGHTS: Array<{ type: AuditLogEventType; severity: AuditLogSeverity; weight: number }> = [
  { type: 'status_change', severity: 'LOW', weight: 22 },
  { type: 'agent_run', severity: 'LOW', weight: 18 },
  { type: 'login', severity: 'LOW', weight: 14 },
  { type: 'hitl_decision', severity: 'MEDIUM', weight: 12 },
  { type: 'export', severity: 'MEDIUM', weight: 9 },
  { type: 'pii_redaction', severity: 'HIGH', weight: 8 },
  { type: 'policy_violation', severity: 'HIGH', weight: 9 },
  { type: 'governance_override', severity: 'CRITICAL', weight: 8 },
]

function seededRandom(seed: number): () => number {
  let state = seed >>> 0
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0
    return state / 0xffffffff
  }
}

function pick<T>(rand: () => number, items: T[]): T {
  return items[Math.floor(rand() * items.length)]
}

function weightedEvent(rand: () => number): { type: AuditLogEventType; severity: AuditLogSeverity } {
  const total = EVENT_WEIGHTS.reduce((sum, e) => sum + e.weight, 0)
  let roll = rand() * total
  for (const entry of EVENT_WEIGHTS) {
    roll -= entry.weight
    if (roll <= 0) return { type: entry.type, severity: entry.severity }
  }
  return { type: 'status_change', severity: 'LOW' }
}

function actionFor(type: AuditLogEventType, rand: () => number): string {
  switch (type) {
    case 'status_change': return pick(rand, ['OPEN → IN_PROGRESS', 'IN_PROGRESS → BLOCKED', 'IN_PROGRESS → CLOSED', 'BLOCKED → IN_PROGRESS'])
    case 'hitl_decision': return pick(rand, ['approve', 'reject', 'modify'])
    case 'policy_violation': return pick(rand, ['unmasked PII in export', 'forbidden dependency', 'schema drift detected'])
    case 'agent_run': return pick(rand, ['task executed', 'context window exceeded → retry', 'tool call: fs.read', 'tool call: neo4j.query'])
    case 'login': return pick(rand, ['password login', 'api key login', 'sso login'])
    case 'export': return pick(rand, ['CSV export', 'JSON export', 'PDF report export'])
    case 'governance_override': return pick(rand, ['permission matrix changed', 'risk level bypassed', 'restriction disabled by admin'])
    case 'pii_redaction': return pick(rand, ['email masked', 'credit card masked', 'api key masked'])
  }
}

function generateEntries(): AuditLogEntry[] {
  const rand = seededRandom(20260924)
  const now = Date.now()
  const entries: AuditLogEntry[] = []
  const count = 84
  for (let i = 0; i < count; i++) {
    const { type, severity } = weightedEvent(rand)
    const actor = type === 'agent_run' || type === 'pii_redaction'
      ? pick(rand, AGENT_ACTORS)
      : pick(rand, rand() > 0.75 ? AGENT_ACTORS : HUMAN_ACTORS)
    const actorType: AuditLogEntry['actorType'] = actor === 'system'
      ? 'system'
      : AGENT_ACTORS.includes(actor)
        ? 'agent'
        : 'human'
    const timestamp = new Date(now - Math.floor((i / count) * 30 * 24 * 3600 * 1000) - Math.floor(rand() * 3600 * 1000)).toISOString()
    entries.push({
      id: `aud-${String(i + 1).padStart(4, '0')}`,
      timestamp,
      actor,
      actorType,
      agent: actorType === 'agent' ? actor : undefined,
      eventType: type,
      severity,
      resource: pick(rand, RESOURCES),
      action: actionFor(type, rand),
      ip: actorType === 'human' ? pick(rand, IPS) : undefined,
      details: {
        session: `sess-${Math.floor(rand() * 0xffffff).toString(16).padStart(6, '0')}`,
      },
    })
  }
  return entries.sort((a, b) => b.timestamp.localeCompare(a.timestamp))
}

function mockHash(input: string): string {
  let h1 = 0x811c9dc5
  let h2 = 0x01000193
  for (let i = 0; i < input.length; i++) {
    h1 = (h1 ^ input.charCodeAt(i)) * 16777619
    h2 = (h2 + input.charCodeAt(i) * (i + 7)) >>> 0
  }
  return (h1 >>> 0).toString(16).padStart(8, '0') + (h2 >>> 0).toString(16).padStart(8, '0')
}

export const useAuditLogStore = defineStore('auditLog', () => {
  const entries = ref<AuditLogEntry[]>(generateEntries())
  const filters = ref<AuditLogFilters>({
    dateFrom: '',
    dateTo: '',
    actor: '',
    agent: '',
    eventType: '',
    severity: '',
    search: '',
  })

  const filteredEntries = computed(() => {
    const f = filters.value
    const q = f.search.trim().toLowerCase()
    return entries.value.filter(entry => {
      if (f.dateFrom && entry.timestamp.slice(0, 10) < f.dateFrom) return false
      if (f.dateTo && entry.timestamp.slice(0, 10) > f.dateTo) return false
      if (f.actor && entry.actor !== f.actor) return false
      if (f.agent && entry.agent !== f.agent) return false
      if (f.eventType && entry.eventType !== f.eventType) return false
      if (f.severity && entry.severity !== f.severity) return false
      if (q) {
        const haystack = `${entry.actor} ${entry.resource} ${entry.action} ${entry.eventType} ${entry.ip ?? ''}`.toLowerCase()
        if (!haystack.includes(q)) return false
      }
      return true
    })
  })

  const severityCounts = computed<Record<AuditLogSeverity, number>>(() => {
    const counts: Record<AuditLogSeverity, number> = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 }
    for (const entry of filteredEntries.value) counts[entry.severity]++
    return counts
  })

  const actors = computed(() => Array.from(new Set(entries.value.map(e => e.actor))).sort())
  const agents = computed(() => Array.from(new Set(entries.value.map(e => e.agent).filter(Boolean) as string[])).sort())

  const chain = computed<AuditChainBlock[]>(() => {
    const BATCH = 12
    const blocks: AuditChainBlock[] = []
    let previousHash = '0000000000000000'
    const ordered = filteredEntries.value
    for (let i = 0; i < ordered.length; i += BATCH) {
      const batch = ordered.slice(i, i + BATCH)
      const seed = batch.map(e => e.id).join('|')
      const hash = mockHash(seed + previousHash)
      blocks.push({
        id: `block-${blocks.length + 1}`,
        label: `#${blocks.length + 1}`,
        count: batch.length,
        hash,
        previousHash,
        timestamp: batch[batch.length - 1]?.timestamp ?? '',
        verified: true,
      })
      previousHash = hash
    }
    return blocks
  })

  function setFilter<K extends keyof AuditLogFilters>(key: K, value: AuditLogFilters[K]) {
    filters.value[key] = value
  }

  function clearFilters() {
    filters.value = {
      dateFrom: '',
      dateTo: '',
      actor: '',
      agent: '',
      eventType: '',
      severity: '',
      search: '',
    }
  }

  function exportRows() {
    return filteredEntries.value.map(entry => ({
      id: entry.id,
      timestamp: entry.timestamp,
      actor: entry.actor,
      actor_type: entry.actorType,
      agent: entry.agent ?? '',
      event_type: entry.eventType,
      severity: entry.severity,
      resource: entry.resource,
      action: entry.action,
      ip: entry.ip ?? '',
    }))
  }

  return {
    entries,
    filters,
    filteredEntries,
    severityCounts,
    actors,
    agents,
    chain,
    setFilter,
    clearFilters,
    exportRows,
    AUDIT_EVENT_TYPES,
    AUDIT_SEVERITIES,
  }
})
