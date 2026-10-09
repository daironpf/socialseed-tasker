import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import {
  loadStudioProfiles,
  saveStudioProfiles,
  mergeStudioAgents,
} from '@/utils/studioAgents'
import type { AgentProfile } from '@/types/agentStudio'
import type { User } from '@/types'

const LS_KEY = 'agent-studio-v1'

function makeProfile(id: string): AgentProfile {
  return {
    id,
    name: id,
    role: 'developer',
    avatar: '🤖',
    model: 'gpt-4o',
    systemPrompt: '',
    tools: [],
    limits: { maxTokensPerRun: 1000, timeoutSeconds: 30, maxRisk: 'LOW' },
    enabled: true,
    createdAt: '2026-10-04T00:00:00Z',
  }
}

function makeUser(id: string): User {
  return {
    id,
    username: id,
    email: `${id}@example.com`,
    role: 'VIEWER',
    type: 'human',
    avatar: '👤',
    skills: [],
    issues_assigned: 0,
    issues_created: 0,
    last_active: '2026-10-04T00:00:00Z',
    is_active: true,
  }
}

describe('studioAgents', () => {
  beforeEach(() => {
    localStorage.removeItem(LS_KEY)
  })

  afterEach(() => {
    localStorage.removeItem(LS_KEY)
  })

  it('returns no demo profiles on a fresh system', () => {
    expect(loadStudioProfiles()).toEqual([])
  })

  it('returns previously saved profiles', () => {
    saveStudioProfiles([makeProfile('agent-studio-1')])
    expect(loadStudioProfiles()).toHaveLength(1)
    expect(loadStudioProfiles()[0].id).toBe('agent-studio-1')
  })

  it('merges saved studio agents into the user list', () => {
    saveStudioProfiles([makeProfile('agent-studio-1')])
    const merged = mergeStudioAgents([makeUser('u-1')])
    expect(merged.map(u => u.id)).toEqual(['u-1', 'agent-studio-1'])
    expect(merged[1].type).toBe('agent')
  })

  it('leaves the user list untouched without saved profiles', () => {
    const users = [makeUser('u-1')]
    expect(mergeStudioAgents(users)).toEqual(users)
  })

  it('never lets a studio profile overwrite a PG id (#565)', () => {
    saveStudioProfiles([makeProfile('pg-agent-uuid')])
    const pgAgent: User = {
      ...makeUser('pg-agent-uuid'),
      type: 'agent',
      username: 'bot-qa-from-pg',
      avatar: '🤖',
    }

    const merged = mergeStudioAgents([pgAgent])

    // No replacement and no duplicate append: the PG card stays authoritative.
    expect(merged).toHaveLength(1)
    expect(merged[0].username).toBe('bot-qa-from-pg')
    expect(merged[0].avatar).toBe('🤖')
  })
})
