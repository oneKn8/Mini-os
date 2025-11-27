import { useEffect, useRef, ReactNode } from 'react'
import { mouseParallax, parallaxScroll } from '../../utils/gsap'

interface SVGParallaxProps {
  children: ReactNode
  mouseIntensity?: number
  scrollIntensity?: number
  axis?: 'x' | 'y' | 'both'
  className?: string
}

export default function SVGParallax({
  children,
  mouseIntensity = 0.1,
  scrollIntensity = 0.5,
  axis = 'both',
  className = '',
}: SVGParallaxProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (containerRef.current) {
      // Mouse parallax
      const cleanupMouse = mouseParallax(containerRef.current, mouseIntensity, axis)
      
      // Scroll parallax
      const scrollAnimation = parallaxScroll(containerRef.current, scrollIntensity, 'y')

      return () => {
        cleanupMouse()
        scrollAnimation.kill()
      }
    }
  }, [mouseIntensity, scrollIntensity, axis])

  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  )
}

