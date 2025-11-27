import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger)

// Common animation presets
export const animations = {
  fadeIn: {
    opacity: 0,
    y: 20,
    duration: 0.6,
    ease: 'power2.out',
  },
  fadeInUp: {
    opacity: 0,
    y: 30,
    duration: 0.8,
    ease: 'power3.out',
  },
  fadeInDown: {
    opacity: 0,
    y: -30,
    duration: 0.8,
    ease: 'power3.out',
  },
  scaleIn: {
    opacity: 0,
    scale: 0.9,
    duration: 0.5,
    ease: 'back.out(1.7)',
  },
  slideInLeft: {
    opacity: 0,
    x: -50,
    duration: 0.6,
    ease: 'power2.out',
  },
  slideInRight: {
    opacity: 0,
    x: 50,
    duration: 0.6,
    ease: 'power2.out',
  },
}

/**
 * Animate elements on mount
 */
export function animateOnMount(
  selector: string | HTMLElement,
  animation: gsap.TweenVars = animations.fadeIn
) {
  return gsap.from(selector, {
    ...animation,
    opacity: animation.opacity ?? 1,
  })
}

/**
 * Stagger animation for list items
 */
export function staggerAnimation(
  selector: string | HTMLElement[],
  animation: gsap.TweenVars = animations.fadeIn,
  stagger: number = 0.1
) {
  return gsap.from(selector, {
    ...animation,
    opacity: animation.opacity ?? 1,
    stagger,
  })
}

/**
 * Create scroll-triggered animation
 */
export function scrollReveal(
  selector: string | HTMLElement,
  animation: gsap.TweenVars = animations.fadeInUp,
  options?: ScrollTrigger.Vars
) {
  return gsap.from(selector, {
    ...animation,
    opacity: animation.opacity ?? 1,
    scrollTrigger: {
      trigger: selector,
      start: 'top 80%',
      toggleActions: 'play none none none',
      ...options,
    },
  })
}

/**
 * Animate counter from 0 to target value
 */
export function animateCounter(
  element: HTMLElement,
  targetValue: number,
  duration: number = 1,
  suffix: string = ''
) {
  const obj = { value: 0 }
  return gsap.to(obj, {
    value: targetValue,
    duration,
    ease: 'power2.out',
    onUpdate: () => {
      element.textContent = Math.round(obj.value) + suffix
    },
  })
}

/**
 * Parallax effect on scroll
 */
export function parallaxScroll(
  element: HTMLElement | string,
  speed: number = 0.5,
  direction: 'y' | 'x' = 'y'
) {
  return gsap.to(element, {
    [direction]: () => window.innerHeight * speed,
    ease: 'none',
    scrollTrigger: {
      trigger: element,
      start: 'top bottom',
      end: 'bottom top',
      scrub: true,
    },
  })
}

/**
 * Mouse parallax effect
 */
export function mouseParallax(
  element: HTMLElement | string,
  intensity: number = 0.1,
  axis: 'x' | 'y' | 'both' = 'both'
) {
  const handleMouseMove = (e: MouseEvent) => {
    const x = (e.clientX / window.innerWidth - 0.5) * intensity * 100
    const y = (e.clientY / window.innerHeight - 0.5) * intensity * 100

    if (axis === 'x' || axis === 'both') {
      gsap.to(element, { x, duration: 0.5, ease: 'power2.out' })
    }
    if (axis === 'y' || axis === 'both') {
      gsap.to(element, { y, duration: 0.5, ease: 'power2.out' })
    }
  }

  window.addEventListener('mousemove', handleMouseMove)

  return () => {
    window.removeEventListener('mousemove', handleMouseMove)
    gsap.to(element, { x: 0, y: 0, duration: 0.5 })
  }
}

/**
 * Hover scale animation
 */
export function hoverScale(
  element: HTMLElement | string,
  scale: number = 1.05,
  duration: number = 0.3
) {
  const el = typeof element === 'string' ? document.querySelector(element) : element
  if (!el) return

  const handleMouseEnter = () => {
    gsap.to(element, { scale, duration, ease: 'power2.out' })
  }

  const handleMouseLeave = () => {
    gsap.to(element, { scale: 1, duration, ease: 'power2.out' })
  }

  el.addEventListener('mouseenter', handleMouseEnter)
  el.addEventListener('mouseleave', handleMouseLeave)

  return () => {
    el.removeEventListener('mouseenter', handleMouseEnter)
    el.removeEventListener('mouseleave', handleMouseLeave)
  }
}

/**
 * Page transition animation
 */
export function pageTransition(
  element: HTMLElement | string,
  direction: 'in' | 'out' = 'in'
) {
  if (direction === 'in') {
    return gsap.from(element, {
      opacity: 0,
      y: 20,
      scale: 0.98,
      duration: 0.4,
      ease: 'power2.out',
    })
  } else {
    return gsap.to(element, {
      opacity: 0,
      y: -20,
      scale: 1.02,
      duration: 0.3,
      ease: 'power2.in',
    })
  }
}

/**
 * Cleanup function for GSAP animations
 */
export function cleanupAnimations() {
  ScrollTrigger.getAll().forEach((trigger) => trigger.kill())
}

// Export gsap as both named and default export
export { gsap }
export default gsap

