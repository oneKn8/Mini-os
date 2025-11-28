import { useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import WorkflowVisualization from './WorkflowVisualization'
import ApprovalCard from './ApprovalCard'
import PlanChecklist from './PlanChecklist'
import ChatHeader from './ChatHeader'
import SuggestedActions from './SuggestedActions'

export default function ChatWindow() {
  const { messages, isStreaming, loadHistory, pendingApprovals, handleApproval, currentReasoning } = useChatStore()
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem('chatCollapsed')
    return saved ? JSON.parse(saved) : false
  })
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    localStorage.setItem('chatCollapsed', JSON.stringify(isCollapsed))
    window.dispatchEvent(new CustomEvent('chat-collapsed-change', { detail: isCollapsed }))
  }, [isCollapsed])

  useEffect(() => {
    const handleExpand = () => setIsCollapsed(false)
    window.addEventListener('chatExpand', handleExpand)
    return () => window.removeEventListener('chatExpand', handleExpand)
  }, [])

  useEffect(() => {
    loadHistory()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  // Keep scroll at bottom during streaming
  useEffect(() => {
    if (isStreaming && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight
    }
  }, [isStreaming, currentReasoning])

  if (isCollapsed) {
    return (
      <div className="flex h-full flex-col bg-zinc-950 border-l border-zinc-800 relative">
        <button
          onClick={() => setIsCollapsed(false)}
          className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full p-2 bg-zinc-900 border border-zinc-800 border-l-0 rounded-r-lg hover:bg-zinc-800 transition-colors z-50"
          aria-label="Expand chat"
        >
          <ChevronLeft size={16} className="text-zinc-400" />
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col bg-zinc-950 relative">
      {/* Header */}
      <div className="flex items-center border-b border-zinc-800/50">
        <button
          onClick={() => setIsCollapsed(true)}
          className="p-2.5 hover:bg-zinc-900 transition-colors text-zinc-500 hover:text-zinc-300"
          aria-label="Collapse chat"
        >
          <ChevronRight size={16} />
        </button>
        <div className="flex-1">
          <ChatHeader />
        </div>
      </div>

      {/* Messages */}
      <div 
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 bg-zinc-950"
      >
        <MessageList messages={messages} />
        
        {/* Processing indicator - shows during streaming */}
        {isStreaming && (
          <div className="bg-zinc-900/50 rounded-lg p-3 border border-zinc-800">
            <div className="flex items-center gap-2 mb-2">
              <Loader2 size={14} className="animate-spin text-blue-400" />
              <span className="text-sm text-zinc-300 font-medium">Processing your request...</span>
            </div>
            <WorkflowVisualization />
          </div>
        )}
        
        {/* Plan Checklists */}
        {messages.map((msg) => {
          if (msg.sender === 'assistant' && msg.metadata?.intent === 'plan_day' && msg.metadata?.result) {
            return <PlanChecklist key={`plan-${msg.id}`} plan={msg.metadata.result} />
          }
          return null
        })}
        
        {/* Pending Approvals */}
        {pendingApprovals.length > 0 && (
          <div className="space-y-3">
            {pendingApprovals.map(proposal => (
              <ApprovalCard 
                key={proposal.id} 
                proposal={proposal}
                onApprove={(id, editedPayload, skipFuture) => handleApproval(id, true, editedPayload, skipFuture)}
                onReject={(id) => handleApproval(id, false)}
              />
            ))}
          </div>
        )}

        <SuggestedActions />
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-zinc-800/50 p-3 bg-zinc-950">
        <ChatInput />
      </div>
    </div>
  )
}
