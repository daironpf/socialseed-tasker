import type {
  BlastRadiusSummary,
  MatchedNode,
  SandboxRuleFormat,
  SandboxRuleSeverity,
  SimulationViolation,
} from '@/types/sandbox'

export interface GraphNodeData {
  id: string
  title: string
  component?: string | null
  status?: string
  priority?: string
  labels?: string[]
}

export interface GraphEdgeData {
  from: string
  to: string
  type?: string
}

export interface GraphData {
  nodes: GraphNodeData[]
  edges: GraphEdgeData[]
}

export interface EngineLimits {
  maxNodes: number
  maxEdges: number
  timeoutMs: number
  maxBlastDepth: number
  maxConditionDepth: number
  maxConditionEvaluations: number
  maxMatches: number
}

export const DEFAULT_ENGINE_LIMITS: EngineLimits = {
  maxNodes: 5000,
  maxEdges: 20000,
  timeoutMs: 2000,
  maxBlastDepth: 10,
  maxConditionDepth: 16,
  maxConditionEvaluations: 200000,
  maxMatches: 500,
}

export type RuleOperator = '=' | '!=' | '>' | '<' | '>=' | '<='

export type Condition =
  | { op: 'compare'; field: string; cmp: RuleOperator; value: string | number }
  | { op: 'contains'; field: string; value: string; negate?: boolean }
  | { op: 'matches'; field: string; pattern: string; flags?: string }
  | { op: 'dependencyCount'; direction?: 'out' | 'in' | 'both'; cmp: RuleOperator; value: number }
  | { op: 'sameNode' }
  | { op: 'all'; conditions: Condition[] }
  | { op: 'any'; conditions: Condition[] }
  | { op: 'not'; condition: Condition }

export interface RuleDsl {
  version: number
  kind: 'node' | 'edge'
  match: Condition
  message?: string
  blastRadiusDepth?: number
}

export interface EngineResult {
  status: 'completed' | 'failed'
  error?: string
  totalNodesChecked: number
  totalEdgesChecked: number
  matchedNodes: MatchedNode[]
  violations: SimulationViolation[]
  blastRadius: BlastRadiusSummary | null
  truncated: boolean
  durationMs: number
}

export interface RuleEvaluationTarget {
  name: string
  code: string
  format: SandboxRuleFormat
  severity: SandboxRuleSeverity
}

interface NodeCtx {
  id: string
  title: string
  component: string
  status: string
  priority: string
  labels: string[]
  dependencyCount: number
  dependentCount: number
}

