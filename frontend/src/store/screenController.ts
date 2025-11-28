import { create } from 'zustand'

// =============================================================================
// Types
// =============================================================================

export type AgentState = 'idle' | 'navigating' | 'working' | 'waiting'

export interface Preview {
  id: string
  type: string // 'calendar_event', 'email_draft', 'setting_change', etc.
  page: string
  data: any
  cursor?: string
  status: 'pending' | 'confirmed' | 'cancelled'
  createdAt: Date
}

export interface UndoableAction {
  id: string
  type: string
  description: string
  timestamp: Date
  undoFn?: () => Promise<void>
  data?: any
}

export interface ScreenControllerState {
  // Agent state
  agentActive: boolean
  agentState: AgentState
  agentPaused: boolean

  // Cursor control
  cursorPosition: { x: number; y: number } | null
  cursorElement: string | null // CSS selector

  // Thought bubbles
  currentThought: string | null
  thoughtPosition: { x: number; y: number }
  thoughtVisible: boolean

  // Page control
  targetPage: string | null
  currentFocus: string | null

  // Previews (generic)
  previews: Map<string, Preview>

  // Activity log / Undo
  activityLog: UndoableAction[]
  canUndo: boolean

  // Actions
  takeControl: () => void
  releaseControl: () => void
  pauseAgent: () => void
  resumeAgent: () => void
  stopAgent: () => void
  
  setAgentState: (state: AgentState) => void
  navigateTo: (page: string, focus?: string) => void
  moveCursor: (element: string) => void
  setCursorPosition: (x: number, y: number) => void
  hideCursor: () => void

  showThought: (thought: string, cursor?: string) => void
  hideThought: () => void

  addPreview: (preview: Omit<Preview, 'status' | 'createdAt'>) => void
  confirmPreview: (id: string) => void
  cancelPreview: (id: string) => void
  removePreview: (id: string) => void
  getPreviewsForPage: (page: string) => Preview[]

  logAction: (action: Omit<UndoableAction, 'timestamp'>) => void
  undo: () => Promise<void>
  clearActivityLog: () => void
}

// =============================================================================
// Store
// =============================================================================

