import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Conversation, ChatMessage, ChatParticipant, TypingUser } from '@/types/chat'

const CURRENT_USER_ID = 'admin'

const MOCK_PARTICIPANTS: Record<string, ChatParticipant> = {
  admin: { id: 'admin', username: 'Admin', avatar: '👨‍💼', type: 'human', isOnline: true },
  alice: { id: 'alice', username: 'alice', avatar: '👩‍💻', type: 'human', isOnline: true },
  bob: { id: 'bob', username: 'bob', avatar: '👨‍💻', type: 'human', isOnline: false, lastSeen: '2026-09-17T10:30:00Z' },
  charlie: { id: 'charlie', username: 'charlie', avatar: '🧑‍💻', type: 'human', isOnline: true },
  'arch-bot': { id: 'arch-bot', username: 'Arch-Bot', avatar: '🏗️', type: 'agent', isOnline: true },
  'code-reviewer': { id: 'code-reviewer', username: 'CodeReviewer', avatar: '🔍', type: 'agent', isOnline: true },
  'security-auditor': { id: 'security-auditor', username: 'SecurityAuditor', avatar: '🛡️', type: 'agent', isOnline: true },
  system: { id: 'system', username: 'System', avatar: '⚙️', type: 'system', isOnline: true },
}

function h(hours: number): string {
  return new Date(Date.now() - hours * 3600000).toISOString()
}
function m(minutes: number): string {
  return new Date(Date.now() - minutes * 60000).toISOString()
}

const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: 'conv-1',
    type: 'agent',
    name: 'Arch-Bot',
    description: 'Architecture agent assistance',
    participants: [MOCK_PARTICIPANTS.admin, MOCK_PARTICIPANTS['arch-bot']],
    unreadCount: 2,
    isPinned: true,
    createdAt: h(72),
    updatedAt: m(5),
  },
  {
    id: 'conv-2',
    type: 'group',
    name: 'Sprint Planning',
    description: 'Weekly sprint coordination',
    participants: [MOCK_PARTICIPANTS.admin, MOCK_PARTICIPANTS.alice, MOCK_PARTICIPANTS.bob, MOCK_PARTICIPANTS.charlie],
    unreadCount: 0,
    isPinned: true,
    createdAt: h(168),
    updatedAt: h(2),
  },
  {
    id: 'conv-3',
    type: 'direct',
    name: 'alice',
    participants: [MOCK_PARTICIPANTS.admin, MOCK_PARTICIPANTS.alice],
    unreadCount: 3,
    isPinned: false,
    createdAt: h(48),
    updatedAt: m(15),
  },
  {
    id: 'conv-4',
    type: 'agent',
    name: 'CodeReviewer',
    description: 'Code review agent',
    participants: [MOCK_PARTICIPANTS.admin, MOCK_PARTICIPANTS['code-reviewer']],
    unreadCount: 0,
    isPinned: false,
    createdAt: h(24),
    updatedAt: h(1),
  },
  {
    id: 'conv-5',
    type: 'group',
    name: 'ISS-042 War Room',
    description: 'Critical issue coordination',
    participants: [MOCK_PARTICIPANTS.admin, MOCK_PARTICIPANTS.alice, MOCK_PARTICIPANTS.bob, MOCK_PARTICIPANTS['arch-bot']],
    unreadCount: 1,
    isPinned: false,
    createdAt: h(6),
    updatedAt: m(30),
  },
  {
    id: 'conv-6',
    type: 'direct',
    name: 'bob',
    participants: [MOCK_PARTICIPANTS.admin, MOCK_PARTICIPANTS.bob],
    unreadCount: 0,
    isPinned: false,
    createdAt: h(240),
    updatedAt: h(8),
  },
  {
    id: 'conv-7',
    type: 'agent',
    name: 'SecurityAuditor',
    description: 'Security scanning agent',
    participants: [MOCK_PARTICIPANTS.admin, MOCK_PARTICIPANTS['security-auditor']],
    unreadCount: 0,
    isPinned: false,
    createdAt: h(12),
    updatedAt: h(3),
  },
]

