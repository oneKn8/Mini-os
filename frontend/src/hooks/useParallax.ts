import { useEffect, useState, useRef } from 'react'
import { mouseParallax, parallaxScroll } from '../utils/gsap'

export function useParallax(speed: number = 0.5) {
  const [offset, setOffset] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const handleScroll = () => {
      setOffset({
        x: window.scrollX * speed,
        y: window.scrollY * speed
      })
    }

    const handleMouseMove = (e: MouseEvent) => {
      const centerX = window.innerWidth / 2
      const centerY = window.innerHeight / 2
      const mouseX = (e.clientX - centerX) * speed * 0.1
      const mouseY = (e.clientY - centerY) * speed * 0.1
      
      setOffset(prev => ({
        x: prev.x + mouseX,
        y: prev.y + mouseY
      }))
    }

    window.addEventListener('scroll', handleScroll)
    window.addEventListener('mousemove', handleMouseMove)
    
    return () => {
      window.removeEventListener('scroll', handleScroll)
      window.removeEventListener('mousemove', handleMouseMove)
    }
  }, [speed])

  return offset
}

/**
 * Enhanced parallax hook with GSAP
 */
export function useGSAPParallax(
  elementRef: React.RefObject<HTMLElement>,
  options: {
    mouseIntensity?: number
    scrollIntensity?: number
    axis?: 'x' | 'y' | 'both'
  } = {}
) {
  const { mouseIntensity = 0.1, scrollIntensity = 0.5, axis = 'both' } = options

  useEffect(() => {
    if (elementRef.current) {
      const cleanupMouse = mouseParallax(elementRef.current, mouseIntensity, axis)
      const scrollAnim = parallaxScroll(elementRef.current, scrollIntensity, 'y')

      return () => {
        cleanupMouse()
        scrollAnim.kill()
      }
    }
  }, [elementRef, mouseIntensity, scrollIntensity, axis])
}

