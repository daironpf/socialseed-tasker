export interface AgentLimits {
  maxTokensPerRun: number
  timeoutSeconds: number
  maxRisk: 'LOW' | 'MEDIUM' | 'HIGH'
}

export interface AgentProfile {
  id: string
  name: string
  role: string
  avatar: string
  model: string
  systemPrompt: string
  tools: string[]
  limits: AgentLimits
  enabled: boolean
  createdAt: string
  lastUsedAt?: string
}

export const AGENT_MODELS = [
  'gpt-4o',
  'claude-3.5-sonnet',
  'llama-3-70b',
  'gemini-1.5-pro',
  'mistral-large',
]

export const AGENT_TOOLS = [
  'code_search',
  'fs_read',
  'fs_write',
  'neo4j_query',
  'web_search',
  'github_pr',
  'test_runner',
  'docs_writer',
  'shell',
] as const

export const PROMPT_VARIABLES = ['{{issue}}', '{{component}}', '{{project}}', '{{constraints}}']

export const DEFAULT_LIMITS: AgentLimits = {
  maxTokensPerRun: 8000,
  timeoutSeconds: 120,
  maxRisk: 'MEDIUM',
}
