import { create } from 'zustand'
import { chatAPI } from '../api/chat'
import type { ChatMessage } from '../types/chat'

export interface Thought {
  agent: string
  status: string
  summary?: any
  log?: any
  duration_ms?: number
}

export interface ChatState {
  isOpen: boolean
  messages: ChatMessage[]
  isStreaming: boolean
  currentThoughts: Thought[]
  pendingApprovals: any[]
  sessions: any[]
  currentSessionId: string | null
  selectedModel: { provider: string, name: string } | null
  
  toggleChat: () => void
  setOpen: (isOpen: boolean) => void
  setModel: (provider: string, name: string) => void
  sendMessage: (content: string, context?: any) => Promise<void>
  handleApproval: (proposalId: string, approved: boolean) => Promise<void>
  loadHistory: (sessionId?: string) => Promise<void>
  loadSessions: () => Promise<void>
  clearHistory: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  isOpen: false,
  messages: [],
  isStreaming: false,
  currentThoughts: [],
  pendingApprovals: [],
  sessions: [],
  currentSessionId: null,
  selectedModel: null,

  toggleChat: () => set((state) => ({ isOpen: !state.isOpen })),
  setOpen: (isOpen) => set({ isOpen }),
  setModel: (provider, name) => set({ selectedModel: { provider, name } }),
  
  sendMessage: async (content, context) => {
    const userMessage: ChatMessage = {
        id: Date.now().toString(),
        content,
        sender: 'user',
        timestamp: new Date().toISOString()
    }
    
    const { currentSessionId, selectedModel } = get()
    
    set((state) => ({ 
        messages: [...state.messages, userMessage],
        isStreaming: true,
        currentThoughts: []
    }))

    try {
        const requestPayload: any = { 
            content, 
            context, 
            sessionId: currentSessionId || undefined 
        }
        
        if (selectedModel) {
            requestPayload.modelProvider = selectedModel.provider
            requestPayload.modelName = selectedModel.name
        }

        const stream = chatAPI.streamMessage(requestPayload)
        
        for await (const event of stream) {
            if (event.type === 'session_id') {
                set({ currentSessionId: event.session_id })
            } else if (event.type === 'thought') {
                set((state) => {
                    // Check if we already have a thought for this agent
                    const existingIdx = state.currentThoughts.findIndex(t => t.agent === event.agent)
                    if (existingIdx !== -1) {
                        // Update existing
                        const newThoughts = [...state.currentThoughts]
                        newThoughts[existingIdx] = { ...newThoughts[existingIdx], ...event }
                        return { currentThoughts: newThoughts }
                    } else {
                        // Add new
                        return { currentThoughts: [...state.currentThoughts, event] }
                    }
                })
            } else if (event.type === 'approval_required') {
                set((state) => ({
                    pendingApprovals: [...state.pendingApprovals, ...event.proposals]
                }))
            } else if (event.type === 'message') {
                 const assistantMessage: ChatMessage = {
                    id: Date.now().toString(),
                    content: event.content,
                    sender: 'assistant',
                    timestamp: new Date().toISOString(),
                    metadata: event.metadata
                }
                set((state) => ({
                    messages: [...state.messages, assistantMessage]
                }))
            } else if (event.type === 'error') {
                 console.error(event.error)
                 const errorMessage: ChatMessage = {
                    id: Date.now().toString(),
                    content: `Error: ${event.error}`,
                    sender: 'assistant',
                    timestamp: new Date().toISOString()
                }
                set((state) => ({
                    messages: [...state.messages, errorMessage]
                }))
            } else if (event.type === 'navigation') {
                // Dispatch custom event for navigation that other components can listen to
                window.dispatchEvent(new CustomEvent('chat-navigate', { detail: event.path }))
            }
        }
    } catch (e) {
        console.error(e)
        const errorMessage: ChatMessage = {
            id: Date.now().toString(),
            content: "Sorry, I encountered an error while connecting to the server.",
            sender: 'assistant',
            timestamp: new Date().toISOString()
        }
        set((state) => ({
            messages: [...state.messages, errorMessage]
        }))
    } finally {
        set({ isStreaming: false })
    }
  },
  
  handleApproval: async (proposalId, approved) => {
      // Optimistically remove from list
      set((state) => ({
          pendingApprovals: state.pendingApprovals.filter(p => p.id !== proposalId)
      }))
      
      // Send to API
      try {
          await chatAPI.sendApproval(proposalId, approved)
          // We should probably re-trigger streaming or wait for socket update?
          // For now, assume user manually resumes conversation or we auto-resume in backend
      } catch (e) {
          console.error("Failed to submit approval", e)
          // Revert?
      }
  },
  
  loadHistory: async (sessionId) => {
      const id = sessionId || chatAPI.getSessionId()
      if (id) {
          set({ currentSessionId: id })
          const history = await chatAPI.getHistory(id) // Pass ID to API
          set({ messages: history })
      }
  },
  
  loadSessions: async () => {
      try {
          const sessions = await chatAPI.getSessions()
          set({ sessions })
      } catch (e) {
          console.error("Failed to load sessions", e)
      }
  },

  clearHistory: () => {
      chatAPI.clearSession()
      set({ messages: [], currentSessionId: null })
  }
}))
