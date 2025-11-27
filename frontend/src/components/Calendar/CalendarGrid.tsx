import { CalendarEvent } from '../../api/calendar'
import EventCard from './EventCard'

interface CalendarGridProps {
  events: CalendarEvent[]
  weekDays: Date[]
  onEventClick?: (event: CalendarEvent) => void
}

export default function CalendarGrid({
  events,
  weekDays,
  onEventClick,
}: CalendarGridProps) {
  const getEventsForDay = (date: Date) => {
    return events.filter((e) => {
      const eventDate = new Date(e.start)
      return (
        eventDate.getDate() === date.getDate() &&
        eventDate.getMonth() === date.getMonth() &&
        eventDate.getFullYear() === date.getFullYear()
      )
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
    <div className="grid grid-cols-7 divide-x divide-white/5">
      {weekDays.map((day, i) => {
        const dayEvents = getEventsForDay(day)
        const today = isToday(day)

        return (
          <div key={i} className="relative min-h-[600px] p-2 space-y-2">
            {dayEvents.map((event, eventIndex) => {
              const eventStart = new Date(event.start)
              const eventEnd = new Date(event.end)
              const startHour = eventStart.getHours()
              const startMinutes = eventStart.getMinutes()
              const duration = (eventEnd.getTime() - eventStart.getTime()) / (1000 * 60)
              
              return (
                <EventCard
                  key={event.id}
                  event={event}
                  top={startHour * 60 + startMinutes}
                  height={duration}
                  onClick={() => onEventClick?.(event)}
                />
              )
            })}
            
            {/* Today indicator */}
            {today && (
              <div
                className="absolute w-full border-t-2 border-accent-error z-10 pointer-events-none"
                style={{
                  top: `${(new Date().getHours() * 60 + new Date().getMinutes()) / (24 * 60) * 100}%`,
                }}
              >
                <div className="absolute -left-1 -top-1.5 w-3 h-3 rounded-full bg-accent-error" />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

