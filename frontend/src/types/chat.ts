export interface ChatMessage {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: string
  metadata?: Record<string, unknown>
}

export interface ChatSession {
  id: string
  messages: ChatMessage[]
  createdAt: Date
  updatedAt: Date
}

export interface SendMessageRequest {
  content: string
  sessionId?: string
  context?: {
    currentView?: string
    selectedItems?: string[]
  }
}

export interface SendMessageResponse {
  message: ChatMessage
  sessionId: string
}

export interface ChatConfig {
  wsUrl?: string
  apiUrl?: string
  maxMessageLength?: number
  enableTypingIndicator?: boolean
}
