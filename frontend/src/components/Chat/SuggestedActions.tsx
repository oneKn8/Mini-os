import { ArrowRight } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'

export default function SuggestedActions() {
  const { suggestedActions, sendSuggestedAction, isStreaming } = useChatStore()

  if (!suggestedActions.length) return null

  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {suggestedActions.map((action, idx) => (
        <button
          key={`${action.text}-${idx}`}
          onClick={() => sendSuggestedAction(action)}
          disabled={isStreaming}
          className="group flex items-center gap-1.5 px-3 py-1.5 text-xs text-zinc-400 border border-zinc-800 rounded-lg hover:text-zinc-200 hover:border-zinc-700 transition-colors disabled:opacity-50"
        >
          <span>{action.text}</span>
          <ArrowRight size={12} className="text-zinc-600 group-hover:text-zinc-400" />
        </button>
      ))}
    </div>
  )
}
