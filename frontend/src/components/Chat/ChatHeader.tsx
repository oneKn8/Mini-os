import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, MessageSquare, Plus, Settings, Cpu } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'
import { clsx } from 'clsx'

const AVAILABLE_MODELS = [
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai' },
    { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai' },
    { id: 'meta/llama3-70b-instruct', name: 'Llama 3 70B (NVIDIA)', provider: 'nvidia' },
    { id: 'nvidia/nemo', name: 'NeMo (NVIDIA)', provider: 'nvidia' }, // Assuming supported by provider
]

export default function ChatHeader() {
  const { sessions, loadSessions, loadHistory, clearHistory, currentSessionId, selectedModel, setModel } = useChatStore()
  const [isHistoryOpen, setIsHistoryOpen] = useState(false)
  const [isModelOpen, setIsModelOpen] = useState(false)

  useEffect(() => {
      if (isHistoryOpen) {
          loadSessions()
      }
  }, [isHistoryOpen])

  const handleSelectSession = (sessionId: string) => {
      loadHistory(sessionId)
      setIsHistoryOpen(false)
  }

  const handleNewChat = () => {
      clearHistory()
      setIsHistoryOpen(false)
  }

  const handleModelSelect = (model: typeof AVAILABLE_MODELS[0]) => {
      setModel(model.provider, model.id)
      setIsModelOpen(false)
  }

  // Find current session title
  const currentSession = sessions.find(s => s.id === currentSessionId)
  const title = currentSession?.title || "New Chat"
  
  const activeModel = AVAILABLE_MODELS.find(m => m.id === selectedModel?.name) || AVAILABLE_MODELS[0]

  return (
    <div className="relative flex items-center justify-between border-b border-border-light px-4 py-3 bg-surface shadow-sm z-20">
        <div className="flex items-center gap-2 min-w-0 flex-1">
            {/* History Toggle */}
            <button 
                onClick={() => { setIsHistoryOpen(!isHistoryOpen); setIsModelOpen(false); }}
                className="flex items-center gap-2 px-2 py-1.5 -ml-2 rounded-lg hover:bg-bg-secondary transition-colors max-w-[60%]"
            >
                <span className="font-semibold text-sm text-text-primary truncate">{title}</span>
                <ChevronDown size={14} className={clsx("text-text-tertiary transition-transform shrink-0", isHistoryOpen && "rotate-180")} />
            </button>

            {/* Model Selector */}
            <button 
                onClick={() => { setIsModelOpen(!isModelOpen); setIsHistoryOpen(false); }}
                className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg hover:bg-bg-secondary transition-colors border border-transparent hover:border-border-light"
            >
                <Cpu size={14} className="text-text-tertiary" />
                <span className="text-xs text-text-secondary hidden sm:inline-block">{activeModel.name}</span>
                <ChevronDown size={12} className={clsx("text-text-tertiary transition-transform shrink-0", isModelOpen && "rotate-180")} />
            </button>
        </div>

        <button 
            onClick={handleNewChat}
            className="p-2 text-text-secondary hover:bg-bg-secondary rounded-lg transition-colors"
            title="New Chat"
        >
            <Plus size={18} />
        </button>

        {/* History Dropdown */}
        <AnimatePresence>
            {isHistoryOpen && (
                <>
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsHistoryOpen(false)}
                        className="fixed inset-0 bg-black/20 z-30"
                    />
                    <motion.div
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ duration: 0.15 }}
                        className="absolute top-full left-4 mt-1 w-64 bg-surface rounded-xl border border-border-light shadow-xl z-40 overflow-hidden flex flex-col max-h-80"
                    >
                        <div className="px-3 py-2 border-b border-border-light text-xs font-medium text-text-tertiary uppercase tracking-wider">
                            Recent Chats
                        </div>
                        <div className="overflow-y-auto flex-1 py-1">
                            {sessions.length === 0 ? (
                                <div className="px-4 py-3 text-sm text-text-muted italic text-center">
                                    No history yet
                                </div>
                            ) : (
                                sessions.map((session) => (
                                    <button
                                        key={session.id}
                                        onClick={() => handleSelectSession(session.id)}
                                        className={clsx(
                                            "w-full text-left px-4 py-2.5 text-sm flex items-center gap-3 hover:bg-bg-secondary transition-colors",
                                            currentSessionId === session.id ? "bg-accent-primary/5 text-accent-primary font-medium" : "text-text-secondary"
                                        )}
                                    >
                                        <MessageSquare size={14} className="shrink-0" />
                                        <span className="truncate">{session.title}</span>
                                    </button>
                                ))
                            )}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>

        {/* Model Dropdown */}
        <AnimatePresence>
            {isModelOpen && (
                <>
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsModelOpen(false)}
                        className="fixed inset-0 bg-black/20 z-30"
                    />
                    <motion.div
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ duration: 0.15 }}
                        className="absolute top-full left-20 mt-1 w-56 bg-surface rounded-xl border border-border-light shadow-xl z-40 overflow-hidden flex flex-col"
                    >
                         <div className="px-3 py-2 border-b border-border-light text-xs font-medium text-text-tertiary uppercase tracking-wider">
                            Select Model
                        </div>
                        <div className="py-1">
                            {AVAILABLE_MODELS.map((model) => (
                                <button
                                    key={model.id}
                                    onClick={() => handleModelSelect(model)}
                                    className={clsx(
                                        "w-full text-left px-4 py-2 text-sm flex flex-col hover:bg-bg-secondary transition-colors",
                                        (selectedModel?.name === model.id || (!selectedModel && model.id === 'gpt-4o-mini')) ? "bg-accent-primary/5 text-accent-primary font-medium" : "text-text-primary"
                                    )}
                                >
                                    <span>{model.name}</span>
                                    <span className="text-[10px] text-text-tertiary uppercase">{model.provider}</span>
                                </button>
                            ))}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    </div>
  )
}
