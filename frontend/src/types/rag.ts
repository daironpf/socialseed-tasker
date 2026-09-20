export interface RAGContextNode {
  id: string
  label: string
  type: 'Issue' | 'Component' | 'Function' | 'Class' | 'Module' | 'Interface'
  relevance: number
}

export interface RAGContextEdge {
  from: string
  to: string
  type: string
}

export interface RAGResult {
  id: string
  issueId: string
  issueTitle: string
  issueStatus: string
  similarity: number
  solutionSummary: string
  solutionDate: string
  component: string
  keywords: string[]
  contextNodes: RAGContextNode[]
  contextEdges: RAGContextEdge[]
}

export interface RAGSearchQuery {
  query: string
  threshold: number
  maxResults: number
}

export interface RAGSearchResponse {
  query: string
  results: RAGResult[]
  totalMatches: number
  searchTimeMs: number
  embeddingModel: string
}

export interface RAGMetrics {
  totalEmbeddings: number
  avgSimilarity: number
  topComponents: { name: string; count: number }[]
  lastIndexedAt: string | null
}
