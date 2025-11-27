import { useEffect, useRef, useState, useCallback } from 'react'

export interface SSEMessage {
  type: string
  channel: string
  data: unknown
  timestamp: string
}

export interface UseSSEOptions {
  url: string
  onMessage?: (message: SSEMessage) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useSSE({
  url,
  onMessage,
  onError,
  onOpen,
  onClose,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
}: UseSSEOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<SSEMessage | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    // Don't connect if URL is empty (backend not available)
    if (!url) {
      return
    }
    
    try {
      const eventSource = new EventSource(url)
      eventSourceRef.current = eventSource

      eventSource.onopen = () => {
        setIsConnected(true)
        reconnectAttemptsRef.current = 0
        onOpen?.()
      }

      eventSource.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as SSEMessage
          setLastMessage(message)
          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse SSE message:', error)
        }
      }

      eventSource.onerror = (error) => {
        // Silently handle errors - don't log connection failures
        setIsConnected(false)
        onError?.(error)
        
        // Close and attempt to reconnect
        eventSource.close()
        eventSourceRef.current = null

        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else {
          // Silently stop reconnecting - backend is offline
          onClose?.()
        }
      }
    } catch (error) {
      // Silently handle connection errors
    }
  }, [url, onMessage, onError, onOpen, onClose, reconnectInterval, maxReconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsConnected(false)
  }, [])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    lastMessage,
    disconnect,
    reconnect: connect,
  }
}

