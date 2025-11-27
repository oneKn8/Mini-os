import { useState, useRef, useEffect, FormEvent, KeyboardEvent } from 'react'
import { Send, Mic, MicOff, Square, Slash } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'
import { useVoiceInput } from '../../hooks/useVoiceInput'

const COMMANDS = [
  { trigger: '/plan', label: 'Plan my day' },
  { trigger: '/weather', label: 'Check weather' },
  { trigger: '/email', label: 'Email actions' },
  { trigger: '/calendar', label: 'Calendar' },
  { trigger: '/priority', label: 'Priority items' },
]

export default function ChatInput() {
  const [input, setInput] = useState('')
  const [suggestions, setSuggestions] = useState<typeof COMMANDS>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { sendMessage, isStreaming } = useChatStore()
  
  const {
    isListening,
    isSupported: voiceSupported,
    interimTranscript,
    toggleListening,
    clearTranscript,
  } = useVoiceInput({
    onResult: (text, isFinal) => {
      if (isFinal) {
        setInput(prev => prev + text)
        clearTranscript()
      }
    },
  })

  // Auto-resize
  useEffect(() => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.min(el.scrollHeight, 120)}px`
    }
  }, [input])

  // Command suggestions
  useEffect(() => {
    if (input.startsWith('/')) {
      const q = input.slice(1).toLowerCase()
      const filtered = COMMANDS.filter(c => c.trigger.includes(q) || c.label.toLowerCase().includes(q))
      setSuggestions(filtered)
      setSelectedIndex(0)
    } else {
      setSuggestions([])
    }
  }, [input])

  const insertCommand = (cmd: typeof COMMANDS[0]) => {
    setInput(cmd.trigger + ' ')
    setSuggestions([])
    textareaRef.current?.focus()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(i => (i + 1) % suggestions.length)
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(i => (i - 1 + suggestions.length) % suggestions.length)
        return
      }
      if (e.key === 'Tab' || (e.key === 'Enter' && !e.shiftKey)) {
        e.preventDefault()
        insertCommand(suggestions[selectedIndex])
        return
      }
      if (e.key === 'Escape') {
        setSuggestions([])
        return
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleSubmit = async (e?: FormEvent) => {
    e?.preventDefault()
    if (!input.trim() || isStreaming) return

    const content = input.trim()
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    
    await sendMessage(content, { currentView: window.location.pathname })
  }

  return (
    <form onSubmit={handleSubmit} className="relative">
      {/* Command suggestions */}
      {suggestions.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 mb-1 bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
          {suggestions.map((cmd, i) => (
            <button
              key={cmd.trigger}
              type="button"
              onClick={() => insertCommand(cmd)}
              className={`w-full flex items-center gap-2 px-3 py-2 text-left text-sm transition-colors ${
                i === selectedIndex ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-400 hover:bg-zinc-800/50'
              }`}
            >
              <Slash size={12} className="text-zinc-600" />
              <span className="text-zinc-300">{cmd.trigger}</span>
              <span className="text-zinc-600 text-xs">{cmd.label}</span>
            </button>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            placeholder={
              isListening ? (interimTranscript || 'Listening...') 
              : isStreaming ? 'Working...' 
              : 'Message...'
            }
            rows={1}
            className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-2.5 pr-20 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-700 disabled:opacity-50 resize-none"
          />
          
          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            {voiceSupported && (
              <button
                type="button"
                onClick={toggleListening}
                className={`p-1.5 rounded-lg transition-colors ${
                  isListening ? 'text-red-400' : 'text-zinc-600 hover:text-zinc-400'
                }`}
              >
                {isListening ? <MicOff size={16} /> : <Mic size={16} />}
              </button>
            )}
            
            {isStreaming ? (
              <button type="button" className="p-1.5 text-zinc-600">
                <Square size={16} />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className={`p-1.5 rounded-lg transition-colors ${
                  input.trim() ? 'text-zinc-100 bg-zinc-700 hover:bg-zinc-600' : 'text-zinc-700'
                }`}
              >
                <Send size={16} />
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end mt-1.5 text-[10px] text-zinc-600">
        <span>
          <kbd className="px-1 py-0.5 bg-zinc-900 rounded">↵</kbd> send
          <span className="mx-1.5">·</span>
          <kbd className="px-1 py-0.5 bg-zinc-900 rounded">⇧↵</kbd> newline
        </span>
      </div>
    </form>
  )
}
