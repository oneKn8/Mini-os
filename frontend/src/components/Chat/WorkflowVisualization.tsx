import { useChatStore } from '../../store/chatStore'

export default function WorkflowVisualization() {
  const { currentReasoning } = useChatStore()

  if (currentReasoning.length === 0) return null

  // Get last 5 reasoning steps
  const recentSteps = currentReasoning.slice(-5)

  return (
    <div className="space-y-1.5 text-sm mt-2">
      {recentSteps.map((step, idx) => (
        <div key={idx} className="flex items-center gap-2 animate-fadeIn">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-500/70" />
          <span className="text-zinc-300">
            {step.tool ? (
              <span className="text-blue-400">{step.tool}</span>
            ) : (
              step.content?.slice(0, 80)
            )}
            {step.content && step.content.length > 80 ? '...' : ''}
          </span>
        </div>
      ))}
    </div>
  )
}
