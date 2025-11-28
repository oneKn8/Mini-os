import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle } from 'lucide-react'
import { useScreenController } from '../store/screenController'
import { useSettingsStore } from '../store/settingsStore'

export function ThoughtBubble() {
  const { currentThought, thoughtPosition, thoughtVisible, agentActive } = useScreenController()
  const { thoughtBubbles, showReasoning, reducedMotion } = useSettingsStore()

  // Don't show if disabled
  if (!thoughtBubbles || showReasoning === 'never' || !agentActive) {
    return null
  }

  return (
    <AnimatePresence>
      {thoughtVisible && currentThought && (
        <motion.div
          className="fixed z-[9998] pointer-events-none max-w-xs"
          style={{
            left: Math.min(thoughtPosition.x, window.innerWidth - 280),
            top: Math.max(thoughtPosition.y, 60),
          }}
          initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 10, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={reducedMotion ? { opacity: 0 } : { opacity: 0, y: -5, scale: 0.95 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
        >
          {/* Bubble */}
          <div className="bg-zinc-900/95 backdrop-blur-sm border border-zinc-800/50 
                          rounded-lg px-3 py-2 shadow-lg">
            <span className="text-sm text-zinc-300 leading-relaxed flex items-center gap-1.5">
              <MessageCircle size={12} className="text-zinc-500" />
              {currentThought}
            </span>
          </div>
          
          {/* Tail */}
          <div 
            className="absolute -bottom-1.5 left-4 w-3 h-3 rotate-45 
                       bg-zinc-900/95 border-r border-b border-zinc-800/50"
          />
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default ThoughtBubble

