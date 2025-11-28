import { useEffect, useRef, useState } from 'react'
import { CalendarEvent } from '../../api/calendar'
// import { gsap } from '../../utils/gsap'
import EventCard from './EventCard'
import TimeIndicator from './TimeIndicator'

interface CalendarTimelineProps {
  events: CalendarEvent[]
  currentDate: Date
  view: 'week' | 'day'
  onEventClick?: (event: CalendarEvent) => void
}

const HOURS = Array.from({ length: 24 }, (_, i) => i)

export default function CalendarTimeline({
  events,
  currentDate,
  view: _view,
  onEventClick,
}: CalendarTimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [currentTime, setCurrentTime] = useState(new Date())

  // Update current time every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date())
    }, 60000)
    return () => clearInterval(interval)
  }, [])

  // Scroll to current time on mount
  useEffect(() => {
    if (containerRef.current) {
      const now = new Date()
      const hours = now.getHours()
      const minutes = now.getMinutes()
      const scrollPosition = (hours * 60 + minutes) * 2 // 2px per minute
      
      containerRef.current.scrollTo({
        top: scrollPosition - 200, // Offset for visibility
        behavior: 'smooth',
      })
    }
  }, [])

  // Get events for a specific hour
  const getEventsForHour = (hour: number) => {
    return events.filter((event) => {
      const eventStart = new Date(event.start)
      return eventStart.getHours() === hour
    })
  }

  const isToday = (date: Date) => {
    const today = new Date()
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    )
  }

  return (
    <div className="relative h-full overflow-y-auto" ref={containerRef}>
      {/* Time slots */}
      <div className="relative min-h-[1440px]">
        {HOURS.map((hour) => {
          const hourEvents = getEventsForHour(hour)
          const isCurrentHour = isToday(currentDate) && currentTime.getHours() === hour

          return (
            <div
              key={hour}
              className="relative border-b border-white/5 min-h-[60px]"
            >
              {/* Hour label */}
              <div className="absolute left-0 top-0 w-16 text-right pr-4 pt-2 text-xs text-text-tertiary">
                {hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`}
              </div>

              {/* Events container */}
              <div className="ml-20 mr-4 relative">
                {hourEvents.map((event, index) => {
                  const eventStart = new Date(event.start)
                  const eventEnd = new Date(event.end)
                  const startMinutes = eventStart.getMinutes()
                  const duration = (eventEnd.getTime() - eventStart.getTime()) / (1000 * 60)
                  
                  return (
                    <EventCard
                      key={event.id}
                      event={event}
                      top={startMinutes}
                      height={duration}
                      onClick={() => onEventClick?.(event)}
                      style={{
                        left: `${index * 5}%`,
                        width: `${95 - index * 5}%`,
                      }}
                    />
                  )
                })}
              </div>

              {/* Current time indicator */}
              {isCurrentHour && isToday(currentDate) && (
                <TimeIndicator currentTime={currentTime} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

