import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// =============================================================================
// Types
// =============================================================================

export interface SettingsState {
  // Agent Behavior
  agentCursor: boolean
  thoughtBubbles: boolean
  confettiEnabled: boolean
  autoNavigate: boolean
  splitViewMode: 'always' | 'when_active' | 'manual'
  agentSpeed: 'slow' | 'normal' | 'fast' | 'instant'

  // Agent Permissions
  autoApproveAll: boolean
  autoApproveLowRisk: boolean
  learnPreferences: boolean
  maxAutoActions: number
  learnedApprovals: string[] // Action types user said "don't ask again"

  // Display
  tempUnit: 'celsius' | 'fahrenheit'
  timeFormat: '12h' | '24h'
  dateFormat: 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD'
  weekStartsOn: 'sunday' | 'monday'
  theme: 'dark' | 'light' | 'system'
  reducedMotion: boolean

  // AI Model
  defaultProvider: string
  defaultModel: string
  responseStyle: 'concise' | 'detailed' | 'balanced'
  showReasoning: 'always' | 'hover' | 'never'

  // Privacy
  saveChatHistory: boolean
  enableMemory: boolean
  persistMemory: boolean
  dataRetention: '7d' | '30d' | 'forever'

  // Location
  locationCity: string
  locationCountry: string

  // Actions
  updateSetting: <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => void
  resetToDefaults: () => void
  addLearnedApproval: (actionType: string) => void
  removeLearnedApproval: (actionType: string) => void
  setLocation: (city: string, country: string) => void
  syncWithBackend: () => Promise<void>
}

// =============================================================================
// Default Values
// =============================================================================

const defaultSettings: Omit<SettingsState, 
  'updateSetting' | 'resetToDefaults' | 'addLearnedApproval' | 
  'removeLearnedApproval' | 'setLocation' | 'syncWithBackend'
> = {
  // Agent Behavior
  agentCursor: true,
  thoughtBubbles: true,
  confettiEnabled: true,
  autoNavigate: true,
  splitViewMode: 'when_active',
  agentSpeed: 'normal',

  // Agent Permissions
  autoApproveAll: false,
  autoApproveLowRisk: false,
  learnPreferences: true,
  maxAutoActions: 3,
  learnedApprovals: [],

  // Display
  tempUnit: 'celsius',
  timeFormat: '12h',
  dateFormat: 'MM/DD/YYYY',
  weekStartsOn: 'sunday',
  theme: 'dark',
  reducedMotion: false,

  // AI Model
  defaultProvider: 'openai',
  defaultModel: 'gpt-4',
  responseStyle: 'balanced',
  showReasoning: 'always',

  // Privacy
  saveChatHistory: true,
  enableMemory: true,
  persistMemory: true,
  dataRetention: '30d',

  // Location
  locationCity: '',
  locationCountry: '',
}

// =============================================================================
// Store
// =============================================================================

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      ...defaultSettings,

      updateSetting: (key, value) => {
        set({ [key]: value } as Partial<SettingsState>)
        
        // Sync certain settings to backend
        const syncKeys = ['tempUnit', 'timeFormat', 'dateFormat', 'locationCity', 'locationCountry', 'theme']
        if (syncKeys.includes(key as string)) {
          get().syncWithBackend()
        }
      },

      resetToDefaults: () => {
        set(defaultSettings)
      },

      addLearnedApproval: (actionType) => {
        set((state) => ({
          learnedApprovals: [...new Set([...state.learnedApprovals, actionType])]
        }))
      },

      removeLearnedApproval: (actionType) => {
        set((state) => ({
          learnedApprovals: state.learnedApprovals.filter((t) => t !== actionType)
        }))
      },

      setLocation: (city, country) => {
        set({ locationCity: city, locationCountry: country })
        get().syncWithBackend()
      },

      syncWithBackend: async () => {
        const state = get()
        try {
          await fetch('/api/preferences', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
              location_city: state.locationCity,
              location_country: state.locationCountry,
              temp_unit: state.tempUnit,
              time_format: state.timeFormat,
              date_format: state.dateFormat,
              theme: state.theme,
            }),
          })
        } catch (error) {
          console.error('Failed to sync settings:', error)
        }
      },
    }),
    {
      name: 'settings-storage',
      partialize: (state) => ({
        // Only persist these fields
        agentCursor: state.agentCursor,
        thoughtBubbles: state.thoughtBubbles,
        confettiEnabled: state.confettiEnabled,
        autoNavigate: state.autoNavigate,
        splitViewMode: state.splitViewMode,
        agentSpeed: state.agentSpeed,
        autoApproveAll: state.autoApproveAll,
        autoApproveLowRisk: state.autoApproveLowRisk,
        learnPreferences: state.learnPreferences,
        maxAutoActions: state.maxAutoActions,
        learnedApprovals: state.learnedApprovals,
        tempUnit: state.tempUnit,
        timeFormat: state.timeFormat,
        dateFormat: state.dateFormat,
        weekStartsOn: state.weekStartsOn,
        theme: state.theme,
        reducedMotion: state.reducedMotion,
        defaultProvider: state.defaultProvider,
        defaultModel: state.defaultModel,
        responseStyle: state.responseStyle,
        showReasoning: state.showReasoning,
        saveChatHistory: state.saveChatHistory,
        enableMemory: state.enableMemory,
        persistMemory: state.persistMemory,
        dataRetention: state.dataRetention,
        locationCity: state.locationCity,
        locationCountry: state.locationCountry,
      }),
    }
  )
)

// =============================================================================
// Helpers
// =============================================================================

export function shouldSkipApproval(actionType: string): boolean {
  const state = useSettingsStore.getState()
  if (state.autoApproveAll) return true
  return state.learnedApprovals.includes(actionType)
}

export function getAnimationDuration(): number {
  const speed = useSettingsStore.getState().agentSpeed
  switch (speed) {
    case 'slow': return 500
    case 'normal': return 300
    case 'fast': return 150
    case 'instant': return 0
  }
}

export function shouldShowCursor(): boolean {
  const state = useSettingsStore.getState()
  return state.agentCursor && !state.reducedMotion
}

export function shouldShowThoughts(): boolean {
  const state = useSettingsStore.getState()
  return state.thoughtBubbles && state.showReasoning !== 'never'
}

export function convertTemperature(celsius: number): number {
  const unit = useSettingsStore.getState().tempUnit
  if (unit === 'fahrenheit') {
    return Math.round((celsius * 9/5) + 32)
  }
  return celsius
}

export function formatTemperature(celsius: number): string {
  const unit = useSettingsStore.getState().tempUnit
  const value = convertTemperature(celsius)
  return `${value}°${unit === 'fahrenheit' ? 'F' : 'C'}`
}

