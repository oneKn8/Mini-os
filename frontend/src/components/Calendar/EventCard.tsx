import { useEffect, useRef } from 'react'
import { CalendarEvent } from '../../api/calendar'
import { animateOnMount, hoverScale } from '../../utils/gsap'
import { MapPin } from 'lucide-react'

interface EventCardProps {
  event: CalendarEvent
  top: number
  height: number
  onClick?: () => void
  style?: React.CSSProperties
}

export default function EventCard({
  event,
  top,
  height,
  onClick,
  style,
}: EventCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (cardRef.current) {
      animateOnMount(cardRef.current, {
        opacity: 0,
        scale: 0.95,
        duration: 0.3,
        delay: top * 0.01,
      })
      
      const cleanup = hoverScale(cardRef.current, 1.02, 0.2)
      return cleanup
    }
  }, [top])

  const startTime = new Date(event.start).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
  const endTime = new Date(event.end).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div
      ref={cardRef}
      onClick={onClick}
      className="absolute rounded-lg bg-accent-secondary/20 border border-accent-secondary/30 hover:bg-accent-secondary/30 transition-all cursor-pointer group p-2 overflow-hidden"
      style={{
        top: `${top}px`,
        height: `${Math.max(height, 30)}px`,
        ...style,
      }}
    >
      <div className="flex flex-col h-full">
        <div className="flex items-start justify-between mb-1">
          <span className="text-xs font-bold text-accent-secondary">
            {startTime} - {endTime}
          </span>
          {event.location && (
            <MapPin size={10} className="text-text-tertiary opacity-0 group-hover:opacity-100 transition-opacity" />
          )}
        </div>
        <h4 className="text-sm font-bold text-white line-clamp-2 leading-tight">
          {event.title}
        </h4>
        {event.description && (
          <p className="text-xs text-text-tertiary line-clamp-1 mt-1">
            {event.description}
          </p>
        )}
      </div>
    </div>
  )
}

