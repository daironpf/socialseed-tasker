export type ChatMessageType = 'text' | 'code' | 'agent_action' | 'system' | 'file_share'

export type ParticipantType = 'human' | 'agent' | 'system'

export interface ChatParticipant {
  id: string
  username: string
  avatar: string
  type: ParticipantType
  isOnline?: boolean
  lastSeen?: string
}

export interface ChatMessage {
  id: string
  conversationId: string
  senderId: string
  senderName: string
  senderAvatar: string
  senderType: ParticipantType
  content: string
  type: ChatMessageType
  metadata?: {
    language?: string
    filename?: string
    action?: string
    issueId?: string
  }
  reactions?: Record<string, string[]>
  readBy: string[]
  createdAt: string
  updatedAt?: string
}

export interface Conversation {
  id: string
  type: 'direct' | 'group' | 'agent'
  name: string
  description?: string
  avatar?: string
  participants: ChatParticipant[]
  lastMessage?: ChatMessage
  unreadCount: number
  isPinned: boolean
  createdAt: string
  updatedAt: string
}

export interface TypingUser {
  userId: string
  username: string
  conversationId: string
  startedAt: number
}
