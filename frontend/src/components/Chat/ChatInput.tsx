import { useState, FormEvent } from 'react'
import { Send, Paperclip, Mic, StopCircle, AtSign } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'
import { clsx } from 'clsx'

export default function ChatInput() {
  const [input, setInput] = useState('')
  const { sendMessage, isStreaming } = useChatStore()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return

    const content = input
    setInput('')
    
    // Capture current URL as context
    const context = {
        currentView: window.location.pathname
    }
    
    await sendMessage(content, context)
  }

  return (
    <form onSubmit={handleSubmit} className="relative flex flex-col gap-2">
        <div className="relative">
            <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isStreaming}
                placeholder={isStreaming ? "Agent is working..." : "Ask anything..."}
                className="w-full rounded-xl border border-border-medium bg-bg-secondary px-4 py-3 pr-12 text-sm text-text-primary placeholder-text-muted focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary disabled:opacity-60 disabled:cursor-not-allowed transition-all"
            />
            
            {/* Send / Stop Button */}
            <div className="absolute right-2 top-1/2 -translate-y-1/2">
                {isStreaming ? (
                    <button
                        type="button"
                        className="p-2 text-text-secondary hover:text-accent-error transition-colors"
                        title="Stop generating (Coming soon)"
                    >
                        <StopCircle size={18} />
                    </button>
                ) : (
                    <button
                        type="submit"
                        disabled={!input.trim()}
                        className={clsx(
                            "p-2 rounded-lg transition-colors",
                            input.trim() 
                                ? "text-white bg-accent-primary hover:bg-accent-primary-hover shadow-sm" 
                                : "text-text-tertiary hover:bg-bg-secondary"
                        )}
                    >
                        <Send size={16} />
                    </button>
                )}
            </div>
        </div>

        {/* Input Controls Toolbar */}
        <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-1">
                <button type="button" className="p-1.5 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-bg-secondary transition-colors" title="Attach file">
                    <Paperclip size={16} />
                </button>
                <button type="button" className="p-1.5 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-bg-secondary transition-colors" title="Voice input">
                    <Mic size={16} />
                </button>
                <button type="button" className="p-1.5 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-bg-secondary transition-colors" title="Mention context">
                    <AtSign size={16} />
                </button>
            </div>
            
            <span className="text-[10px] text-text-tertiary hidden sm:inline-block">
                <strong>Return</strong> to send, <strong>Shift+Return</strong> for new line
            </span>
        </div>
    </form>
  )
}
