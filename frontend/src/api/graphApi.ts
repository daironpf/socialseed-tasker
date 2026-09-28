import client from './client'
import type { APIResponse, Component, Issue } from '@/types'
import type { GraphData, GraphEdgeData, GraphNodeData } from '@/utils/ruleEngine'

interface DependencyGraphPayload {
  nodes: Array<{ id: string; title: string; component?: string | null; status?: string; priority?: string }>
  edges: Array<{ from_node: string; to_node: string }>
}

export async function fetchDependencyGraph(): Promise<GraphData | null> {
  try {
    const { data } = await client.get<APIResponse<DependencyGraphPayload>>('/graph/dependencies')
    const payload = data.data
    if (!payload || !Array.isArray(payload.nodes) || !Array.isArray(payload.edges)) return null
    const nodes: GraphNodeData[] = payload.nodes.map(node => ({
      id: node.id,
      title: node.title,
      component: node.component ?? null,
      status: node.status,
      priority: node.priority,
      labels: [],
    }))
    const edges: GraphEdgeData[] = payload.edges.map(edge => ({
      from: edge.from_node,
      to: edge.to_node,
      type: 'DEPENDS_ON',
    }))
    return { nodes, edges }
  } catch {
    return null
  }
}

export function buildGraphFromIssues(issues: Issue[], components: Component[]): GraphData {
  const componentNames = new Map(components.map(component => [component.id, component.name]))
  const nodes: GraphNodeData[] = issues.map(issue => ({
    id: issue.id,
    title: issue.title,
    component: componentNames.get(issue.component_id) ?? null,
    status: issue.status,
    priority: issue.priority,
    labels: issue.labels ?? [],
  }))
  const edges: GraphEdgeData[] = []
  for (const issue of issues) {
    for (const depId of issue.dependencies ?? []) {
      edges.push({ from: issue.id, to: depId, type: 'DEPENDS_ON' })
    }
  }
  return { nodes, edges }
}
