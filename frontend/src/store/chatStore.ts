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

export interface AgentEvent {
  type: string
  timestamp?: string
  content?: string
  step?: string
  tool?: string
  status?: string
  progress_percent?: number
  current_step?: number
  total_steps?: number
  percent_complete?: number
  capabilities?: string[]
  data_type?: string
  count?: number
  question?: string
  choice?: string
  [key: string]: any
}

export interface ChatState {
  isOpen: boolean
  messages: ChatMessage[]
  isStreaming: boolean
  currentThoughts: Thought[]
  currentReasoning: ReasoningStep[]
  agentEvents: AgentEvent[]
  suggestedActions: SuggestedAction[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  pendingApprovals: any[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  sessions: any[]
  currentSessionId: string | null
  selectedModel: { provider: string, name: string } | null
  currentProgress: number
  agentStatus: string
  // WebSocket state (for real-time features like live collaboration)
  wsConnected: boolean
  
  toggleChat: () => void
  setOpen: (isOpen: boolean) => void
  setModel: (provider: string, name: string) => void
  setWsConnected: (connected: boolean) => void
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  sendMessage: (content: string, context?: any) => Promise<void>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  handleApproval: (proposalId: string, approved: boolean, editedPayload?: any) => Promise<void>
  resumeWorkflow: () => Promise<void>
  loadHistory: (sessionId?: string) => Promise<void>
  loadSessions: () => Promise<void>
  clearHistory: () => void
  sendSuggestedAction: (action: SuggestedAction) => Promise<void>
  addAgentEvent: (event: AgentEvent) => void
}

// Load saved model from localStorage
const loadSavedModel = () => {
  if (typeof window === 'undefined') return null
  try {
    const saved = localStorage.getItem('ops-center-selected-model')
    if (saved) {
      const parsed = JSON.parse(saved)
      return { provider: parsed.provider, name: parsed.name }
    }
  } catch (e) {
    console.error('Failed to load saved model:', e)
  }
  return null
}

// Save model to localStorage
const saveModel = (provider: string, name: string) => {
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem('ops-center-selected-model', JSON.stringify({ provider, name }))
    } catch (e) {
      console.error('Failed to save model:', e)
    }
  }
}

