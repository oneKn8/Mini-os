import { SendMessageRequest, SendMessageResponse, ChatMessage } from '../types/chat'

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001'

const SESSION_STORAGE_KEY = 'ops-center-chat-session'

export class ChatAPI {
  private static instance: ChatAPI
  private sessionId: string | null = null

  private constructor() {
    if (typeof window !== 'undefined') {
      this.sessionId = window.localStorage.getItem(SESSION_STORAGE_KEY)
    }
  }

  static getInstance(): ChatAPI {
    if (!ChatAPI.instance) {
      ChatAPI.instance = new ChatAPI()
    }
    return ChatAPI.instance
  }

  async sendMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...request,
          sessionId: request.sessionId || this.sessionId,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      this.sessionId = data.sessionId
      this.persistSessionId(this.sessionId)
      return data
    } catch (error) {
      console.error('Error sending message:', error)
      throw error
    }
  }

  async getHistory(): Promise<ChatMessage[]> {
    if (!this.sessionId) {
      return []
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/history/${this.sessionId}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching chat history:', error)
      return []
    }
  }

  clearSession(): void {
    this.sessionId = null
    this.persistSessionId(null)
  }

  getSessionId(): string | null {
    return this.sessionId
  }

  private persistSessionId(sessionId: string | null) {
    if (typeof window === 'undefined') {
      return
    }

    if (sessionId) {
      window.localStorage.setItem(SESSION_STORAGE_KEY, sessionId)
    } else {
      window.localStorage.removeItem(SESSION_STORAGE_KEY)
    }
  }
}

export const chatAPI = ChatAPI.getInstance()