interface EvalState {
  startedAt: number
  limits: EngineLimits
  conditionEvaluations: number
  timedOut: boolean
  budgetExhausted: boolean
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isRuleOperator(value: unknown): value is RuleOperator {
  return value === '=' || value === '!=' || value === '>' || value === '<' || value === '>=' || value === '<='
}

function validateCondition(raw: unknown, depth: number, limits: EngineLimits): Condition | null {
  if (depth > limits.maxConditionDepth || !isRecord(raw) || typeof raw.op !== 'string') return null
  switch (raw.op) {
    case 'compare':
      return typeof raw.field === 'string' && isRuleOperator(raw.cmp) && (typeof raw.value === 'string' || typeof raw.value === 'number')
        ? { op: 'compare', field: raw.field, cmp: raw.cmp, value: raw.value }
        : null
    case 'matches':
      return typeof raw.field === 'string' && typeof raw.pattern === 'string'
        ? { op: 'matches', field: raw.field, pattern: raw.pattern, flags: typeof raw.flags === 'string' ? raw.flags : undefined }
        : null
    case 'dependencyCount':
      return isRuleOperator(raw.cmp) && typeof raw.value === 'number'
        ? {
            op: 'dependencyCount',
            direction: raw.direction === 'in' || raw.direction === 'both' ? raw.direction : 'out',
            cmp: raw.cmp,
            value: raw.value,
          }
        : null
    case 'sameNode':
      return { op: 'sameNode' }
    case 'contains':
      return typeof raw.field === 'string' && typeof raw.value === 'string'
        ? { op: 'contains', field: raw.field, value: raw.value, negate: raw.negate === true }
        : null
    case 'all':
    case 'any': {
      if (!Array.isArray(raw.conditions) || raw.conditions.length === 0 || raw.conditions.length > 32) return null
      const conditions: Condition[] = []
      for (const item of raw.conditions) {
        const parsed = validateCondition(item, depth + 1, limits)
        if (!parsed) return null
        conditions.push(parsed)
      }
      return raw.op === 'all' ? { op: 'all', conditions } : { op: 'any', conditions }
    }
    case 'not':
      return isRecord(raw.condition) ? (() => {
        const inner = validateCondition(raw.condition, depth + 1, limits)
        return inner ? { op: 'not', condition: inner } : null
      })() : null
    default:
      return null
  }
}

export function validateRuleDsl(raw: unknown, limits: EngineLimits = DEFAULT_ENGINE_LIMITS): RuleDsl | null {
  if (!isRecord(raw) || (raw.kind !== 'node' && raw.kind !== 'edge')) return null
  const match = validateCondition(raw.match, 0, limits)
  if (!match) return null
  const depth = typeof raw.blastRadiusDepth === 'number' ? raw.blastRadiusDepth : undefined
  return {
    version: typeof raw.version === 'number' ? raw.version : 1,
    kind: raw.kind,
    match,
    message: typeof raw.message === 'string' ? raw.message : undefined,
    blastRadiusDepth: depth,
  }
}

function interpretCypher(code: string): RuleDsl | null {
  const selfMatch = code.match(/MATCH\s*\(\s*(\w+)[^)]*\)\s*-\[[^\]]*\]->\s*\(\s*\1\s*\)/i)
  if (selfMatch) {
    return { version: 1, kind: 'edge', match: { op: 'sameNode' } }
  }
  const countMatch = code.match(/depCount\s*(>=|<=|!=|==|>|<)\s*(\d+)/i)
  if (countMatch) {
    const cmp = countMatch[1] === '==' ? '=' : (countMatch[1] as RuleOperator)
    return {
      version: 1,
      kind: 'node',
      match: { op: 'dependencyCount', direction: 'out', cmp, value: Number(countMatch[2]) },
    }
  }
  const layerMatches = [...code.matchAll(/(\w+)\.layer\s*=\s*['"]([^'"]+)['"]/gi)]
  if (layerMatches.length >= 2) {
    return {
      version: 1,
      kind: 'edge',
      match: {
        op: 'all',
        conditions: [
          { op: 'compare', field: 'from.component', cmp: '=', value: layerMatches[0][2] },
          { op: 'compare', field: 'to.component', cmp: '=', value: layerMatches[1][2] },
        ],
      },
    }
  }
  if (layerMatches.length === 1) {
    return {
      version: 1,
      kind: 'node',
      match: { op: 'compare', field: 'component', cmp: '=', value: layerMatches[0][2] },
    }
  }
  return null
}

