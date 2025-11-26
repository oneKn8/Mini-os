import { useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import ThinkingIndicator from './ThinkingIndicator'
import ApprovalCard from './ApprovalCard'
import PlanChecklist from './PlanChecklist'
import ChatHeader from './ChatHeader'

export default function ChatWindow() {
  const { messages, isStreaming, loadHistory, pendingApprovals, handleApproval } = useChatStore()
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem('chatCollapsed')
    return saved ? JSON.parse(saved) : false
  })
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    localStorage.setItem('chatCollapsed', JSON.stringify(isCollapsed))
  }, [isCollapsed])

  useEffect(() => {
    const handleExpand = () => {
      setIsCollapsed(false)
    }
    window.addEventListener('chatExpand', handleExpand)
    return () => window.removeEventListener('chatExpand', handleExpand)
  }, [])

  useEffect(() => {
    loadHistory()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const scrollToBottom = () => {
     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isStreaming, pendingApprovals]) 

  if (isCollapsed) {
    return (
      <div className="flex h-full flex-col bg-surface border-l border-border-light relative">
        <button
          onClick={() => setIsCollapsed(false)}
          className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full p-2 bg-surface border border-border-light border-l-0 rounded-r-lg hover:bg-surface-hover transition-colors z-50 shadow-lg"
          aria-label="Expand chat"
        >
          <ChevronLeft size={18} className="text-text-secondary" />
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col bg-surface relative">
      <div className="flex items-center border-b border-border-light">
        <button
          onClick={() => setIsCollapsed(true)}
          className="p-2 hover:bg-surface-hover transition-colors text-text-secondary hover:text-text-primary"
          aria-label="Collapse chat"
        >
          <ChevronRight size={18} />
        </button>
        <div className="flex-1">
          <ChatHeader />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-surface scroll-smooth">
        <MessageList messages={messages} />
        
        {/* Plan Checklists - Show for plan_day intent messages */}
        {messages.map((msg) => {
          if (msg.sender === 'assistant' && msg.metadata?.intent === 'plan_day' && msg.metadata?.result) {
            return (
              <PlanChecklist 
                key={`plan-${msg.id}`}
                plan={msg.metadata.result}
              />
            )
          }
          return null
        })}
        
        {/* Pending Approvals - Interactive Cards */}
        {pendingApprovals.length > 0 && (
            <div className="space-y-4">
                {pendingApprovals.map(proposal => (
                    <ApprovalCard 
                        key={proposal.id} 
                        proposal={proposal}
                        onApprove={(id, editedPayload) => handleApproval(id, true, editedPayload)}
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
