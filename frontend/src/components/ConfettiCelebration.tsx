import { useEffect, useState } from 'react'
import { create } from 'zustand'
import { useSettingsStore } from '../store/settingsStore'

// Confetti store for triggering celebrations
interface ConfettiStore {
  isActive: boolean
  origin: { x: number; y: number }
  trigger: (x?: number, y?: number) => void
  clear: () => void
}

export const useConfettiStore = create<ConfettiStore>((set) => ({
  isActive: false,
  origin: { x: 0.5, y: 0.5 },
  trigger: (x = 0.5, y = 0.5) => {
    set({ isActive: true, origin: { x, y } })
    // Auto-clear after animation
    setTimeout(() => set({ isActive: false }), 2000)
  },
  clear: () => set({ isActive: false }),
}))

// Helper to trigger confetti from anywhere
export const triggerConfetti = (x?: number, y?: number) => {
  useConfettiStore.getState().trigger(x, y)
}

// Confetti particle component
function Particle({ 
  index, 
  originX, 
  originY 
}: { 
  index: number
  originX: number
  originY: number 
}) {
  const colors = [
    'bg-blue-400/80',
    'bg-violet-400/80',
    'bg-emerald-400/80',
    'bg-amber-400/80',
    'bg-rose-400/80',
  ]

  const color = colors[index % colors.length]
  const angle = (index * 137.5) % 360 // Golden angle distribution
  const distance = 50 + Math.random() * 100
  const duration = 0.8 + Math.random() * 0.6
  const delay = Math.random() * 0.2
  const size = 4 + Math.random() * 4

  const endX = Math.cos((angle * Math.PI) / 180) * distance
  const endY = Math.sin((angle * Math.PI) / 180) * distance + 50 // Gravity

  return (
    <div
      className={`absolute rounded-full ${color}`}
      style={{
        width: size,
        height: size,
        left: `${originX * 100}%`,
        top: `${originY * 100}%`,
        animation: `confetti-fall ${duration}s ease-out ${delay}s forwards`,
        ['--end-x' as string]: `${endX}px`,
        ['--end-y' as string]: `${endY}px`,
        ['--rotation' as string]: `${Math.random() * 720 - 360}deg`,
      }}
    />
  )
}

// Main confetti component
export function ConfettiCelebration() {
  const { isActive, origin } = useConfettiStore()
  const { confettiEnabled, reducedMotion } = useSettingsStore()
  const [particles, setParticles] = useState<number[]>([])

  useEffect(() => {
    if (isActive && confettiEnabled && !reducedMotion) {
      // Create particles
      setParticles(Array.from({ length: 30 }, (_, i) => i))
    } else {
      setParticles([])
    }
  }, [isActive, confettiEnabled, reducedMotion])

  if (!confettiEnabled || reducedMotion || particles.length === 0) {
    return null
  }

  return (
    <>
      {/* CSS for confetti animation */}
      <style>{`
        @keyframes confetti-fall {
          0% {
            transform: translate(0, 0) rotate(0deg) scale(1);
            opacity: 1;
          }
          100% {
            transform: translate(var(--end-x), var(--end-y)) rotate(var(--rotation)) scale(0);
            opacity: 0;
          }
        }
      `}</style>
      
      {/* Confetti container */}
      <div className="fixed inset-0 pointer-events-none z-[9997] overflow-hidden">
        {particles.map((i) => (
          <Particle key={i} index={i} originX={origin.x} originY={origin.y} />
        ))}
      </div>
    </>
  )
}

export default ConfettiCelebration

