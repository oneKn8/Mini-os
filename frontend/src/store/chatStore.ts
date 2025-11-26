import { create } from 'zustand'
import { chatAPI } from '../api/chat'
import type { ChatMessage } from '../types/chat'

export interface Thought {
  agent: string
  status: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  summary?: any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  log?: any
  duration_ms?: number
}

export interface ReasoningStep {
  content: string
  step: string
  tool?: string
}

export interface SuggestedAction {
  text: string
  action: string
  payload: string
}

export interface ChatState {
  isOpen: boolean
  messages: ChatMessage[]
  isStreaming: boolean
  currentThoughts: Thought[]
  currentReasoning: ReasoningStep[]
  suggestedActions: SuggestedAction[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  pendingApprovals: any[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  sessions: any[]
  currentSessionId: string | null
  selectedModel: { provider: string, name: string } | null
  
  toggleChat: () => void
  setOpen: (isOpen: boolean) => void
  setModel: (provider: string, name: string) => void
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  sendMessage: (content: string, context?: any) => Promise<void>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  handleApproval: (proposalId: string, approved: boolean, editedPayload?: any) => Promise<void>
  resumeWorkflow: () => Promise<void>
  loadHistory: (sessionId?: string) => Promise<void>
  loadSessions: () => Promise<void>
  clearHistory: () => void
  sendSuggestedAction: (action: SuggestedAction) => Promise<void>
}

export const useChatStore = create<ChatState>((set, get) => ({
  isOpen: false,
  messages: [],
  isStreaming: false,
  currentThoughts: [],
  currentReasoning: [],
  suggestedActions: [],
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
        currentThoughts: [],
        currentReasoning: [],
        suggestedActions: []
    }))

    try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
            } else if (event.type === 'reasoning') {
                // Chain of thought - visible reasoning
                set((state) => ({
                    currentReasoning: [...state.currentReasoning, {
                        content: event.content,
                        step: event.step,
                        tool: event.tool
                    }]
                }))
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
            } else if (event.type === 'tool_start') {
                // Tool starting - add to reasoning
                set((state) => ({
                    currentReasoning: [...state.currentReasoning, {
                        content: `${event.icon} ${event.action}...`,
                        step: 'tool',
                        tool: event.tool
                    }]
                }))
            } else if (event.type === 'insight') {
                // Key insight from tool - add to reasoning
                set((state) => ({
                    currentReasoning: [...state.currentReasoning, {
                        content: `[Insight] ${event.content}`,
                        step: 'insight',
                        tool: event.source
                    }]
                }))
            } else if (event.type === 'suggestions') {
                // Follow-up suggestions
                set({ suggestedActions: event.actions || [] })
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
                    messages: [...state.messages, assistantMessage],
                    currentReasoning: [] // Clear reasoning after response
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
  
  handleApproval: async (proposalId, approved, editedPayload) => {
      // Optimistically remove from list
      set((state) => ({
          pendingApprovals: state.pendingApprovals.filter(p => p.id !== proposalId)
      }))
      
      // Send to API
      try {
          await chatAPI.sendApproval(proposalId, approved)
          
          // If approved, resume workflow
          if (approved) {
              // Update proposal payload if edited
              if (editedPayload) {
                  // In a real app, we'd update the proposal in DB via API
                  // For now, we'll just resume and let backend handle it
              }
              
              // Resume workflow
              await get().resumeWorkflow()
          }
      } catch (e) {
          console.error("Failed to submit approval", e)
          // Revert?
      }
  },
  
  resumeWorkflow: async () => {
      const { currentSessionId } = get()
      if (!currentSessionId) return
      
      set({ isStreaming: true, currentThoughts: [] })
      
      try {
          const stream = chatAPI.resumeWorkflow(currentSessionId)
          
          for await (const event of stream) {
              if (event.type === 'thought') {
                  set((state) => {
                      const existingIdx = state.currentThoughts.findIndex(t => t.agent === event.agent)
                      if (existingIdx !== -1) {
                          const newThoughts = [...state.currentThoughts]
                          newThoughts[existingIdx] = { ...newThoughts[existingIdx], ...event }
                          return { currentThoughts: newThoughts }
                      } else {
                          return { currentThoughts: [...state.currentThoughts, event] }
                      }
                  })
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
              }
          }
      } catch (e) {
          console.error("Failed to resume workflow", e)
      } finally {
          set({ isStreaming: false })
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
      set({ messages: [], currentSessionId: null, suggestedActions: [] })
  },

  sendSuggestedAction: async (action: SuggestedAction) => {
      // Handle suggested action based on type
      if (action.action === 'message') {
          // Send the payload as a message
          await get().sendMessage(action.payload)
      } else if (action.action === 'navigate') {
          // Navigate to the path
          window.dispatchEvent(new CustomEvent('chat-navigate', { detail: action.payload }))
      }
      // Clear suggestions after use
      set({ suggestedActions: [] })
  }
}))