export const useScreenController = create<ScreenControllerState>((set, get) => ({
  // Initial state
  agentActive: false,
  agentState: 'idle',
  agentPaused: false,

  cursorPosition: null,
  cursorElement: null,

  currentThought: null,
  thoughtPosition: { x: 0, y: 0 },
  thoughtVisible: false,

  targetPage: null,
  currentFocus: null,

  previews: new Map(),

  activityLog: [],
  canUndo: false,

  // Control methods
  takeControl: () => {
    set({ agentActive: true, agentState: 'navigating', agentPaused: false })
  },

  releaseControl: () => {
    set({
      agentActive: false,
      agentState: 'idle',
      cursorPosition: null,
      cursorElement: null,
      currentThought: null,
      thoughtVisible: false,
    })
  },

  pauseAgent: () => {
    set({ agentPaused: true })
  },

  resumeAgent: () => {
    set({ agentPaused: false })
  },

  stopAgent: () => {
    // Cancel all pending previews
    const previews = get().previews
    previews.forEach((preview, id) => {
      if (preview.status === 'pending') {
        previews.set(id, { ...preview, status: 'cancelled' })
      }
    })

    set({
      agentActive: false,
      agentState: 'idle',
      agentPaused: false,
      cursorPosition: null,
      cursorElement: null,
      currentThought: null,
      thoughtVisible: false,
      previews: new Map(previews),
    })
  },

  setAgentState: (state) => {
    set({ agentState: state })
  },

  // Navigation
  navigateTo: (page, focus) => {
    set({ targetPage: page, currentFocus: focus || null })
    
    // Dispatch navigation event
    window.dispatchEvent(new CustomEvent('agent-navigate', { detail: { page, focus } }))
  },

  // Cursor
  moveCursor: (element) => {
    set({ cursorElement: element })

    // Find element and calculate position
    requestAnimationFrame(() => {
      const el = document.querySelector(element)
      if (el) {
        const rect = el.getBoundingClientRect()
        set({
          cursorPosition: {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2,
          },
        })
      }
    })
  },

  setCursorPosition: (x, y) => {
    set({ cursorPosition: { x, y } })
  },

  hideCursor: () => {
    set({ cursorPosition: null, cursorElement: null })
  },

  // Thoughts
  showThought: (thought, cursor) => {
    const state = get()
    
    // Position near cursor or center
    let position = { x: window.innerWidth / 2, y: 100 }
    if (state.cursorPosition) {
      position = {
        x: state.cursorPosition.x + 20,
        y: state.cursorPosition.y - 40,
      }
    } else if (cursor) {
      const el = document.querySelector(cursor)
      if (el) {
        const rect = el.getBoundingClientRect()
        position = { x: rect.right + 10, y: rect.top }
      }
    }

    set({
      currentThought: thought,
      thoughtPosition: position,
      thoughtVisible: true,
    })

    // Auto-hide after 4 seconds
    setTimeout(() => {
      const current = get()
      if (current.currentThought === thought) {
        set({ thoughtVisible: false })
      }
    }, 4000)
  },

  hideThought: () => {
    set({ thoughtVisible: false, currentThought: null })
  },

  // Previews
  addPreview: (preview) => {
    const previews = new Map(get().previews)
    previews.set(preview.id, {
      ...preview,
      status: 'pending',
      createdAt: new Date(),
    })
    set({ previews })
  },

  confirmPreview: (id) => {
    const previews = new Map(get().previews)
    const preview = previews.get(id)
    if (preview) {
      previews.set(id, { ...preview, status: 'confirmed' })
      set({ previews })

      // Remove after animation
      setTimeout(() => {
        get().removePreview(id)
      }, 500)
    }
  },

  cancelPreview: (id) => {
    const previews = new Map(get().previews)
    const preview = previews.get(id)
    if (preview) {
      previews.set(id, { ...preview, status: 'cancelled' })
      set({ previews })

      // Remove after animation
      setTimeout(() => {
        get().removePreview(id)
      }, 300)
    }
  },

  removePreview: (id) => {
    const previews = new Map(get().previews)
    previews.delete(id)
    set({ previews })
  },

  getPreviewsForPage: (page) => {
    const previews = get().previews
    return Array.from(previews.values()).filter(
      (p) => p.page === page && p.status === 'pending'
    )
  },

  // Activity Log
  logAction: (action) => {
    const log = [
      { ...action, timestamp: new Date() },
      ...get().activityLog.slice(0, 49), // Keep last 50
    ]
    set({ activityLog: log, canUndo: log.length > 0 && !!log[0].undoFn })
  },

  undo: async () => {
    const log = get().activityLog
    if (log.length === 0) return

    const lastAction = log[0]
    if (lastAction.undoFn) {
      try {
        await lastAction.undoFn()
      } catch (error) {
        console.error('Undo failed:', error)
      }
    }

    const newLog = log.slice(1)
    set({
      activityLog: newLog,
      canUndo: newLog.length > 0 && !!newLog[0]?.undoFn,
    })
  },

  clearActivityLog: () => {
    set({ activityLog: [], canUndo: false })
  },
}))

// =============================================================================
// Hooks for pages
// =============================================================================

export function useScreenUpdates(pagePath: string) {
  const {
    previews,
    currentFocus,
    agentActive,
    agentState,
    targetPage,
  } = useScreenController()

  // Filter previews for this page
  const pagePreview = Array.from(previews.values()).filter(
    (p) => p.page === pagePath && p.status === 'pending'
  )

  // Is agent focused on this page?
  const isAgentFocused = targetPage === pagePath && agentActive

  return {
    previews: pagePreview,
    isAgentFocused,
    currentFocus,
    agentState,
  }
}

