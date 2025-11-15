import { Message } from './ChatAssistant'

interface ChatMessageProps {
  message: Message
}

function ChatMessage({ message }: ChatMessageProps) {
  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: 'numeric',
      hour12: true
    }).format(date)
  }

  return (
    <div className={`chat-message ${message.sender}`}>
      <div className="message-content">
        <p>{message.content}</p>
        <span className="message-time">{formatTime(message.timestamp)}</span>
      </div>
    </div>
  )
}

export default ChatMessage
