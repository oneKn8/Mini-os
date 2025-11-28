import { gsap } from './gsap'

/**
 * Create a parallax layer system with multiple depth layers
 */
export function createParallaxLayers(
  layers: Array<{ element: HTMLElement | string; speed: number }>
) {
  const animations = layers.map((layer) => {
    return gsap.to(layer.element, {
      y: () => window.innerHeight * layer.speed,
      ease: 'none',
      scrollTrigger: {
        trigger: layer.element,
        start: 'top bottom',
        end: 'bottom top',
        scrub: true,
      },
    })
  })

  return () => {
    animations.forEach((anim) => anim.kill())
  }
}

/**
 * Parallax background with multiple layers
 */
export function parallaxBackground(
  container: HTMLElement | string,
  layers: Array<{ selector: string; speed: number }>
) {
  const animations = layers.map((layer) => {
    return gsap.to(layer.selector, {
      y: () => window.innerHeight * layer.speed,
      ease: 'none',
      scrollTrigger: {
        trigger: container,
        start: 'top bottom',
        end: 'bottom top',
        scrub: true,
      },
    })
  })

  return () => {
    animations.forEach((anim) => anim.kill())
  }
}

/**
 * Mouse-based parallax for SVG elements
 */
export function svgMouseParallax(
  _svgElement: SVGSVGElement | string,
  elements: Array<{ selector: string; intensity: number }>
) {
  const handleMouseMove = (e: MouseEvent) => {
    const x = (e.clientX / window.innerWidth - 0.5) * 100
    const y = (e.clientY / window.innerHeight - 0.5) * 100

    elements.forEach(({ selector, intensity }) => {
      gsap.to(selector, {
        x: x * intensity,
        y: y * intensity,
        duration: 0.5,
        ease: 'power2.out',
      })
    })
  }

  window.addEventListener('mousemove', handleMouseMove)

  return () => {
    window.removeEventListener('mousemove', handleMouseMove)
    elements.forEach(({ selector }) => {
      gsap.to(selector, { x: 0, y: 0, duration: 0.5 })
    })
  }
}

