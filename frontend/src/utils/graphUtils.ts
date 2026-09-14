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
