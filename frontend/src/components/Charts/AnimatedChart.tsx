import { useEffect, useRef } from 'react'
import { gsap } from '../../utils/gsap'

interface AnimatedChartProps {
  children: React.ReactNode
  data: unknown[]
  className?: string
}

export default function AnimatedChart({ children, data, className = '' }: AnimatedChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (chartRef.current && data.length > 0) {
      gsap.fromTo(chartRef.current,
        {
          opacity: 0,
          scale: 0.98,
        },
        {
          opacity: 1,
          scale: 1,
          duration: 0.5,
          ease: 'power2.out',
        }
      )
    }
  }, [data])

  return (
    <div
      ref={chartRef}
      className={`${className}`}
      style={{
        width: '100%',
        height: '100%',
        minWidth: 0,
        minHeight: 0,
        position: 'relative',
        opacity: data.length > 0 ? 1 : 0.3
      }}
    >
      {children}
    </div>
  )
}
