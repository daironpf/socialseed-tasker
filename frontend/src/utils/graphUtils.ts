export function wouldCreateCycle(
  edges: Array<{ from: string; to: string }>,
  newFrom: string,
  newTo: string
): boolean {
  const adj = new Map<string, string[]>()
  for (const e of edges) {
    if (!adj.has(e.from)) adj.set(e.from, [])
    adj.get(e.from)!.push(e.to)
  }
  if (!adj.has(newFrom)) adj.set(newFrom, [])
  adj.get(newFrom)!.push(newTo)

  const visited = new Set<string>()
  const stack = [newTo]
  while (stack.length > 0) {
    const node = stack.pop()!
    if (node === newFrom) return true
    if (visited.has(node)) continue
    visited.add(node)
    for (const neighbor of (adj.get(node) || [])) {
      stack.push(neighbor)
    }
  }
  return false
}

export function findPath(
  edges: Array<{ from: string; to: string }>,
  from: string,
  to: string,
  maxDepth = 12
): string[] | null {
  if (from === to) return [from]

  const bfs = (source: string, target: string, reversed: boolean): string[] | null => {
    const adj = new Map<string, string[]>()
    for (const e of edges) {
      const a = reversed ? e.to : e.from
      const b = reversed ? e.from : e.to
      if (!adj.has(a)) adj.set(a, [])
      adj.get(a)!.push(b)
    }
    const prev = new Map<string, string>()
    const visited = new Set<string>([source])
    let queue: string[] = [source]
    let depth = 0
    while (queue.length > 0 && depth < maxDepth) {
      const next: string[] = []
      for (const node of queue) {
        for (const neighbor of adj.get(node) || []) {
          if (visited.has(neighbor)) continue
          visited.add(neighbor)
          prev.set(neighbor, node)
          if (neighbor === target) {
            const path = [neighbor]
            let cur = neighbor
            while (prev.has(cur)) {
              cur = prev.get(cur)!
              path.unshift(cur)
            }
            return path
          }
          next.push(neighbor)
        }
      }
      queue = next
      depth++
    }
    return null
  }

  return bfs(from, to, false) ?? (() => {
    const reversed = bfs(to, from, true)
    return reversed ? [...reversed].reverse() : null
  })()
}

export interface BlastRadius {
  direct: number
  total: number
  maxDepth: number
  critical: number
  high: number
}

export function blastRadius(
  edges: Array<{ from: string; to: string }>,
  rootId: string,
  maxDepth = 5,
  priorityOf?: (id: string) => string | undefined
): BlastRadius {
  const adj = new Map<string, string[]>()
  for (const e of edges) {
    if (!adj.has(e.from)) adj.set(e.from, [])
    if (!adj.has(e.to)) adj.set(e.to, [])
    adj.get(e.from)!.push(e.to)
    adj.get(e.to)!.push(e.from)
  }
  const visited = new Set<string>([rootId])
  let frontier = [rootId]
  let depth = 0
  let critical = 0
  let high = 0
  let direct = 0
  while (frontier.length > 0 && depth < maxDepth) {
    const next: string[] = []
    for (const node of frontier) {
      for (const neighbor of adj.get(node) || []) {
        if (visited.has(neighbor)) continue
        visited.add(neighbor)
        if (depth === 0) direct++
        const priority = priorityOf?.(neighbor)
        if (priority === 'CRITICAL') critical++
        else if (priority === 'HIGH') high++
        next.push(neighbor)
      }
    }
    frontier = next
    depth++
  }
  return {
    direct,
    total: visited.size - 1,
    maxDepth: depth,
    critical,
    high,
  }
}
