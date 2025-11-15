import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './ChatView.css'
import ChatMessage from '../components/ChatAssistant/ChatMessage'
import ChatInput from '../components/ChatAssistant/ChatInput'
import { chatAPI } from '../api/chat'
import type { ChatMessage as ApiChatMessage } from '../types/chat'

export interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  metadata?: Record<string, unknown>
}

function ChatView() {
  const navigate = useNavigate()
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
    <div className="chat-view">
      <div className="chat-container">
        <div className="chat-header">
          <div className="chat-header-content">
            <button className="chat-back-button" onClick={() => navigate(-1)}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
            </button>
            <div className="chat-avatar">
              <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor">
                <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
                <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
              </svg>
            </div>
            <div>
              <h1 className="chat-title">AI Assistant</h1>
              <p className="chat-status">Online</p>
            </div>
          </div>
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
    </div>
  )
}

export default ChatView

