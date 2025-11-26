import { useEffect, useRef } from 'react'
import { useChatStore } from '../../store/chatStore'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import ThinkingIndicator from './ThinkingIndicator'
import ApprovalCard from './ApprovalCard'
import ChatHeader from './ChatHeader'

export default function ChatWindow() {
  const { messages, isStreaming, loadHistory, pendingApprovals, handleApproval } = useChatStore()
  const scrollRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadHistory()
  }, [])

  const scrollToBottom = () => {
     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isStreaming, pendingApprovals]) 

  return (
    <div className="flex h-full flex-col bg-surface">
      <ChatHeader />

      <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-surface scroll-smooth">
        <MessageList messages={messages} />
        
        {/* Pending Approvals - Interactive Cards */}
        {pendingApprovals.length > 0 && (
            <div className="space-y-4">
                {pendingApprovals.map(proposal => (
                    <ApprovalCard 
                        key={proposal.id} 
                        proposal={proposal}
                        onApprove={(id) => handleApproval(id, true)}
                        onReject={(id) => handleApproval(id, false)}
                    />
                ))}
            </div>
        )}

        {isStreaming && <ThinkingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-border-light p-4 bg-surface">
        <ChatInput />
      </div>
    </div>
  )
}
