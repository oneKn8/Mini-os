import { useEffect, useRef } from 'react'
import { gsap } from '../../utils/gsap'

interface LoadingSpinnerProps {
  size?: number
  className?: string
}

export default function LoadingSpinner({ size = 40, className = '' }: LoadingSpinnerProps) {
  const spinnerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (spinnerRef.current) {
      gsap.to(spinnerRef.current, {
        rotation: 360,
        duration: 1,
        repeat: -1,
        ease: 'none',
      })
    }
  }, [])

  return (
    <div
      ref={spinnerRef}
      className={`border-4 border-white/20 border-t-accent-primary rounded-full ${className}`}
      style={{ width: size, height: size }}
    />
  )
}

