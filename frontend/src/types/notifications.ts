export type NotificationCategory = 'mention' | 'hitl' | 'constraint_violation' | 'agent_failure' | 'sla'

export type SeverityGroup = 'emergency' | 'warning' | 'info'

export const SEVERITY_GROUPS: Record<SeverityGroup, NotificationCategory[]> = {
  emergency: ['constraint_violation', 'agent_failure', 'sla'],
  warning: ['hitl'],
  info: ['mention'],
}

export interface AppNotification {
  id: string
  title: string
  message: string
  category: NotificationCategory
  read: boolean
  requiresAction: boolean
  linkTo?: { name: string; params?: Record<string, string> }
  hitlRequestId?: string
  createdAt: string
}

export const CATEGORY_CONFIG: Record<NotificationCategory, { icon: string; color: string; label: string }> = {
  mention: { icon: '@', color: 'text-blue-600 dark:text-blue-400', label: 'Mention' },
  hitl: { icon: '!', color: 'text-amber-600 dark:text-amber-400', label: 'HITL Request' },
  constraint_violation: { icon: 'X', color: 'text-red-600 dark:text-red-400', label: 'Violation' },
  agent_failure: { icon: '?', color: 'text-purple-600 dark:text-purple-400', label: 'Agent Failure' },
  sla: { icon: 'T', color: 'text-rose-600 dark:text-rose-400', label: 'SLA' },
}
