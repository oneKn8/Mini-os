import { useState, FormEvent } from 'react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
}

function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (message.trim()) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <input
        type="text"
        className="chat-input"
        placeholder="Type a message..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        autoFocus
        disabled={disabled}
      />
      <button
        type="submit"
        className="chat-send-button"
        disabled={!message.trim() || disabled}
        aria-label="Send message"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
        </svg>
      </button>
    </form>
  )
}

export default ChatInput
