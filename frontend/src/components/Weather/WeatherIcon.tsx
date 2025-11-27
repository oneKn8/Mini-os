import { useEffect, useRef } from 'react'
import { Cloud, Sun, Wind, Droplets, CloudRain, CloudLightning, Snowflake, Moon } from 'lucide-react'
import { gsap } from '../../utils/gsap'

interface WeatherIconProps {
  condition: string
  timeOfDay: 'day' | 'night' | 'dusk' | 'dawn'
  size?: number
  className?: string
}

export default function WeatherIcon({ condition, timeOfDay, size = 80, className = '' }: WeatherIconProps) {
  const iconRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (iconRef.current) {
      // Animate icon on mount
      gsap.from(iconRef.current, {
        opacity: 0,
        scale: 0.5,
        rotation: -180,
        duration: 1,
        ease: 'back.out(1.7)',
      })

      // Continuous pulse animation
      gsap.to(iconRef.current, {
        scale: 1.1,
        duration: 2,
        yoyo: true,
        repeat: -1,
        ease: 'power1.inOut',
      })
    }
  }, [condition])

  const getIcon = () => {
    const lower = condition?.toLowerCase() || ''
    if (lower.includes('rain')) return CloudRain
    if (lower.includes('storm')) return CloudLightning
    if (lower.includes('snow')) return Snowflake
    if (lower.includes('cloud')) return Cloud
    if (timeOfDay === 'night') return Moon
    return Sun
  }

  const Icon = getIcon()

  return (
    <Icon
      ref={iconRef}
      size={size}
      className={className}
      strokeWidth={1}
    />
  )
}

