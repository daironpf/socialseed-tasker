import client from './client'

export interface RAGSearchResultItem {
  id: string
  content: string
  sourceType: string
  sourceId: string
  score: number
  content_length?: number
}

export interface RAGSearchRaw {
  results?: RAGSearchResultItem[]
  count?: number
  error?: string
}

export interface RAGStatsRaw {
  total?: number
  by_type?: Record<string, number>
  error?: string
}

export async function searchRag(
  query: string,
  limit: number,
  threshold: number,
): Promise<RAGSearchRaw> {
  const { data } = await client.post<RAGSearchRaw>('/rag/search', null, {
    params: { query, limit, threshold },
  })
  return data ?? {}
}

export async function getRagStats(): Promise<RAGStatsRaw> {
  const { data } = await client.get<RAGStatsRaw>('/rag/stats')
  return data ?? {}
}
