import { motion, AnimatePresence } from 'framer-motion'
import { useScreenController, type AgentState } from '../store/screenController'
import { useSettingsStore } from '../store/settingsStore'

// State-based colors (muted, minimal)
const stateColors: Record<AgentState, { outer: string; inner: string }> = {
  idle: { outer: 'bg-zinc-500/30', inner: 'bg-zinc-400/50' },
  navigating: { outer: 'bg-blue-500/30', inner: 'bg-blue-400/60' },
  working: { outer: 'bg-violet-500/30', inner: 'bg-violet-400/60' },
  waiting: { outer: 'bg-amber-500/30', inner: 'bg-amber-400/60' },
}

export function AgentCursor() {
  const { cursorPosition, agentActive, agentState, agentPaused } = useScreenController()
  const { agentCursor, reducedMotion, agentSpeed } = useSettingsStore()

  // Don't show if disabled or no position
  if (!agentCursor || !agentActive || !cursorPosition) {
    return null
  }

  const colors = stateColors[agentState]
  
  // Animation speed based on settings
  const getSpringConfig = () => {
    if (reducedMotion) return { duration: 0.1 }
    switch (agentSpeed) {
      case 'slow': return { type: 'spring' as const, damping: 30, stiffness: 100 }
      case 'normal': return { type: 'spring' as const, damping: 25, stiffness: 200 }
      case 'fast': return { type: 'spring' as const, damping: 20, stiffness: 400 }
      case 'instant': return { duration: 0.05 }
    }
  }

  return (
    <AnimatePresence>
      {!agentPaused && (
        <motion.div
          className="fixed pointer-events-none z-[9999]"
          initial={{ opacity: 0, scale: 0 }}
          animate={{
            opacity: 1,
            scale: 1,
            x: cursorPosition.x - 12,
            y: cursorPosition.y - 12,
          }}
          exit={{ opacity: 0, scale: 0 }}
          transition={getSpringConfig()}
        >
          {/* Outer glow */}
          <motion.div
            className={`w-6 h-6 rounded-full ${colors.outer} blur-sm`}
            animate={{
              scale: agentState === 'waiting' ? [1, 1.2, 1] : 1,
            }}
            transition={{
              repeat: agentState === 'waiting' ? Infinity : 0,
              duration: 1.5,
              ease: 'easeInOut',
            }}
          />
          
          {/* Inner dot */}
          <div
            className={`absolute top-1.5 left-1.5 w-3 h-3 rounded-full ${colors.inner}`}
          />

          {/* Ripple effect when working */}
          {agentState === 'working' && !reducedMotion && (
            <motion.div
              className="absolute -top-1 -left-1 w-8 h-8 rounded-full border border-violet-400/30"
              initial={{ scale: 0.8, opacity: 0.5 }}
              animate={{ scale: 1.5, opacity: 0 }}
              transition={{
                repeat: Infinity,
                duration: 1,
                ease: 'easeOut',
              }}
            />
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default AgentCursor

