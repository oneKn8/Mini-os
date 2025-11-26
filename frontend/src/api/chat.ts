export interface SendMessageRequest {
  content: string
  sessionId?: string | null
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  context?: any
  modelProvider?: string
  modelName?: string
}

export interface SendMessageResponse {
  message: ChatMessage
  sessionId: string
}

export interface ChatMessage {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  metadata?: any
}

// Use relative URLs to go through Vite proxy, or use env variable if set
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || ''

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

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async *streamMessage(request: SendMessageRequest): AsyncGenerator<any, void, unknown> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
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

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is null')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.trim()) {
            try {
                const event = JSON.parse(line)
                // Update session ID if received
                if (event.type === 'session_id' && event.session_id) {
                    this.sessionId = event.session_id
                    this.persistSessionId(this.sessionId)
                }
                yield event
            } catch (e) {
                console.error("Failed to parse stream line", line, e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error streaming message:', error)
      throw error
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async sendApproval(actionId: string, approved: boolean): Promise<any> {
    if (!this.sessionId) throw new Error("No session active")
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/action/${actionId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approved })
        })
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
        return await response.json()
    } catch (error) {
        console.error('Error sending approval:', error)
        throw error
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async *resumeWorkflow(sessionId: string, userId: string = "default_user"): AsyncGenerator<any, void, unknown> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sessionId, user_id: userId }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is null')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.trim()) {
            try {
              const event = JSON.parse(line)
              yield event
            } catch (e) {
              console.error("Failed to parse stream line", line, e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error resuming workflow:', error)
      throw error
    }
  }
  
  async getHistory(sessionId?: string): Promise<ChatMessage[]> {
    const id = sessionId || this.sessionId
    if (!id) {
      return []
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/history/${id}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching chat history:', error)
      return []
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async getSessions(): Promise<any[]> {
      try {
          const response = await fetch(`${API_BASE_URL}/api/chat/sessions`)
          if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
          return await response.json()
      } catch (error) {
          console.error('Error fetching sessions:', error)
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
