export type ExplorerNodeType = 'issue' | 'component' | 'agent' | 'policy' | 'pr' | 'code'

export type EdgeRelation = 'component' | 'dependency' | 'code' | 'agent' | 'pr'

export interface InspectorField {
  label: string
  value: string
}

export interface InspectorLink {
  label: string
  kind: 'route' | 'issue' | 'url'
  value: string
}

export interface BlastRadiusStats {
  total: number
  direct: number
  maxDepth: number
  critical: number
  high: number
}

export interface EdgeInspectorInfo {
  relation: EdgeRelation | string
  fromLabel: string
  toLabel: string
  weight: number
  inCycle: boolean
}

export interface InspectorPayload {
  kind: 'node' | 'edge'
  type: ExplorerNodeType | string
  title: string
  subtitle?: string
  badge?: string
  fields: InspectorField[]
  blast?: BlastRadiusStats
  edge?: EdgeInspectorInfo
  links: InspectorLink[]
}

export interface TraceSelectOption {
  id: string
  label: string
}
