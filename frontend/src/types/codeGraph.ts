export type CodeNodeType = 'File' | 'Class' | 'Function'

export interface CodeNode {
  id: string
  name: string
  type: CodeNodeType
  filePath: string
  language: string
  startLine: number
  endLine: number
  componentId: string | null
}

export interface CodeEdge {
  from: string
  to: string
  type: 'CONTAINS' | 'CALLS' | 'AFFECTS' | 'IMPORTS'
  issueId?: string
}

export interface CodeStructureData {
  nodes: CodeNode[]
  edges: CodeEdge[]
}
