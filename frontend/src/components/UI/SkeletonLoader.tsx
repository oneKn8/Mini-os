import { useEffect, useRef } from 'react'
import { gsap } from '../../utils/gsap'
import { clsx } from 'clsx'

interface SkeletonLoaderProps {
  className?: string
  variant?: 'text' | 'rect' | 'circle'
  width?: string | number
  height?: string | number
}

export default function SkeletonLoader({
  className = '',
  variant = 'rect',
  width,
  height,
}: SkeletonLoaderProps) {
  const skeletonRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (skeletonRef.current) {
      gsap.to(skeletonRef.current, {
        opacity: 0.5,
        duration: 1,
        yoyo: true,
        repeat: -1,
        ease: 'power1.inOut',
      })
    }
  }, [])

  const baseClasses = 'bg-white/10 rounded'
  const variantClasses = {
    text: 'h-4',
    rect: '',
    circle: 'rounded-full',
  }

  return (
    <div
      ref={skeletonRef}
      className={clsx(baseClasses, variantClasses[variant], className)}
      style={{
        width: width || (variant === 'circle' ? height : '100%'),
        height: height || (variant === 'circle' ? width : 'auto'),
      }}
    />
  )
}

