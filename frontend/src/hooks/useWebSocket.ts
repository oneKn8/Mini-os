import { useEffect, useRef, useState, useCallback } from 'react'

export interface WebSocketMessage {
  type: string
  [key: string]: unknown
}

export interface UseWebSocketOptions {
  url: string
  room?: string
  onMessage?: (message: WebSocketMessage) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useWebSocket({
  url,
  room = 'default',
  onMessage,
  onError,
  onOpen,
  onClose,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const shouldReconnectRef = useRef(true)
  const isMountedRef = useRef(true)

  const connect = useCallback(() => {
    // Don't connect if URL is empty (backend not available)
    if (!url || !isMountedRef.current) {
      return
    }
    shouldReconnectRef.current = true
    
    try {
      // Convert http(s) to ws(s)
      const wsUrl = url.replace(/^http/, 'ws')
      const fullUrl = `${wsUrl}?room=${room}`
      
      const ws = new WebSocket(fullUrl)
      wsRef.current = ws

      ws.onopen = () => {
        if (!isMountedRef.current) {
          return
        }
        setIsConnected(true)
        reconnectAttemptsRef.current = 0
        onOpen?.()
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          if (!isMountedRef.current) {
            return
          }
          setLastMessage(message)
          onMessage?.(message)
        } catch (error) {
          // Only log parsing errors, not connection errors
          if (import.meta.env.DEV) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }
      }

      ws.onerror = () => {
        // Silently handle connection errors - don't trigger callbacks or log
        // The browser will show its own error, but we won't add to it
      }

      ws.onclose = (event) => {
        if (!isMountedRef.current) {
          return
        }
        
        // Log disconnection in development for debugging
        if (import.meta.env.DEV && !event.wasClean) {
          console.warn(
            `WebSocket disconnected (code: ${event.code}). Is the backend running at ${url}?`, 
            event.reason || 'No reason provided'
          )
        }

        setIsConnected(false)
        onClose?.()

        // Attempt to reconnect silently
        if (shouldReconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else {
          // Silently stop reconnecting - backend is offline
        }
      }
    } catch (error) {
      // Silently handle connection errors
    }
  }, [url, room, onMessage, onError, onOpen, onClose, reconnectInterval, maxReconnectAttempts])

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    if (isMountedRef.current) {
      setIsConnected(false)
    }
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    connect()

    return () => {
      isMountedRef.current = false
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect,
  }
}
