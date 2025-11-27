import { useChatStore } from '../../store/chatStore'
import { Circle, Loader2 } from 'lucide-react'

export default function WorkflowVisualization() {
  const { isStreaming, currentReasoning } = useChatStore()

  // Only show during streaming with reasoning steps
  if (!isStreaming || currentReasoning.length === 0) return null

  return (
    <div className="space-y-1 text-xs text-zinc-500">
      {currentReasoning.slice(-5).map((step, idx) => {
        const isLast = idx === currentReasoning.length - 1 && isStreaming
        
        return (
          <div key={idx} className="flex items-center gap-2">
            {isLast ? (
              <Loader2 size={10} className="animate-spin text-zinc-600" />
            ) : (
              <Circle size={10} className="text-zinc-700" />
            )}
            <span className={isLast ? 'text-zinc-400' : ''}>
              {step.tool ? `Using ${step.tool}` : step.content?.slice(0, 60)}
              {step.content && step.content.length > 60 ? '...' : ''}
            </span>
          </div>
        )
      })}
    </div>
  )
}
