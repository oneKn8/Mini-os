import { useState, useRef, useEffect } from 'react'
import './ChatAssistant.css'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import { chatAPI } from '../../api/chat'
import type { ChatMessage as ApiChatMessage } from '../../types/chat'

export interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  metadata?: Record<string, unknown>
}

function ChatAssistant() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      content: 'Hello! I\'m your AI assistant. How can I help you manage your tasks today?',
      sender: 'assistant',
      timestamp: new Date()
    }
  ])
  const [isTyping, setIsTyping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    let cancelled = false

    const loadHistory = async () => {
      const sessionId = chatAPI.getSessionId()
      if (!sessionId) {
        return
      }

      try {
        const history = await chatAPI.getHistory()
        if (!cancelled && history.length > 0) {
          setMessages(history.map(transformApiMessage))
        }
      } catch (historyError) {
        console.error('Failed to load chat history:', historyError)
      }
    }

    loadHistory()

    return () => {
      cancelled = true
    }
  }, [])

  const transformApiMessage = (message: ApiChatMessage): Message => ({
    id: message.id,
    content: message.content,
    sender: message.sender,
    timestamp: new Date(message.timestamp),
    metadata: message.metadata
  })

  const handleSendMessage = async (content: string) => {
    setError(null)

    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, newMessage])
    setIsTyping(true)

    try {
      const response = await chatAPI.sendMessage({
        content,
        context: {
          currentView: window.location.pathname
        }
      })

      const assistantMessage = transformApiMessage(response.message)
      setMessages(prev => [...prev, assistantMessage])
    } catch (apiError) {
      console.error('Error sending message:', apiError)
      setError('Unable to reach the agent hub. Please try again.')
      setMessages(prev => [
        ...prev,
        {
          id: `${Date.now()}-error`,
          content: 'I couldn\'t reach the agent hub. Please try again in a moment.',
          sender: 'assistant',
          timestamp: new Date()
        }
      ])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className={`chat-assistant ${isOpen ? 'open' : 'closed'}`}>
      {!isOpen && (
        <button
          className="chat-toggle-button"
          onClick={() => setIsOpen(true)}
          aria-label="Open chat assistant"
        >
          <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
          </svg>
        </button>
      )}

      {isOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <div className="chat-header-content">
              <div className="chat-avatar">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
                  <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
                </svg>
              </div>
              <div>
                <h3 className="chat-title">AI Assistant</h3>
                <p className="chat-status">Online</p>
              </div>
            </div>
            <button
              className="chat-close-button"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>

          <div className="chat-messages">
            {messages.map(message => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isTyping && (
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {error && <div className="chat-error">{error}</div>}

          <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
        </div>
      )}
    </div>
  )
}

export default ChatAssistant
