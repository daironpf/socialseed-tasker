import { describe, it, expect } from 'vitest'
import type { GraphData, EngineLimits } from '@/utils/ruleEngine'
import { DEFAULT_ENGINE_LIMITS, evaluateRule, parseRuleDsl, validateRuleDsl } from '@/utils/ruleEngine'

const GRAPH: GraphData = {
  nodes: [
    { id: 'n1', title: 'Auth flow', component: 'Frontend', status: 'OPEN', priority: 'CRITICAL', labels: ['ui'] },
    { id: 'n2', title: 'REST API', component: 'Backend', status: 'BLOCKED', priority: 'HIGH', labels: ['api'] },
    { id: 'n3', title: 'Neo4j driver', component: 'Database', status: 'OPEN', priority: 'MEDIUM', labels: ['db', 'legacy'] },
    { id: 'n4', title: 'Mock API', component: 'Backend', status: 'BLOCKED', priority: 'LOW', labels: [] },
  ],
  edges: [
    { from: 'n1', to: 'n2', type: 'DEPENDS_ON' },
    { from: 'n2', to: 'n3', type: 'DEPENDS_ON' },
    { from: 'n4', to: 'n4', type: 'DEPENDS_ON' },
  ],
}

function limits(overrides: Partial<EngineLimits> = {}): EngineLimits {
  return { ...DEFAULT_ENGINE_LIMITS, ...overrides }
}

function nodeRule(code: string, overrides: Record<string, unknown> = {}) {
  return { name: 'Test rule', code, format: 'json' as const, severity: 'HARD' as const, ...overrides }
}

function nestedAny(depth: number): unknown {
  let cond: unknown = { op: 'compare', field: 'status', cmp: '=', value: 'OPEN' }
  for (let i = 0; i < depth; i++) cond = { op: 'any', conditions: [cond] }
  return cond
}

describe('validateRuleDsl', () => {
  it('accepts a valid node rule', () => {
    const dsl = validateRuleDsl({
      version: 1,
      kind: 'node',
      match: { op: 'compare', field: 'status', cmp: '=', value: 'OPEN' },
      message: 'blocked',
      blastRadiusDepth: 2,
    })
    expect(dsl).not.toBeNull()
    expect(dsl?.kind).toBe('node')
    expect(dsl?.blastRadiusDepth).toBe(2)
  })

  it('rejects invalid rules', () => {
    expect(validateRuleDsl({ kind: 'node' })).toBeNull()
    expect(validateRuleDsl({ kind: 'unknown', match: { op: 'sameNode' } })).toBeNull()
    expect(validateRuleDsl({ kind: 'edge', match: { op: 'compare', field: 'status', cmp: '==', value: 1 } })).toBeNull()
    expect(validateRuleDsl(null)).toBeNull()
  })

  it('rejects conditions nested beyond the depth limit', () => {
    expect(validateRuleDsl({ version: 1, kind: 'node', match: nestedAny(20) })).toBeNull()
  })
})

describe('parseRuleDsl', () => {
  it('parses JSON rules', () => {
    const dsl = parseRuleDsl('{"version":1,"kind":"edge","match":{"op":"sameNode"}}', 'json')
    expect(dsl?.kind).toBe('edge')
    expect(dsl?.match.op).toBe('sameNode')
  })

  it('returns null for invalid JSON', () => {
    expect(parseRuleDsl('{ not json', 'json')).toBeNull()
    expect(parseRuleDsl('', 'json')).toBeNull()
  })

  it('interprets legacy cypher self-dependency', () => {
    const dsl = parseRuleDsl('MATCH (i:Issue)-[r:DEPENDS_ON]->(i)\nRETURN i.name', 'cypher')
    expect(dsl?.kind).toBe('edge')
    expect(dsl?.match).toEqual({ op: 'sameNode' })
  })

  it('interprets legacy cypher dependency count', () => {
    const dsl = parseRuleDsl('MATCH (c)-[]->(d) WITH c, COUNT(d) AS depCount WHERE depCount > 5', 'cypher')
    expect(dsl?.match).toEqual({ op: 'dependencyCount', direction: 'out', cmp: '>', value: 5 })
  })

  it('interprets legacy cypher layer constraints', () => {
    const single = parseRuleDsl("MATCH (n) WHERE n.layer = 'frontend' RETURN n", 'cypher')
    expect(single?.match).toEqual({ op: 'compare', field: 'component', cmp: '=', value: 'frontend' })

    const edge = parseRuleDsl("MATCH (a)-[]->(b) WHERE a.layer = 'frontend' AND b.layer = 'backend'", 'cypher')
    expect(edge?.kind).toBe('edge')
    expect(edge?.match.op).toBe('all')
  })

  it('interprets legacy yaml constraints', () => {
    const contains = parseRuleDsl('field: labels\ncondition: contains\nvalue: priority', 'yaml')
    expect(contains?.match).toEqual({ op: 'contains', field: 'labels', value: 'priority', negate: true })

    const notContains = parseRuleDsl('field: labels\ncondition: not_contains\nvalue: legacy', 'yaml')
    expect(notContains?.match).toEqual({ op: 'contains', field: 'labels', value: 'legacy', negate: false })

    const equals = parseRuleDsl('field: status\ncondition: equals\nvalue: OPEN', 'yaml')
    expect(equals?.match.op).toBe('not')

    const notEquals = parseRuleDsl('field: status\ncondition: not_equals\nvalue: OPEN', 'yaml')
    expect(notEquals?.match).toEqual({ op: 'compare', field: 'status', cmp: '!=', value: 'OPEN' })

    expect(parseRuleDsl('field: status', 'yaml')).toBeNull()
  })
})

