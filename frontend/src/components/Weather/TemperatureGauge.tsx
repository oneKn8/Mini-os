import { useEffect, useRef } from 'react'
import { gsap } from '../../utils/gsap'

interface TemperatureGaugeProps {
  temperature: number
  min?: number
  max?: number
  size?: number
}

export default function TemperatureGauge({ 
  temperature, 
  min = -20, 
  max = 120,
  size = 200 
}: TemperatureGaugeProps) {
  const gaugeRef = useRef<SVGSVGElement>(null)
  const needleRef = useRef<SVGLineElement>(null)
  const valueRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (gaugeRef.current && needleRef.current && valueRef.current) {
      // Calculate angle (0-180 degrees for semicircle)
      const range = max - min
      const normalized = (temperature - min) / range
      const angle = normalized * 180 - 90 // -90 to 90 degrees

      // Animate needle
      gsap.to(needleRef.current, {
        rotation: angle,
        transformOrigin: 'center center',
        duration: 1.5,
        ease: 'power2.out',
      })

      // Animate value counter
      const obj = { value: min }
      gsap.to(obj, {
        value: temperature,
        duration: 1.5,
        ease: 'power2.out',
        onUpdate: () => {
          if (valueRef.current) {
            valueRef.current.textContent = Math.round(obj.value) + '°'
          }
        },
      })
    }
  }, [temperature, min, max])

  const centerX = size / 2
  const centerY = size / 2
  const radius = size * 0.4

  return (
    <div className="relative">
      <svg
        ref={gaugeRef}
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* Background arc */}
        <path
          d={`M ${centerX - radius} ${centerY} A ${radius} ${radius} 0 0 1 ${centerX + radius} ${centerY}`}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="8"
        />
        {/* Temperature arc */}
        <path
          d={`M ${centerX - radius} ${centerY} A ${radius} ${radius} 0 0 1 ${centerX + radius} ${centerY}`}
          fill="none"
          stroke="url(#tempGradient)"
          strokeWidth="8"
          strokeDasharray={`${(temperature - min) / (max - min) * Math.PI * radius} ${Math.PI * radius}`}
        />
        {/* Needle */}
        <line
          ref={needleRef}
          x1={centerX}
          y1={centerY}
          x2={centerX}
          y2={centerY - radius + 20}
          stroke="#4c6ef5"
          strokeWidth="3"
          strokeLinecap="round"
        />
        <defs>
          <linearGradient id="tempGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="50%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#f59e0b" />
          </linearGradient>
        </defs>
      </svg>
      <div
        ref={valueRef}
        className="absolute inset-0 flex items-center justify-center text-3xl font-bold text-white"
      >
        {temperature}°
      </div>
    </div>
  )
}

