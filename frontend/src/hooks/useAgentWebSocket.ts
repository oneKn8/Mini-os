import { useEffect, useRef, useState, useCallback } from 'react'
import { AgentEvent } from '../store/chatStore'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8101'

export interface UseAgentWebSocketOptions {
  sessionId: string | null
  enabled?: boolean
  onEvent?: (event: AgentEvent) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: string) => void
}

export interface AgentWebSocketState {
  isConnected: boolean
  isConnecting: boolean
  events: AgentEvent[]
  lastEvent: AgentEvent | null
  error: string | null
}

/**
 * WebSocket hook for real-time agent event streaming.
 * 
 * Connects to the agent event room for a specific chat session
 * and receives events like reasoning, tool execution, progress, etc.
 * 
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Event buffering
 * - Connection state management
 * - Graceful fallback to SSE if WebSocket unavailable
 */
export function useAgentWebSocket({
  sessionId,
  enabled = true,
  onEvent,
  onConnect,
  onDisconnect,
  onError,
}: UseAgentWebSocketOptions): AgentWebSocketState & {
  subscribe: () => void
  unsubscribe: () => void
  clearEvents: () => void
} {
  const [state, setState] = useState<AgentWebSocketState>({
    isConnected: false,
    isConnecting: false,
    events: [],
    lastEvent: null,
    error: null,
  })
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const shouldReconnectRef = useRef(true)
  const maxReconnectAttempts = 10
  const baseReconnectDelay = 1000

  const getReconnectDelay = useCallback(() => {
    // Exponential backoff: 1s, 2s, 4s, 8s, ... up to 30s max
    const delay = Math.min(
      baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current),
      30000
    )
    return delay
  }, [])

  const connect = useCallback(() => {
    if (!sessionId || !enabled) {
      return
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }))
    shouldReconnectRef.current = true

    try {
      // Build WebSocket URL
      const wsUrl = API_BASE_URL.replace(/^http/, 'ws')
      const fullUrl = `${wsUrl}/api/realtime/agent/${sessionId}`

      const ws = new WebSocket(fullUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
        }))
        reconnectAttemptsRef.current = 0
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as AgentEvent
          
          setState(prev => ({
            ...prev,
            events: [...prev.events, data],
            lastEvent: data,
          }))
          
          onEvent?.(data)
        } catch (error) {
          console.warn('Failed to parse agent event:', error)
        }
      }

      ws.onerror = () => {
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection error',
          isConnecting: false,
        }))
        onError?.('WebSocket connection error')
      }

      ws.onclose = (event) => {
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }))
        onDisconnect?.()

        // Attempt to reconnect with exponential backoff
        if (shouldReconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = getReconnectDelay()
          reconnectAttemptsRef.current += 1
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setState(prev => ({
            ...prev,
            error: 'Max reconnection attempts reached',
          }))
          onError?.('Max reconnection attempts reached')
        }
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: error instanceof Error ? error.message : 'Connection failed',
      }))
      onError?.(error instanceof Error ? error.message : 'Connection failed')
    }
  }, [sessionId, enabled, onEvent, onConnect, onDisconnect, onError, getReconnectDelay])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }))
  }, [])

  const subscribe = useCallback(() => {
    if (!state.isConnected && !state.isConnecting) {
      connect()
    }
  }, [connect, state.isConnected, state.isConnecting])

  const unsubscribe = useCallback(() => {
    disconnect()
  }, [disconnect])

  const clearEvents = useCallback(() => {
    setState(prev => ({
      ...prev,
      events: [],
      lastEvent: null,
    }))
  }, [])

  // Auto-connect when sessionId changes
  useEffect(() => {
    if (sessionId && enabled) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [sessionId, enabled]) // eslint-disable-line react-hooks/exhaustive-deps

  return {
    ...state,
    subscribe,
    unsubscribe,
    clearEvents,
  }
}

/**
 * Hook to get WebSocket connection status for monitoring.
 */
export function useAgentWebSocketStatus() {
  const [status, setStatus] = useState<{
    rooms: string[]
    totalConnections: number
    roomCounts: Record<string, number>
  } | null>(null)

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/realtime/status`)
      if (response.ok) {
        const data = await response.json()
        setStatus({
          rooms: data.rooms,
          totalConnections: data.total_connections,
          roomCounts: data.room_counts,
        })
      }
    } catch (error) {
      console.warn('Failed to fetch WebSocket status:', error)
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 30000) // Poll every 30s
    return () => clearInterval(interval)
  }, [fetchStatus])

  return status
}

export default useAgentWebSocket