describe('evaluateRule', () => {
  it('matches node rules and reports violations, matched nodes and blast radius', () => {
    const result = evaluateRule(nodeRule('{"version":1,"kind":"node","match":{"op":"compare","field":"status","cmp":"=","value":"BLOCKED"}}'), GRAPH)
    expect(result.status).toBe('completed')
    expect(result.totalNodesChecked).toBe(4)
    expect(result.matchedNodes.map(n => n.id)).toEqual(['n2', 'n4'])
    expect(result.violations).toHaveLength(2)
    expect(result.violations[0].severity).toBe('HARD')
    expect(result.blastRadius).toEqual({ direct: 2, total: 2, maxDepth: 2, critical: 1, high: 0 })
  })

  it('matches edge rules for self dependencies', () => {
    const result = evaluateRule(
      nodeRule('{"version":1,"kind":"edge","match":{"op":"sameNode"}}', { format: 'cypher', code: 'MATCH (i:Issue)-[r:DEPENDS_ON]->(i)' }),
      GRAPH,
    )
    expect(result.status).toBe('completed')
    expect(result.totalEdgesChecked).toBe(3)
    expect(result.matchedNodes.map(n => n.id)).toEqual(['n4'])
    expect(result.violations).toHaveLength(1)
    expect(result.violations[0].edgeFrom).toBe('Mock API')
  })

  it('compares array fields against scalar values', () => {
    const result = evaluateRule(nodeRule('{"version":1,"kind":"node","match":{"op":"compare","field":"labels","cmp":"=","value":"db"}}'), GRAPH)
    expect(result.matchedNodes.map(n => n.id)).toEqual(['n3'])
  })

  it('negates array comparisons with !=', () => {
    const result = evaluateRule(nodeRule('{"version":1,"kind":"node","match":{"op":"compare","field":"labels","cmp":"!=","value":"db"}}'), GRAPH)
    expect(result.matchedNodes.map(n => n.id)).toEqual(['n1', 'n2', 'n4'])
  })

  it('evaluates dependency counts', () => {
    const code = '{"version":1,"kind":"node","match":{"op":"dependencyCount","direction":"both","cmp":">","value":1}}'
    const result = evaluateRule(nodeRule(code), GRAPH)
    expect(result.matchedNodes.map(n => n.id)).toEqual(['n2', 'n4'])
  })

  it('evaluates composite all/any/not conditions', () => {
    const code = JSON.stringify({
      version: 1,
      kind: 'node',
      match: {
        op: 'all',
        conditions: [
          { op: 'any', conditions: [
            { op: 'compare', field: 'status', cmp: '=', value: 'OPEN' },
            { op: 'compare', field: 'status', cmp: '=', value: 'BLOCKED' },
          ] },
          { op: 'not', condition: { op: 'contains', field: 'labels', value: 'api' } },
        ],
      },
    })
    const result = evaluateRule(nodeRule(code), GRAPH)
    expect(result.matchedNodes.map(n => n.id)).toEqual(['n1', 'n3', 'n4'])
  })

  it('renders custom messages with placeholders', () => {
    const code = '{"version":1,"kind":"node","match":{"op":"compare","field":"status","cmp":"=","value":"OPEN"},"message":"{title} is open in {component}"}'
    const result = evaluateRule(nodeRule(code), GRAPH)
    expect(result.violations[0].message).toBe('Auth flow is open in Frontend')
  })

  it('returns failed with unrecognizedRule when the code cannot be parsed', () => {
    const result = evaluateRule(nodeRule('not a rule'), GRAPH)
    expect(result.status).toBe('failed')
    expect(result.error).toBe('unrecognizedRule')
    expect(result.violations).toHaveLength(0)
  })

  it('returns failed when conditions exceed the depth limit', () => {
    const code = JSON.stringify({ version: 1, kind: 'node', match: nestedAny(20) })
    const result = evaluateRule(nodeRule(code), GRAPH)
    expect(result.status).toBe('failed')
    expect(result.error).toBe('unrecognizedRule')
  })

  it('truncates evaluation when maxNodes is exceeded', () => {
    const code = '{"version":1,"kind":"node","match":{"op":"compare","field":"status","cmp":"=","value":"OPEN"}}'
    const result = evaluateRule(nodeRule(code), GRAPH, limits({ maxNodes: 2 }))
    expect(result.totalNodesChecked).toBe(2)
    expect(result.truncated).toBe(true)
  })

  it('truncates when the evaluation budget is exhausted', () => {
    const code = JSON.stringify({
      version: 1,
      kind: 'node',
      match: {
        op: 'all',
        conditions: [
          { op: 'compare', field: 'status', cmp: '=', value: 'OPEN' },
          { op: 'compare', field: 'priority', cmp: '=', value: 'MEDIUM' },
        ],
      },
    })
    const result = evaluateRule(nodeRule(code), GRAPH, limits({ maxConditionEvaluations: 1 }))
    expect(result.status).toBe('completed')
    expect(result.truncated).toBe(true)
    expect(result.matchedNodes).toHaveLength(0)
  })

  it('skips the blast radius when depth is zero', () => {
    const code = '{"version":1,"kind":"node","match":{"op":"compare","field":"status","cmp":"=","value":"BLOCKED"},"blastRadiusDepth":0}'
    const result = evaluateRule(nodeRule(code), GRAPH)
    expect(result.blastRadius).toBeNull()
    expect(result.violations).toHaveLength(2)
  })

  it('caps the blast radius depth at the engine limit', () => {
    const code = '{"version":1,"kind":"node","match":{"op":"compare","field":"status","cmp":"=","value":"BLOCKED"},"blastRadiusDepth":99}'
    const result = evaluateRule(nodeRule(code), GRAPH, limits({ maxBlastDepth: 1 }))
    expect(result.blastRadius?.maxDepth).toBeLessThanOrEqual(1)
  })
})