const MOCK_MESSAGES: Record<string, ChatMessage[]> = {
  'conv-1': [
    { id: 'msg-1-1', conversationId: 'conv-1', senderId: 'admin', senderName: 'Admin', senderAvatar: '👨‍💼', senderType: 'human', content: 'Hey Arch-Bot, can you analyze the dependency structure of the auth module?', type: 'text', readBy: ['admin', 'arch-bot'], createdAt: h(4) },
    { id: 'msg-1-2', conversationId: 'conv-1', senderId: 'arch-bot', senderName: 'Arch-Bot', senderAvatar: '🏗️', senderType: 'agent', content: 'Sure! I\'ve analyzed the auth module. Here are my findings:\n\n**Key Issues:**\n- Circular dependency between `authStore` and `apiClient`\n- Missing error boundaries in the login flow\n- Token refresh logic duplicates in 3 places\n\n**Recommendations:**\n1. Extract token management into a composable\n2. Add centralized error handling\n3. Implement refresh token queue', type: 'text', readBy: ['admin', 'arch-bot'], createdAt: h(3.5) },
    { id: 'msg-1-3', conversationId: 'conv-1', senderId: 'arch-bot', senderName: 'Arch-Bot', senderAvatar: '🏗️', senderType: 'agent', content: '```typescript\n// Proposed composable structure\nexport function useTokenManager() {\n  const refreshToken = ref<string>()\n  const isRefreshing = ref(false)\n  \n  async function refresh() {\n    if (isRefreshing.value) return\n    isRefreshing.value = true\n    // ... implementation\n    isRefreshing.value = false\n  }\n  \n  return { refresh, isRefreshing }\n}\n```', type: 'code', metadata: { language: 'typescript' }, readBy: ['admin'], createdAt: h(3) },
    { id: 'msg-1-4', conversationId: 'conv-1', senderId: 'admin', senderName: 'Admin', senderAvatar: '👨‍💼', senderType: 'human', content: 'Great analysis! Can you create issues for each of these?', type: 'text', readBy: ['admin', 'arch-bot'], createdAt: h(2) },
    { id: 'msg-1-5', conversationId: 'conv-1', senderId: 'arch-bot', senderName: 'Arch-Bot', senderAvatar: '🏗️', senderType: 'agent', content: 'I\'ve created 3 issues for the auth module refactor. Check the Issues board for ISS-089, ISS-090, and ISS-091.', type: 'agent_action', metadata: { action: 'created_issues', issueId: 'ISS-089' }, readBy: ['arch-bot'], createdAt: m(5) },
    { id: 'msg-1-6', conversationId: 'conv-1', senderId: 'arch-bot', senderName: 'Arch-Bot', senderAvatar: '🏗️', senderType: 'agent', content: 'I also updated the dependency graph to reflect the new proposed structure.', type: 'text', readBy: [], createdAt: m(3) },
  ],
  'conv-2': [
    { id: 'msg-2-1', conversationId: 'conv-2', senderId: 'alice', senderName: 'alice', senderAvatar: '👩‍💻', senderType: 'human', content: 'Morning everyone! Ready for sprint planning?', type: 'text', readBy: ['alice', 'admin', 'bob', 'charlie'], createdAt: h(3) },
    { id: 'msg-2-2', conversationId: 'conv-2', senderId: 'bob', senderName: 'bob', senderAvatar: '👨‍💻', senderType: 'human', content: 'Yep, I\'ve finished the backend API for the notification system. Ready for review.', type: 'text', readBy: ['bob', 'alice', 'admin', 'charlie'], createdAt: h(2.5) },
    { id: 'msg-2-3', conversationId: 'conv-2', senderId: 'charlie', senderName: 'charlie', senderAvatar: '🧑‍💻', senderType: 'human', content: 'I\'ll take the code review. Anything specific to look out for?', type: 'text', readBy: ['charlie', 'bob'], createdAt: h(2) },
    { id: 'msg-2-4', conversationId: 'conv-2', senderId: 'bob', senderName: 'bob', senderAvatar: '👨‍💻', senderType: 'human', content: 'The WebSocket reconnection logic might need some edge case handling. I\'ve added tests but a second pair of eyes would be good.', type: 'text', readBy: ['bob', 'charlie'], createdAt: h(1.8) },
    { id: 'msg-2-5', conversationId: 'conv-2', senderId: 'admin', senderName: 'Admin', senderAvatar: '👨‍💼', senderType: 'human', content: 'Let\'s also discuss the ISS-042 blocker. Alice, what\'s the status on the dependency resolution?', type: 'text', readBy: ['admin', 'alice', 'bob', 'charlie'], createdAt: h(1) },
    { id: 'msg-2-6', conversationId: 'conv-2', senderId: 'alice', senderName: 'alice', senderAvatar: '👩‍💻', senderType: 'human', content: 'I\'m working on the graph traversal fix. Should have a PR up by EOD.', type: 'text', readBy: ['alice', 'admin', 'bob', 'charlie'], createdAt: h(0.5) },
  ],
  'conv-3': [
    { id: 'msg-3-1', conversationId: 'conv-3', senderId: 'alice', senderName: 'alice', senderAvatar: '👩‍💻', senderType: 'human', content: 'Hey, did you see the issue with the Kanban drag-and-drop?', type: 'text', readBy: ['alice', 'admin'], createdAt: h(1) },
    { id: 'msg-3-2', conversationId: 'conv-3', senderId: 'admin', senderName: 'Admin', senderAvatar: '👨‍💼', senderType: 'human', content: 'Yes, I noticed it drops cards sometimes when the column is full. Is it the same root cause?', type: 'text', readBy: ['admin', 'alice'], createdAt: h(0.8) },
    { id: 'msg-3-3', conversationId: 'conv-3', senderId: 'alice', senderName: 'alice', senderAvatar: '👩‍💻', senderType: 'human', content: 'Exactly. The virtual scroll calculation is off by one when there are exactly 10 items. I\'ll fix it in the next commit.', type: 'text', readBy: ['alice'], createdAt: m(30) },
    { id: 'msg-3-4', conversationId: 'conv-3', senderId: 'alice', senderName: 'alice', senderAvatar: '👩‍💻', senderType: 'human', content: 'Also, the dark mode toggle animation feels a bit janky. Can we smooth it out?', type: 'text', readBy: ['alice'], createdAt: m(20) },
    { id: 'msg-3-5', conversationId: 'conv-3', senderId: 'alice', senderName: 'alice', senderAvatar: '👩‍💻', senderType: 'human', content: 'Let me know when you\'re free to pair on this!', type: 'text', readBy: [], createdAt: m(15) },
  ],
  'conv-4': [
    { id: 'msg-4-1', conversationId: 'conv-4', senderId: 'admin', senderName: 'Admin', senderAvatar: '👨‍💼', senderType: 'human', content: 'Can you review the latest changes to the constraints engine?', type: 'text', readBy: ['admin', 'code-reviewer'], createdAt: h(2) },
    { id: 'msg-4-2', conversationId: 'conv-4', senderId: 'code-reviewer', senderName: 'CodeReviewer', senderAvatar: '🔍', senderType: 'agent', content: 'Reviewing now... Found 3 issues:\n\n1. **Type safety**: `as any` cast in line 142\n2. **Missing error handling**: `validateConstraints` doesn\'t handle network errors\n3. **Performance**: `byCategory` method re-filters on every call\n\nSeverity: LOW to MEDIUM', type: 'text', readBy: ['admin', 'code-reviewer'], createdAt: h(1.5) },
    { id: 'msg-4-3', conversationId: 'conv-4', senderId: 'code-reviewer', senderName: 'CodeReviewer', senderAvatar: '🔍', senderType: 'agent', content: '```typescript\n// Suggested fix for byCategory\nbyCategory(cat: ConstraintCategory) {\n  return computed(() => \n    constraints.value.filter(c => c.category === cat)\n  )\n}\n```', type: 'code', metadata: { language: 'typescript' }, readBy: ['code-reviewer'], createdAt: h(1.4) },
    { id: 'msg-4-4', conversationId: 'conv-4', senderId: 'admin', senderName: 'Admin', senderAvatar: '👨‍💼', senderType: 'human', content: 'Good catches! I\'ll address all three. Thanks!', type: 'text', readBy: ['admin', 'code-reviewer'], createdAt: h(1) },
  ],
  'conv-5': [
    { id: 'msg-5-1', conversationId: 'conv-5', senderId: 'system', senderName: 'System', senderAvatar: '⚙️', senderType: 'system', content: 'Issue ISS-042 escalated to CRITICAL priority', type: 'system', readBy: ['admin', 'alice', 'bob', 'arch-bot'], createdAt: h(4) },
    { id: 'msg-5-2', conversationId: 'conv-5', senderId: 'alice', senderName: 'alice', senderAvatar: '👩‍💻', senderType: 'human', content: 'The dependency cycle is blocking all critical path items. We need to resolve this ASAP.', type: 'text', readBy: ['alice', 'admin', 'bob', 'arch-bot'], createdAt: h(3) },
    { id: 'msg-5-3', conversationId: 'conv-5', senderId: 'arch-bot', senderName: 'Arch-Bot', senderAvatar: '🏗️', senderType: 'agent', content: 'I\'ve identified the exact cycle: `authStore` -> `apiClient` -> `tokenManager` -> `authStore`. Breaking point: extract token logic.', type: 'text', readBy: ['arch-bot', 'admin', 'alice', 'bob'], createdAt: h(2.5) },
    { id: 'msg-5-4', conversationId: 'conv-5', senderId: 'bob', senderName: 'bob', senderAvatar: '👨‍💻', senderType: 'human', content: 'I can do the extraction. Should take about 2 hours.', type: 'text', readBy: ['bob', 'admin', 'alice', 'arch-bot'], createdAt: h(2) },
    { id: 'msg-5-5', conversationId: 'conv-5', senderId: 'admin', senderName: 'Admin', senderAvatar: '👨‍💼', senderType: 'human', content: 'Go for it. Alice, can you handle the graph update after Bob is done?', type: 'text', readBy: ['admin', 'alice', 'bob'], createdAt: h(1) },
    { id: 'msg-5-6', conversationId: 'conv-5', senderId: 'alice', senderName: 'alice', senderAvatar: '👩‍💻', senderType: 'human', content: 'On it!', type: 'text', readBy: [], createdAt: m(30) },
  ],
  'conv-6': [
    { id: 'msg-6-1', conversationId: 'conv-6', senderId: 'bob', senderName: 'bob', senderAvatar: '👨‍💻', senderType: 'human', content: 'Hey, do you have the credentials for the staging environment?', type: 'text', readBy: ['bob', 'admin'], createdAt: h(10) },
    { id: 'msg-6-2', conversationId: 'conv-6', senderId: 'admin', senderName: 'Admin', senderAvatar: '👨‍💼', senderType: 'human', content: 'Check the team vault. Should be under "socialseed-staging".', type: 'text', readBy: ['admin', 'bob'], createdAt: h(9) },
    { id: 'msg-6-3', conversationId: 'conv-6', senderId: 'bob', senderName: 'bob', senderAvatar: '👨‍💻', senderType: 'human', content: 'Found it, thanks!', type: 'text', readBy: ['bob', 'admin'], createdAt: h(8) },
  ],
  'conv-7': [
    { id: 'msg-7-1', conversationId: 'conv-7', senderId: 'admin', senderName: 'Admin', senderAvatar: '👨‍💼', senderType: 'human', content: 'Run a security scan on the latest release?', type: 'text', readBy: ['admin', 'security-auditor'], createdAt: h(5) },
    { id: 'msg-7-2', conversationId: 'conv-7', senderId: 'security-auditor', senderName: 'SecurityAuditor', senderAvatar: '🛡️', senderType: 'agent', content: 'Security scan complete. Results:\n\n**Vulnerabilities Found:** 0 Critical, 1 Medium, 3 Low\n\n**Medium:**\n- XSS risk in `MarkdownRenderer.vue` (line 68) - mermaid error handler uses innerHTML\n\n**Low:**\n- Missing CSRF token in mock API\n- Hardcoded CORS origins in docker-compose\n- Console statements left in production code', type: 'text', readBy: ['admin', 'security-auditor'], createdAt: h(4) },
    { id: 'msg-7-3', conversationId: 'conv-7', senderId: 'admin', senderName: 'Admin', senderAvatar: '👨‍💼', senderType: 'human', content: 'Good report. The XSS one is already fixed in the latest commit. Can you verify?', type: 'text', readBy: ['admin', 'security-auditor'], createdAt: h(3) },
    { id: 'msg-7-4', conversationId: 'conv-7', senderId: 'security-auditor', senderName: 'SecurityAuditor', senderAvatar: '🛡️', senderType: 'agent', content: 'Verified. The XSS issue in MarkdownRenderer has been resolved with proper HTML escaping. The other 3 low-severity items remain.', type: 'text', readBy: ['security-auditor'], createdAt: h(3) },
  ],
}

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>(MOCK_CONVERSATIONS)
  const messages = ref<Record<string, ChatMessage[]>>(MOCK_MESSAGES)
  const activeConversationId = ref<string | null>(null)
  const typingUsers = ref<TypingUser[]>([])
  const searchQuery = ref('')
  const loading = ref(false)

  const activeConversation = computed(() =>
    conversations.value.find(c => c.id === activeConversationId.value) || null
  )

  const activeMessages = computed(() => {
    if (!activeConversationId.value) return []
    return messages.value[activeConversationId.value] || []
  })

  const filteredConversations = computed(() => {
    const q = searchQuery.value.toLowerCase()
    let result = conversations.value
    if (q) {
      result = result.filter(c =>
        c.name.toLowerCase().includes(q) ||
        c.description?.toLowerCase().includes(q) ||
        c.participants.some(p => p.username.toLowerCase().includes(q))
      )
    }
    return result.sort((a, b) => {
      if (a.isPinned !== b.isPinned) return a.isPinned ? -1 : 1
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    })
  })

  const totalUnread = computed(() =>
    conversations.value.reduce((sum, c) => sum + c.unreadCount, 0)
  )

  function selectConversation(id: string) {
    activeConversationId.value = id
    const conv = conversations.value.find(c => c.id === id)
    if (conv) {
      conv.unreadCount = 0
    }
  }

  function sendMessage(conversationId: string, content: string, type: ChatMessage['type'] = 'text', metadata?: ChatMessage['metadata']) {
    const msg: ChatMessage = {
      id: `msg-${Date.now()}`,
      conversationId,
      senderId: CURRENT_USER_ID,
      senderName: 'Admin',
      senderAvatar: '👨‍💼',
      senderType: 'human',
      content,
      type,
      metadata,
      readBy: [CURRENT_USER_ID],
      createdAt: new Date().toISOString(),
    }

    if (!messages.value[conversationId]) {
      messages.value[conversationId] = []
    }
    messages.value[conversationId].push(msg)

    const conv = conversations.value.find(c => c.id === conversationId)
    if (conv) {
      conv.lastMessage = msg
      conv.updatedAt = msg.createdAt
    }

    // Simulate agent response after 1-3 seconds
    if (conv?.type === 'agent') {
      const agent = conv.participants.find(p => p.type === 'agent')
      if (agent) {
        simulateTyping(conversationId, agent.id, agent.username)
        setTimeout(() => {
          const response = generateAgentResponse(agent.username, content)
          receiveMessage(conversationId, agent, response)
        }, 1500 + Math.random() * 2000)
      }
    }
  }

  function receiveMessage(conversationId: string, sender: ChatParticipant, content: string, type: ChatMessage['type'] = 'text') {
    const msg: ChatMessage = {
      id: `msg-${Date.now()}`,
      conversationId,
      senderId: sender.id,
      senderName: sender.username,
      senderAvatar: sender.avatar,
      senderType: sender.type,
      content,
      type,
      readBy: [sender.id],
      createdAt: new Date().toISOString(),
    }

    if (!messages.value[conversationId]) {
      messages.value[conversationId] = []
    }
    messages.value[conversationId].push(msg)

    const conv = conversations.value.find(c => c.id === conversationId)
    if (conv) {
      conv.lastMessage = msg
      conv.updatedAt = msg.createdAt
      if (activeConversationId.value !== conversationId) {
        conv.unreadCount++
      }
    }
  }

  function simulateTyping(conversationId: string, userId: string, username: string) {
    typingUsers.value.push({ userId, username, conversationId, startedAt: Date.now() })
    setTimeout(() => {
      typingUsers.value = typingUsers.value.filter(t => t.userId !== userId || t.conversationId !== conversationId)
    }, 3000)
  }

  function generateAgentResponse(agentName: string, _userMessage: string): string {
    const responses: Record<string, string[]> = {
      'Arch-Bot': [
        'I\'ll analyze the architecture implications of that. Give me a moment...',
        'Good point. Based on the dependency graph, I recommend refactoring the module boundary first.',
        'The current structure suggests we should extract this into a shared composable. Shall I create a proposal?',
        'I\'ve identified 2 potential circular dependencies in that area. Let me document them.',
      ],
      'CodeReviewer': [
        'I\'ll review the changes. Looking for potential issues now...',
        'Found a few suggestions:\n1. Consider using `computed` instead of `watch` for derived state\n2. Missing error boundary in the async handler\n3. The type assertion could be more specific',
        'Looks good overall! Just minor nits on naming conventions.',
        'I\'d suggest extracting this into a utility function for reusability.',
      ],
      'SecurityAuditor': [
        'Running security analysis on that component...',
        'No critical vulnerabilities found. Minor observation: the input sanitization could be stricter.',
        'I recommend adding rate limiting to this endpoint. Current config allows unlimited requests.',
        'The authentication flow looks secure. One suggestion: add CSRF token validation.',
      ],
    }

    const agentResponses = responses[agentName] || ['I\'ll look into that and get back to you.']
    return agentResponses[Math.floor(Math.random() * agentResponses.length)]
  }

  function createConversation(type: 'direct' | 'group' | 'agent', name: string, participantIds: string[]) {
    const participants = participantIds
      .map(id => MOCK_PARTICIPANTS[id])
      .filter(Boolean)

    if (!participants.find(p => p.id === CURRENT_USER_ID)) {
      participants.unshift(MOCK_PARTICIPANTS[CURRENT_USER_ID])
    }

    const conv: Conversation = {
      id: `conv-${Date.now()}`,
      type,
      name,
      participants,
      unreadCount: 0,
      isPinned: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    conversations.value.unshift(conv)
    messages.value[conv.id] = []

    if (type === 'agent') {
      setTimeout(() => {
        const agent = participants.find(p => p.type === 'agent')
        if (agent) {
          receiveMessage(conv.id, agent, `Hello! I'm ${agent.username}. How can I help you today?`)
        }
      }, 1000)
    }

    return conv
  }

  function togglePin(conversationId: string) {
    const conv = conversations.value.find(c => c.id === conversationId)
    if (conv) conv.isPinned = !conv.isPinned
  }

  function getParticipant(id: string): ChatParticipant | undefined {
    return MOCK_PARTICIPANTS[id]
  }

  function getOnlineParticipants(): ChatParticipant[] {
    return Object.values(MOCK_PARTICIPANTS).filter(p => p.isOnline)
  }

  return {
    conversations,
    messages,
    activeConversationId,
    activeConversation,
    activeMessages,
    typingUsers,
    searchQuery,
    loading,
    filteredConversations,
    totalUnread,
    selectConversation,
    sendMessage,
    receiveMessage,
    createConversation,
    togglePin,
    getParticipant,
    getOnlineParticipants,
    MOCK_PARTICIPANTS,
  }
})
