import client from './client'
import type { APIResponse } from '@/types'

/** One row of `GET /skills` (issue #572): `id` is the slug, free values are upserted on save. */
export interface SkillCatalogItem {
  id: string
  name: string
}

/** One row of `GET /tools` (issue #572): canonical snake_case slugs, validated with 422 (#564). */
export interface ToolCatalogItem {
  id: string
  name: string
  description?: string | null
}

// Catalogs change rarely (seed + upserts): cache per short window so opening
// several modals hits the API once; failures are never cached (#572).
const CACHE_TTL_MS = 60_000
let skillsCache: { at: number; items: SkillCatalogItem[] } | null = null
let toolsCache: { at: number; items: ToolCatalogItem[] } | null = null

export function resetCatalogsCache(): void {
  skillsCache = null
  toolsCache = null
}

export async function fetchSkills(): Promise<SkillCatalogItem[]> {
  if (skillsCache && Date.now() - skillsCache.at < CACHE_TTL_MS) return skillsCache.items
  // Degrade silently: the pickers keep free-text chips without suggestions (#572).
  const { data } = await client.get<APIResponse<SkillCatalogItem[]>>('/skills', {
    suppressErrorToast: true,
  })
  const items = data.data ?? []
  skillsCache = { at: Date.now(), items }
  return items
}

export async function fetchTools(): Promise<ToolCatalogItem[]> {
  if (toolsCache && Date.now() - toolsCache.at < CACHE_TTL_MS) return toolsCache.items
  // Degrade silently: the pickers keep the AGENT_TOOLS local fallback (#572).
  const { data } = await client.get<APIResponse<ToolCatalogItem[]>>('/tools', {
    suppressErrorToast: true,
  })
  const items = data.data ?? []
  toolsCache = { at: Date.now(), items }
  return items
}
