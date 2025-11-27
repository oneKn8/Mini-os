import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { pageTransition } from '../../utils/gsap'

interface PageTransitionProps {
  children: React.ReactNode
}

export default function PageTransition({ children }: PageTransitionProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const location = useLocation()

  useEffect(() => {
    if (containerRef.current) {
      pageTransition(containerRef.current, 'in')
    }
  }, [location.pathname])

  return (
    <div ref={containerRef} className="h-full w-full relative z-50">
      {children}
    </div>
  )
}
