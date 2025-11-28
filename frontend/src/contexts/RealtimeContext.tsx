import { createContext, useContext, ReactNode } from 'react'
import { useWebSocket, WebSocketMessage } from '../hooks/useWebSocket'
import { useSSE, SSEMessage } from '../hooks/useSSE'

interface RealtimeContextValue {
  // WebSocket for chat and actions
  wsConnected: boolean
  wsLastMessage: WebSocketMessage | null
  sendWSMessage: (message: WebSocketMessage) => void
  
  // SSE for data updates
  sseInboxConnected: boolean
  sseInboxLastMessage: SSEMessage | null
  sseCalendarConnected: boolean
  sseCalendarLastMessage: SSEMessage | null
  sseWeatherConnected: boolean
  sseWeatherLastMessage: SSEMessage | null
}

const RealtimeContext = createContext<RealtimeContextValue | undefined>(undefined)

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8101'
const WS_BASE_URL = import.meta.env.VITE_WS_URL || API_BASE_URL.replace(/^http/, 'ws')

export function RealtimeProvider({ children }: { children: ReactNode }) {
  // Don't do health checks - let the connections handle their own logic
  // They will fail silently and reconnect when backend comes online
  const shouldConnect = true // Always try to connect, hooks will handle failures
  
  // WebSocket for chat and actions
  // Note: WebSocket can't use HTTP proxy, so we connect directly to backend
  const {
    isConnected: wsConnected,
    lastMessage: wsLastMessage,
    sendMessage: sendWSMessage,
  } = useWebSocket({
    url: shouldConnect ? `${WS_BASE_URL}/api/realtime/ws` : '',
    room: 'default',
    maxReconnectAttempts: shouldConnect ? 5 : 0,
  })

  // SSE for inbox updates (use proxy path)
  const {
    isConnected: sseInboxConnected,
    lastMessage: sseInboxLastMessage,
  } = useSSE({
    url: shouldConnect ? '/api/realtime/sse/inbox' : '',
    maxReconnectAttempts: shouldConnect ? 5 : 0,
  })

  // SSE for calendar updates (use proxy path)
  const {
    isConnected: sseCalendarConnected,
    lastMessage: sseCalendarLastMessage,
  } = useSSE({
    url: shouldConnect ? '/api/realtime/sse/calendar' : '',
    maxReconnectAttempts: shouldConnect ? 5 : 0,
  })

  // SSE for weather updates (use proxy path)
  const {
    isConnected: sseWeatherConnected,
    lastMessage: sseWeatherLastMessage,
  } = useSSE({
    url: shouldConnect ? '/api/realtime/sse/weather' : '',
    maxReconnectAttempts: shouldConnect ? 5 : 0,
  })
  

  const value: RealtimeContextValue = {
    wsConnected,
    wsLastMessage,
    sendWSMessage,
    sseInboxConnected,
    sseInboxLastMessage,
    sseCalendarConnected,
    sseCalendarLastMessage,
    sseWeatherConnected,
    sseWeatherLastMessage,
  }

  return (
    <RealtimeContext.Provider value={value}>
      {children}
    </RealtimeContext.Provider>
  )
}

export function useRealtime() {
  const context = useContext(RealtimeContext)
  if (context === undefined) {
    throw new Error('useRealtime must be used within a RealtimeProvider')
  }
  return context
}

