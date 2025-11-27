import { useState, useEffect, useRef } from 'react'
import { ChevronDown, MessageSquare, Plus, Cpu } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'

const MODELS = [
  { id: 'gpt-5', name: 'GPT-5', provider: 'openai' },
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai' },
  { id: 'meta/llama-3.1-70b-instruct', name: 'Llama 70B', provider: 'nvidia' },
  { id: 'meta/llama-3.1-8b-instruct', name: 'Llama 8B', provider: 'nvidia' },
]

export default function ChatHeader() {
  const { sessions, loadSessions, loadHistory, clearHistory, currentSessionId, selectedModel, setModel } = useChatStore()
  const [isHistoryOpen, setIsHistoryOpen] = useState(false)
  const [isModelOpen, setIsModelOpen] = useState(false)
  const historyRef = useRef<HTMLDivElement>(null)
  const modelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isHistoryOpen) loadSessions()
  }, [isHistoryOpen]) // eslint-disable-line

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (historyRef.current && !historyRef.current.contains(e.target as Node)) setIsHistoryOpen(false)
      if (modelRef.current && !modelRef.current.contains(e.target as Node)) setIsModelOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const currentSession = sessions.find(s => s.id === currentSessionId)
  const title = currentSession?.title || "New Chat"
  const activeModel = selectedModel ? MODELS.find(m => m.id === selectedModel.name) : MODELS[0]

  return (
    <div className="relative flex items-center justify-between px-3 py-2 bg-zinc-950">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {/* History */}
        <div ref={historyRef} className="relative">
          <button 
            onClick={() => { setIsHistoryOpen(!isHistoryOpen); setIsModelOpen(false) }}
            className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-sm text-zinc-300 hover:bg-zinc-900 transition-colors"
          >
            <span className="font-medium truncate max-w-[120px]">{title}</span>
            <ChevronDown size={12} className={`text-zinc-600 transition-transform ${isHistoryOpen ? 'rotate-180' : ''}`} />
          </button>

          {isHistoryOpen && (
            <div className="absolute top-full left-0 mt-1 w-52 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl z-50 overflow-hidden">
              <div className="px-3 py-2 text-[10px] text-zinc-600 uppercase tracking-wide border-b border-zinc-800">
                History
              </div>
              <div className="max-h-48 overflow-y-auto">
                {sessions.length === 0 ? (
                  <div className="px-3 py-4 text-xs text-zinc-600 text-center">No history</div>
                ) : (
                  sessions.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => { loadHistory(s.id); setIsHistoryOpen(false) }}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center gap-2 hover:bg-zinc-800 transition-colors ${
                        currentSessionId === s.id ? 'text-zinc-200 bg-zinc-800/50' : 'text-zinc-400'
                      }`}
                    >
                      <MessageSquare size={12} />
                      <span className="truncate">{s.title}</span>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Model */}
        <div ref={modelRef} className="relative">
          <button
            onClick={() => { setIsModelOpen(!isModelOpen); setIsHistoryOpen(false) }}
            className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900 transition-colors"
          >
            <Cpu size={12} />
            <span className="hidden sm:inline">{activeModel?.name || 'Model'}</span>
            <ChevronDown size={10} className={`transition-transform ${isModelOpen ? 'rotate-180' : ''}`} />
          </button>

          {isModelOpen && (
            <div className="absolute top-full left-0 mt-1 w-44 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl z-50 overflow-hidden">
              <div className="px-3 py-2 text-[10px] text-zinc-600 uppercase tracking-wide border-b border-zinc-800">
                Model
              </div>
              {MODELS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => { setModel(m.provider, m.id); setIsModelOpen(false) }}
                  className={`w-full text-left px-3 py-2 text-xs hover:bg-zinc-800 transition-colors ${
                    selectedModel?.name === m.id ? 'text-zinc-200 bg-zinc-800/50' : 'text-zinc-400'
                  }`}
                >
                  <div>{m.name}</div>
                  <div className="text-[10px] text-zinc-600">{m.provider}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <button 
        onClick={() => { clearHistory(); setIsHistoryOpen(false) }}
        className="p-1.5 text-zinc-600 hover:text-zinc-400 hover:bg-zinc-900 rounded-lg transition-colors"
        title="New Chat"
      >
        <Plus size={16} />
      </button>
    </div>
  )
}
