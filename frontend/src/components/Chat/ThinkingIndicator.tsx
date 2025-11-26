import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'
import { clsx } from 'clsx'
import ProcessStep from './ProcessStep'

export default function ThinkingIndicator() {
  const { currentThoughts, isStreaming } = useChatStore()
  const [isExpanded, setIsExpanded] = useState(true)
  const [elapsed, setElapsed] = useState(0)

  // Auto-expand when streaming starts
  useEffect(() => {
      if (isStreaming) {
          setIsExpanded(true)
          setElapsed(0)
      }
  }, [isStreaming])

  useEffect(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let interval: any
      if (isStreaming) {
        interval = setInterval(() => {
            setElapsed(e => e + 0.1)
        }, 100)
      }
      return () => clearInterval(interval)
  }, [isStreaming])

  if (currentThoughts.length === 0 && !isStreaming) return null

  const activeStep = currentThoughts.find(t => t.status === 'running')
  const isDone = !isStreaming && currentThoughts.length > 0

  return (
    <div className="w-full pl-0 mb-4">
      <motion.div 
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        className={clsx(
            "border rounded-lg overflow-hidden bg-surface shadow-sm transition-colors",
            isStreaming ? "border-accent-primary/30" : "border-border-light"
        )}
      >
        <button 
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex w-full items-center justify-between px-3 py-2.5 text-xs font-medium hover:bg-bg-secondary/50 transition-colors"
        >
          <div className="flex items-center gap-2.5">
              <div className="relative flex h-3 w-3 items-center justify-center">
                  {isStreaming ? (
                      <>
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent-primary opacity-75"></span>
                        <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-primary"></span>
                      </>
                  ) : (
                      <span className="h-2 w-2 rounded-full bg-accent-success"></span>
                  )}
              </div>
              <div className="flex flex-col items-start">
                  <span className="font-semibold text-text-primary">
                      {isDone ? "Process Completed" : (activeStep ? `Running ${activeStep.agent}...` : "Thinking...")}
                  </span>
              </div>
              {isStreaming && <span className="text-text-tertiary font-mono ml-2">{elapsed.toFixed(1)}s</span>}
          </div>
          {isExpanded ? <ChevronDown size={14} className="text-text-tertiary" /> : <ChevronRight size={14} className="text-text-tertiary" />}
        </button>
        
        <AnimatePresence>
          {isExpanded && (
              <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="bg-bg-secondary/30 border-t border-border-light divide-y divide-border-light/50"
              >
                  <div className="px-3 py-2">
                    {currentThoughts.length === 0 && isStreaming && (
                        <div className="text-xs text-text-tertiary italic py-2 pl-1">Initializing workflow...</div>
                    )}
                    {currentThoughts.map((thought, idx) => (
                        <ProcessStep key={`${thought.agent}-${idx}`} thought={thought} />
                    ))}
                  </div>
              </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
