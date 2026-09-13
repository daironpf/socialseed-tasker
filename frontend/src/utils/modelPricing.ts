export interface ModelPricing {
  model: string
  provider: string
  promptPricePer1k: number
  completionPricePer1k: number
}

export const MODEL_PRICING: Record<string, ModelPricing> = {
  'claude-3.5-sonnet': {
    model: 'Claude 3.5 Sonnet',
    provider: 'Anthropic',
    promptPricePer1k: 0.003,
    completionPricePer1k: 0.015,
  },
  'claude-3-opus': {
    model: 'Claude 3 Opus',
    provider: 'Anthropic',
    promptPricePer1k: 0.015,
    completionPricePer1k: 0.075,
  },
  'gpt-4-turbo': {
    model: 'GPT-4 Turbo',
    provider: 'OpenAI',
    promptPricePer1k: 0.01,
    completionPricePer1k: 0.03,
  },
  'gpt-4o': {
    model: 'GPT-4o',
    provider: 'OpenAI',
    promptPricePer1k: 0.005,
    completionPricePer1k: 0.015,
  },
  'gemini-pro': {
    model: 'Gemini Pro',
    provider: 'Google',
    promptPricePer1k: 0.00025,
    completionPricePer1k: 0.0005,
  },
  'llama-3': {
    model: 'Llama 3',
    provider: 'Meta',
    promptPricePer1k: 0.0005,
    completionPricePer1k: 0.0008,
  },
}

export function calculateCost(
  model: string,
  promptTokens: number,
  completionTokens: number
): number {
  const pricing = MODEL_PRICING[model]
  if (!pricing) return 0
  return (promptTokens / 1000) * pricing.promptPricePer1k +
    (completionTokens / 1000) * pricing.completionPricePer1k
}

export function formatCost(cost: number): string {
  if (cost < 0.01) return '<$0.01'
  return `$${cost.toFixed(2)}`
}

export function formatTokens(tokens: number): string {
  if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`
  return String(tokens)
}
