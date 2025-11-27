import { useEffect, useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { 
    ChevronLeft, 
    ChevronRight, 
    Plus,
    RefreshCw
} from 'lucide-react'
import { clsx } from 'clsx'
import GlassCard from '../components/UI/GlassCard'
import { CalendarEvent, useCreateEvent, useUpdateEvent, useDeleteEvent } from '../api/calendar'
import { useCalendarWithRealtime } from '../hooks/useCalendar'
import CalendarTimeline from '../components/Calendar/CalendarTimeline'
import CalendarGrid from '../components/Calendar/CalendarGrid'
import EventModal from '../components/Calendar/EventModal'
import { staggerAnimation } from '../utils/gsap'

export default function CalendarView() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [view, setView] = useState<'week' | 'day'>('week')
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const headerRef = useRef<HTMLDivElement>(null)

  // Calculate date range for current view
  const startDate = new Date(currentDate)
  if (view === 'week') {
    startDate.setDate(startDate.getDate() - startDate.getDay()) // Start of week
  } else {
    startDate.setHours(0, 0, 0, 0) // Start of day
  }

  const endDate = new Date(startDate)
  if (view === 'week') {
    endDate.setDate(endDate.getDate() + 7) // End of week
  } else {
    endDate.setDate(endDate.getDate() + 1) // End of day
  }

  // Use real-time calendar hook
  const { events, isLoading, refresh, isRefreshing } = useCalendarWithRealtime(startDate, endDate)
  
  // Mutations
  const createEvent = useCreateEvent()
  const updateEvent = useUpdateEvent()
  const deleteEvent = useDeleteEvent()

  // Animate header on mount
  useEffect(() => {
    if (headerRef.current) {
      staggerAnimation(headerRef.current.children, {
        opacity: 0,
        y: -20,
        duration: 0.5,
      }, 0.1)
    }
  }, [])

  const weekDays = Array.from({ length: 7 }).map((_, i) => {
    const d = new Date(currentDate)
    d.setDate(d.getDate() - d.getDay() + i)
    return d
  })

  const handleEventClick = (event: CalendarEvent) => {
    setSelectedEvent(event)
    setIsModalOpen(true)
  }

  const handleNewEvent = () => {
    setSelectedEvent(null)
    setIsModalOpen(true)
  }

  const handleSaveEvent = (eventData: { title: string; start: Date; end: Date; description?: string; location?: string }) => {
    if (selectedEvent) {
      updateEvent.mutate({
        eventId: selectedEvent.id,
        updates: eventData,
      })
    } else {
      createEvent.mutate(eventData)
    }
  }

  const handleDeleteEvent = (eventId: string) => {
    deleteEvent.mutate(eventId)
  }

  const navigateDate = (direction: 'prev' | 'next') => {
    setCurrentDate((prev) => {
      const newDate = new Date(prev)
      if (view === 'week') {
        newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7))
      } else {
        newDate.setDate(newDate.getDate() + (direction === 'next' ? 1 : -1))
      }
      return newDate
    })
  }

  if (isLoading && events.length === 0) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="animate-spin h-8 w-8 border-2 border-white/20 border-t-white rounded-full"></div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col gap-6 pb-20">
      {/* Header */}
      <div ref={headerRef} className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold text-white text-glow">Calendar</h1>
          <div className="flex items-center gap-2 bg-surface border border-white/10 rounded-lg p-1">
            <button 
              onClick={() => setView('week')}
              className={clsx(
                "px-3 py-1 rounded-md text-sm transition-colors",
                view === 'week' ? "bg-white/10 text-white" : "text-text-tertiary hover:text-white"
              )}
            >
              Week
            </button>
            <button 
              onClick={() => setView('day')}
              className={clsx(
                "px-3 py-1 rounded-md text-sm transition-colors",
                view === 'day' ? "bg-white/10 text-white" : "text-text-tertiary hover:text-white"
              )}
            >
              Day
            </button>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <button 
              onClick={() => navigateDate('prev')} 
              className="p-2 hover:bg-white/10 rounded-full transition-colors text-white"
            >
              <ChevronLeft size={20} />
            </button>
            <span className="text-lg font-medium text-white min-w-[200px] text-center">
              {currentDate.toLocaleDateString('en-US', { 
                month: 'long', 
                year: 'numeric',
                ...(view === 'day' ? { day: 'numeric' } : {})
              })}
            </span>
            <button 
              onClick={() => navigateDate('next')} 
              className="p-2 hover:bg-white/10 rounded-full transition-colors text-white"
            >
              <ChevronRight size={20} />
            </button>
          </div>
          <button 
            onClick={() => refresh()} 
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-surface hover:bg-surface-hover border border-border-light transition-colors disabled:opacity-50"
            title="Sync from Google Calendar"
          >
            <RefreshCw size={18} className={clsx(isRefreshing && "animate-spin", "text-white")} />
          </button>
          <button 
            onClick={handleNewEvent}
            className="flex items-center gap-2 bg-accent-primary hover:bg-accent-primary-hover text-white px-4 py-2 rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(76,110,245,0.3)]"
          >
            <Plus size={18} />
            New Event
          </button>
        </div>
      </div>

      {/* Calendar Content */}
      <GlassCard className="flex-1 flex flex-col overflow-hidden" noBorder>
        {view === 'week' ? (
          <>
            {/* Days Header */}
            <div className="grid grid-cols-7 border-b border-white/5 bg-black/20">
              {weekDays.map((day, i) => {
                const isToday = new Date().toDateString() === day.toDateString()
                return (
                  <div key={i} className="py-4 text-center border-r border-white/5 last:border-r-0">
                    <div className="text-xs text-text-tertiary uppercase mb-1">
                      {day.toLocaleDateString('en-US', { weekday: 'short' })}
                    </div>
                    <div className={clsx(
                      "text-xl font-bold mx-auto w-10 h-10 flex items-center justify-center rounded-full transition-all",
                      isToday ? "bg-accent-primary text-white shadow-[0_0_10px_#4c6ef5]" : "text-white"
                    )}>
                      {day.getDate()}
                    </div>
                  </div>
                )
              })}
            </div>
            <CalendarGrid 
              events={events} 
              weekDays={weekDays}
              onEventClick={handleEventClick}
            />
          </>
        ) : (
          <CalendarTimeline
            events={events}
            currentDate={currentDate}
            view="day"
            onEventClick={handleEventClick}
          />
        )}
      </GlassCard>

      {/* Event Modal */}
      <EventModal
        event={selectedEvent}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveEvent}
        onDelete={selectedEvent ? () => handleDeleteEvent(selectedEvent.id) : undefined}
      />
    </div>
  )
}