export const useChatStore = create<ChatState>((set, get) => ({
  isOpen: false,
  messages: [],
  isStreaming: false,
  currentThoughts: [],
  currentReasoning: [],
  agentEvents: [],
  suggestedActions: [],
  pendingApprovals: [],
  sessions: [],
  currentSessionId: null,
  selectedModel: loadSavedModel() || { provider: 'openai', name: 'gpt-5' }, // Default to GPT-5
  currentProgress: 0,
  agentStatus: 'idle',
  wsConnected: false,

  toggleChat: () => set((state) => ({ isOpen: !state.isOpen })),
  setOpen: (isOpen) => set({ isOpen }),
  setModel: (provider, name) => {
    saveModel(provider, name)
    set({ selectedModel: { provider, name } })
  },
  setWsConnected: (connected) => set({ wsConnected: connected }),
  addAgentEvent: (event) => set((state) => ({ 
    agentEvents: [...state.agentEvents, { ...event, timestamp: event.timestamp || new Date().toISOString() }] 
  })),
  
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
        agentEvents: [],
        suggestedActions: [],
        currentProgress: 0,
        agentStatus: 'active'
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
            } else if (event.type === 'plan') {
                // Execution plan
                set((state) => ({
                    agentEvents: [...state.agentEvents, {
                        type: 'plan',
                        steps: event.steps,
                        estimated_duration_ms: event.estimated_duration_ms,
                        strategy: event.strategy,
                        timestamp: new Date().toISOString()
                    }]
                }))
            } else if (event.type === 'data') {
                // Data retrieved
                set((state) => ({
                    agentEvents: [...state.agentEvents, {
                        type: 'data',
                        data_type: event.data_type,
                        count: event.count,
                        preview: event.preview,
                        timestamp: new Date().toISOString()
                    }]
                }))
            } else if (event.type === 'decision') {
                // Agent decision point
                set((state) => ({
                    agentEvents: [...state.agentEvents, {
                        type: 'decision',
                        question: event.question,
                        choice: event.choice,
                        reasoning: event.reasoning,
                        timestamp: new Date().toISOString()
                    }]
                }))
            } else if (event.type === 'progress') {
                // Progress update
                set({
                    currentProgress: event.percent_complete || 0,
                    agentEvents: [...get().agentEvents, {
                        type: 'progress',
                        current_step: event.current_step,
                        total_steps: event.total_steps,
                        percent_complete: event.percent_complete,
                        current_action: event.current_action,
                        timestamp: new Date().toISOString()
                    }]
                })
            } else if (event.type === 'agent_status') {
                // Agent status change
                set({
                    agentStatus: event.status || 'active',
                    agentEvents: [...get().agentEvents, {
                        type: 'agent_status',
                        status: event.status,
                        capabilities: event.capabilities,
                        tools: event.tools,
                        message: event.message,
                        timestamp: new Date().toISOString()
                    }]
                })
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
                    currentReasoning: [], // Clear reasoning after response
                    agentStatus: 'completed',
                    currentProgress: 100
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
        set({
            isStreaming: false,
            agentStatus: 'idle',
            currentProgress: 0
        })
    }
  },
  
  handleApproval: async (proposalId, approved, editedPayload) => {
      // Optimistically remove from list
      const proposal = get().pendingApprovals.find(p => p.id === proposalId)
      set((state) => ({
          pendingApprovals: state.pendingApprovals.filter(p => p.id !== proposalId)
      }))
      
      const buildFollowUps = () => {
          if (!proposal) return []
          if (proposal.action_type === "create_calendar_event") {
              const title = proposal.payload?.title || "the event"
              return [
                  { text: "Email attendees", action: "message", payload: `Draft an email with the agenda for "${title}"` },
                  { text: "Add reminder", action: "message", payload: `Set a 15 minute reminder for "${title}"` },
              ]
          }
          if (proposal.action_type === "create_email_draft") {
              const subject = proposal.payload?.subject || "that email"
              return [
                  { text: "Send it now", action: "message", payload: "Send that email now" },
                  { text: "Tighten it up", action: "message", payload: `Shorten "${subject}" and make it punchier` },
              ]
          }
          return []
      }

      // Send to API
      try {
          const result = await chatAPI.sendApproval(proposalId, approved)
          
          const actionType = proposal?.action_type || "action"
          const status = result.status
          const executionStatus = result.execution_status
          const followUps = status === "executed" ? buildFollowUps() : []

          if (approved) {
              let message = result.message || "Action processed."

              if (status === "executed") {
                  if (actionType === "create_calendar_event") {
                      message = `Event "${proposal?.payload?.title || 'event'}" has been added to your calendar!`
                  } else if (actionType === "create_email_draft") {
                      message = `Draft ready: "${proposal?.payload?.subject || 'email'}" is waiting for your review.`
                  } else {
                      message = result.message || "Action executed successfully!"
                  }
              } else if (status === "failed") {
                  message = result.message ? `Action failed: ${result.message}` : "Action execution failed."
              } else if (status) {
                  const statusText = executionStatus ? `${status} (${executionStatus})` : status
                  message = result.message || `Action status: ${statusText}.`
              }
              
              const successMessage: ChatMessage = {
                  id: Date.now().toString(),
                  content: message,
                  sender: 'assistant',
                  timestamp: new Date().toISOString(),
                  metadata: { type: 'action_executed', action_id: proposalId, status }
              }
              
              set((state) => ({
                  messages: [...state.messages, successMessage],
                  suggestedActions: followUps.length ? followUps : state.suggestedActions
              }))
          } else if (!approved) {
              const rejectMessage: ChatMessage = {
                  id: Date.now().toString(),
                  content: "Action has been rejected.",
                  sender: 'assistant',
                  timestamp: new Date().toISOString(),
              }
              
              set((state) => ({
                  messages: [...state.messages, rejectMessage]
              }))
          }
      } catch (e) {
          console.error("Failed to submit approval", e)
          
          // Show error message
          const errorMessage: ChatMessage = {
              id: Date.now().toString(),
              content: `Failed to execute action: ${e instanceof Error ? e.message : 'Unknown error'}`,
              sender: 'assistant',
              timestamp: new Date().toISOString(),
          }
          
          set((state) => ({
              messages: [...state.messages, errorMessage],
              // Re-add proposal if it failed
              pendingApprovals: proposal ? [...state.pendingApprovals, proposal] : state.pendingApprovals
          }))
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
