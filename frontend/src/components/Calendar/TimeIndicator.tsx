import { useEffect, useRef } from 'react'
import { gsap } from '../../utils/gsap'

interface TimeIndicatorProps {
  currentTime: Date
}

export default function TimeIndicator({ currentTime }: TimeIndicatorProps) {
  const indicatorRef = useRef<HTMLDivElement>(null)
  const dotRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const minutes = currentTime.getMinutes()
    const position = minutes * 2 // 2px per minute

    if (indicatorRef.current) {
      gsap.to(indicatorRef.current, {
        top: `${position}px`,
        duration: 0.5,
        ease: 'power2.out',
      })
    }

    if (dotRef.current) {
      gsap.to(dotRef.current, {
        scale: 1.2,
        duration: 0.3,
        yoyo: true,
        repeat: 1,
      })
    }
  }, [currentTime])

  return (
    <div
      ref={indicatorRef}
      className="absolute left-0 right-0 border-t-2 border-accent-error z-10 pointer-events-none"
      style={{ top: `${currentTime.getMinutes() * 2}px` }}
    >
      <div
        ref={dotRef}
        className="absolute -left-1 -top-1.5 w-3 h-3 rounded-full bg-accent-error shadow-[0_0_8px_rgba(239,68,68,0.8)]"
      />
    </div>
  )
}

