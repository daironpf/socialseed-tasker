export type AuditAction = 'status' | 'priority' | 'assignment' | 'agent' | 'system' | 'hitl' | 'comment' | 'label'

export interface AuditEntry {
  id: string
  issueId: string
  action: AuditAction
  actor: string
  actorAvatar: string
  actorType: 'human' | 'agent' | 'system'
  description: string
  details?: Record<string, any>
  timestamp: string
}

export const ACTION_CONFIG: Record<AuditAction, { color: string; bg: string; icon: string }> = {
  status: { color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30', icon: 'S' },
  priority: { color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900/30', icon: 'P' },
  assignment: { color: 'text-green-600 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900/30', icon: 'A' },
  agent: { color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-100 dark:bg-purple-900/30', icon: '🤖' },
  system: { color: 'text-gray-600 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-900/30', icon: '⚙' },
  hitl: { color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-100 dark:bg-amber-900/30', icon: '!' },
  comment: { color: 'text-cyan-600 dark:text-cyan-400', bg: 'bg-cyan-100 dark:bg-cyan-900/30', icon: '💬' },
  label: { color: 'text-pink-600 dark:text-pink-400', bg: 'bg-pink-100 dark:bg-pink-900/30', icon: '🏷' },
}
