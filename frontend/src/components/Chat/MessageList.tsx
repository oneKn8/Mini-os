import type { ChatMessage } from '../../types/chat'
import { clsx } from 'clsx'

interface MessageListProps {
  messages: ChatMessage[]
}

export default function MessageList({ messages }: MessageListProps) {
  return (
    <div className="flex flex-col space-y-4">
      {messages.map((msg, idx) => {
        const isUser = msg.sender === 'user'
        return (
          <div
            key={msg.id || idx}
            className={clsx(
              "flex w-full",
              isUser ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={clsx(
                "px-4 py-2 text-sm leading-relaxed",
                isUser 
                  ? "rounded-2xl bg-bg-secondary text-text-primary max-w-[85%]" 
                  : "w-full pl-0 bg-transparent text-text-primary"
              )}
            >
              {isUser ? (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
              ) : (
                  <div className="prose prose-sm max-w-none">
                      {msg.content.split('\n').map((line, i) => (
                          <p key={i} className="mb-2 last:mb-0">{line}</p>
                      ))}
                  </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

