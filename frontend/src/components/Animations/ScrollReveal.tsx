import { useEffect, useRef, ReactNode } from 'react'
import { scrollReveal, animations } from '../../utils/gsap'

interface ScrollRevealProps {
  children: ReactNode
  animation?: 'fadeIn' | 'fadeInUp' | 'fadeInDown' | 'scaleIn' | 'slideInLeft' | 'slideInRight'
  delay?: number
  className?: string
}

const animationMap = {
  fadeIn: animations.fadeIn,
  fadeInUp: animations.fadeInUp,
  fadeInDown: animations.fadeInDown,
  scaleIn: animations.scaleIn,
  slideInLeft: animations.slideInLeft,
  slideInRight: animations.slideInRight,
}

export default function ScrollReveal({
  children,
  animation = 'fadeInUp',
  delay = 0,
  className = '',
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) {
      const anim = scrollReveal(ref.current, {
        ...animationMap[animation],
        delay,
      })

      return () => {
        anim.kill()
      }
    }
  }, [animation, delay])

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  )
}