function interpretYaml(code: string): RuleDsl | null {
  const fields: Record<string, string> = {}
  for (const line of code.split('\n')) {
    const kv = line.match(/^\s*([A-Za-z_]+)\s*:\s*(.+?)\s*$/)
    if (kv) fields[kv[1].toLowerCase()] = kv[2].replace(/^["']|["']$/g, '')
  }
  const field = fields.field
  const condition = (fields.condition || '').toLowerCase()
  const value = fields.value
  if (!field || !value) return null
  let match: Condition
  if (condition === 'contains') {
    match = { op: 'contains', field, value, negate: true }
  } else if (condition === 'not_contains') {
    match = { op: 'contains', field, value, negate: false }
  } else if (condition === 'equals') {
    match = { op: 'not', condition: { op: 'compare', field, cmp: '=', value } }
  } else if (condition === 'not_equals') {
    match = { op: 'compare', field, cmp: '!=', value }
  } else {
    match = { op: 'contains', field, value, negate: true }
  }
  return { version: 1, kind: 'node', match, message: fields.message }
}

export function parseRuleDsl(
  code: string,
  format: SandboxRuleFormat,
  limits: EngineLimits = DEFAULT_ENGINE_LIMITS,
): RuleDsl | null {
  const trimmed = code.trim()
  if (!trimmed) return null
  if (format === 'json' || trimmed.startsWith('{')) {
    try {
      return validateRuleDsl(JSON.parse(trimmed), limits)
    } catch {
      return null
    }
  }
  if (format === 'cypher') return interpretCypher(trimmed)
  if (format === 'yaml') return interpretYaml(trimmed)
  return null
}

function normalize(value: unknown): string {
  return String(value ?? '').trim().toLowerCase()
}

function compareValues(actual: unknown, cmp: RuleOperator, expected: string | number): boolean {
  if (Array.isArray(actual) && (cmp === '=' || cmp === '!=')) {
    const needle = normalize(expected)
    const found = actual.some(item => normalize(item) === needle)
    return cmp === '=' ? found : !found
  }
  if (typeof expected === 'number' && actual !== undefined && actual !== null && actual !== '') {
    const num = Number(actual)
    if (!Number.isNaN(num)) {
      switch (cmp) {
        case '=': return num === expected
        case '!=': return num !== expected
        case '>': return num > expected
        case '<': return num < expected
        case '>=': return num >= expected
        case '<=': return num <= expected
      }
    }
  }
  const a = normalize(actual)
  const b = normalize(expected)
  switch (cmp) {
    case '=': return a === b
    case '!=': return a !== b
    case '>': return a > b
    case '<': return a < b
    case '>=': return a >= b
    case '<=': return a <= b
  }
}

function getFieldValue(ctx: NodeCtx | EdgeCtx, field: string): unknown {
  if (field.includes('.')) {
    const [head, ...rest] = field.split('.')
    if (head === 'from' && 'from' in ctx) return getFieldValue((ctx as EdgeCtx).from, rest.join('.'))
    if (head === 'to' && 'to' in ctx) return getFieldValue((ctx as EdgeCtx).to, rest.join('.'))
    return undefined
  }
  if (field in ctx) return (ctx as unknown as Record<string, unknown>)[field]
  if ('from' in ctx) return getFieldValue((ctx as EdgeCtx).from, field)
  return undefined
}

function sanitizeFlags(flags: string | undefined): string {
  if (!flags) return ''
  return [...flags].filter(ch => 'imsu'.includes(ch)).join('')
}

function evaluateCondition(
  cond: Condition,
  ctx: NodeCtx | EdgeCtx,
  state: EvalState,
  depth: number,
): boolean {
  if (state.timedOut || state.budgetExhausted) return false
  if (depth > state.limits.maxConditionDepth) {
    state.budgetExhausted = true
    return false
  }
  state.conditionEvaluations += 1
  if (state.conditionEvaluations > state.limits.maxConditionEvaluations) {
    state.budgetExhausted = true
    return false
  }
  if ((state.conditionEvaluations & 511) === 0 && Date.now() - state.startedAt > state.limits.timeoutMs) {
    state.timedOut = true
    return false
  }
  switch (cond.op) {
    case 'compare':
      return compareValues(getFieldValue(ctx, cond.field), cond.cmp, cond.value)
    case 'contains': {
      const raw = getFieldValue(ctx, cond.field)
      const needle = normalize(cond.value)
      let found = false
      if (Array.isArray(raw)) {
        found = raw.some(item => normalize(item).includes(needle))
      } else {
        found = normalize(raw).includes(needle)
      }
      return cond.negate ? !found : found
    }
    case 'matches': {
      const raw = normalize(getFieldValue(ctx, cond.field))
      try {
        return new RegExp(cond.pattern, sanitizeFlags(cond.flags)).test(raw)
      } catch {
        return false
      }
    }
    case 'dependencyCount': {
      const node = 'from' in ctx ? (ctx as EdgeCtx).from : (ctx as NodeCtx)
      const actual =
        cond.direction === 'in'
          ? node.dependentCount
          : cond.direction === 'both'
            ? node.dependencyCount + node.dependentCount
            : node.dependencyCount
      return compareValues(actual, cond.cmp, cond.value)
    }
    case 'sameNode': {
      if (!('from' in ctx)) return false
      return ctx.from.id === ctx.to.id
    }
    case 'all':
      return cond.conditions.every(item => evaluateCondition(item, ctx, state, depth + 1))
    case 'any':
      return cond.conditions.some(item => evaluateCondition(item, ctx, state, depth + 1))
    case 'not':
      return !evaluateCondition(cond.condition, ctx, state, depth + 1)
  }
}

interface EdgeCtx {
  from: NodeCtx
  to: NodeCtx
  type: string
}

function buildNodeCtx(
  node: GraphNodeData,
  outDegree: Map<string, number>,
  inDegree: Map<string, number>,
): NodeCtx {
  return {
    id: node.id,
    title: node.title,
    component: node.component ?? '',
    status: node.status ?? '',
    priority: node.priority ?? '',
    labels: node.labels ?? [],
    dependencyCount: outDegree.get(node.id) ?? 0,
    dependentCount: inDegree.get(node.id) ?? 0,
  }
}

function renderMessage(
  template: string | undefined,
  fallback: string,
  values: Record<string, string>,
): string {
  let message = template || fallback
  for (const [key, value] of Object.entries(values)) {
    message = message.split(`{${key}}`).join(value)
  }
  return message
}

function computeBlastRadius(
  edges: GraphEdgeData[],
  roots: string[],
  maxDepth: number,
  priorityOf: (id: string) => string | undefined,
): BlastRadiusSummary | null {
  if (roots.length === 0 || maxDepth <= 0) return null
  const adjacency = new Map<string, string[]>()
  for (const edge of edges) {
    if (!adjacency.has(edge.from)) adjacency.set(edge.from, [])
    adjacency.get(edge.from)!.push(edge.to)
    if (!adjacency.has(edge.to)) adjacency.set(edge.to, [])
    adjacency.get(edge.to)!.push(edge.from)
  }
  const rootSet = new Set(roots)
  const visited = new Set<string>(roots)
  let frontier = [...roots]
  let depth = 0
  let direct = 0
  let critical = 0
  let high = 0
  while (frontier.length > 0 && depth < maxDepth) {
    const next: string[] = []
    for (const id of frontier) {
      for (const neighbor of adjacency.get(id) || []) {
        if (visited.has(neighbor)) continue
        visited.add(neighbor)
        if (depth === 0) direct += 1
        const priority = priorityOf(neighbor)
        if (priority === 'CRITICAL') critical += 1
        else if (priority === 'HIGH') high += 1
        next.push(neighbor)
      }
    }
    frontier = next
    depth += 1
  }
  const total = [...visited].filter(id => !rootSet.has(id)).length
  return { direct, total, maxDepth: depth, critical, high }
}

export function evaluateRule(
  rule: RuleEvaluationTarget,
  graph: GraphData,
  limits: EngineLimits = DEFAULT_ENGINE_LIMITS,
): EngineResult {
  const startedAt = Date.now()
  const empty: EngineResult = {
    status: 'completed',
    totalNodesChecked: 0,
    totalEdgesChecked: 0,
    matchedNodes: [],
    violations: [],
    blastRadius: null,
    truncated: false,
    durationMs: 0,
  }
  const dsl = parseRuleDsl(rule.code, rule.format, limits)
  if (!dsl) {
    return {
      ...empty,
      status: 'failed',
      error: 'unrecognizedRule',
      durationMs: Date.now() - startedAt,
    }
  }

  const state: EvalState = {
    startedAt,
    limits,
    conditionEvaluations: 0,
    timedOut: false,
    budgetExhausted: false,
  }

  const outDegree = new Map<string, number>()
  const inDegree = new Map<string, number>()
  for (const edge of graph.edges) {
    outDegree.set(edge.from, (outDegree.get(edge.from) ?? 0) + 1)
    inDegree.set(edge.to, (inDegree.get(edge.to) ?? 0) + 1)
  }
  const nodeById = new Map<string, GraphNodeData>()
  for (const node of graph.nodes) nodeById.set(node.id, node)

  const ctxById = new Map<string, NodeCtx>()
  const ctxOf = (id: string): NodeCtx => {
    const cached = ctxById.get(id)
    if (cached) return cached
    const node = nodeById.get(id)
    const ctx = node
      ? buildNodeCtx(node, outDegree, inDegree)
      : { id, title: id, component: '', status: '', priority: '', labels: [], dependencyCount: 0, dependentCount: 0 }
    ctxById.set(id, ctx)
    return ctx
  }

  const matchedNodes: MatchedNode[] = []
  const matchedIds = new Set<string>()
  const violations: SimulationViolation[] = []
  const seenViolationKeys = new Set<string>()
  let truncated = false
  let totalNodesChecked = 0
  let totalEdgesChecked = 0

  const pushMatch = (ctx: NodeCtx) => {
    if (matchedIds.has(ctx.id)) return
    if (matchedNodes.length >= limits.maxMatches) {
      truncated = true
      return
    }
    matchedIds.add(ctx.id)
    matchedNodes.push({
      id: ctx.id,
      title: ctx.title,
      component: ctx.component || null,
      status: ctx.status,
      priority: ctx.priority,
    })
  }

  const pushViolation = (violation: SimulationViolation) => {
    const key = `${violation.edgeFrom}|${violation.edgeTo}|${violation.constraint}`
    if (seenViolationKeys.has(key)) return
    if (violations.length >= limits.maxMatches) {
      truncated = true
      return
    }
    seenViolationKeys.add(key)
    violations.push(violation)
  }

  if (dsl.kind === 'node') {
    const nodes = graph.nodes.length > limits.maxNodes ? graph.nodes.slice(0, limits.maxNodes) : graph.nodes
    if (nodes.length < graph.nodes.length) truncated = true
    for (const node of nodes) {
      if ((totalNodesChecked & 63) === 0 && Date.now() - startedAt > limits.timeoutMs) {
        state.timedOut = true
        break
      }
      totalNodesChecked += 1
      const ctx = buildNodeCtx(node, outDegree, inDegree)
      ctxById.set(node.id, ctx)
      if (evaluateCondition(dsl.match, ctx, state, 0)) {
        pushMatch(ctx)
        pushViolation({
          edgeFrom: ctx.title,
          edgeTo: ctx.component || ctx.status || ctx.id,
          edgeType: 'NODE',
          constraint: rule.name,
          severity: rule.severity,
          message: renderMessage(dsl.message, `${rule.name}: ${ctx.title}`, {
            title: ctx.title,
            component: ctx.component,
            status: ctx.status,
            priority: ctx.priority,
          }),
        })
      }
      if (state.timedOut || state.budgetExhausted) break
    }
  } else {
    const edges = graph.edges.length > limits.maxEdges ? graph.edges.slice(0, limits.maxEdges) : graph.edges
    if (edges.length < graph.edges.length) truncated = true
    for (const edge of edges) {
      if ((totalEdgesChecked & 63) === 0 && Date.now() - startedAt > limits.timeoutMs) {
        state.timedOut = true
        break
      }
      totalEdgesChecked += 1
      const ctx: EdgeCtx = { from: ctxOf(edge.from), to: ctxOf(edge.to), type: edge.type || 'DEPENDS_ON' }
      if (evaluateCondition(dsl.match, ctx, state, 0)) {
        pushMatch(ctx.from)
        pushViolation({
          edgeFrom: ctx.from.title,
          edgeTo: ctx.to.title,
          edgeType: ctx.type,
          constraint: rule.name,
          severity: rule.severity,
          message: renderMessage(dsl.message, `${rule.name}: ${ctx.from.title} -> ${ctx.to.title}`, {
            from: ctx.from.title,
            to: ctx.to.title,
            title: ctx.from.title,
            component: ctx.from.component,
          }),
        })
      }
      if (state.timedOut || state.budgetExhausted) break
    }
    if (state.timedOut || state.budgetExhausted) truncated = true
  }

  if (state.timedOut || state.budgetExhausted) truncated = true

  const depth = Math.min(Math.max(dsl.blastRadiusDepth ?? 3, 0), limits.maxBlastDepth)
  const blastRadius = computeBlastRadius(graph.edges, [...matchedIds], depth, id => {
    const node = nodeById.get(id)
    return node?.priority
  })

  return {
    status: 'completed',
    totalNodesChecked,
    totalEdgesChecked,
    matchedNodes,
    violations,
    blastRadius,
    truncated,
    durationMs: Date.now() - startedAt,
  }
}
