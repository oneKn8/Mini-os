import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronLeft, ChevronRight, Plus, RefreshCw, CalendarDays } from 'lucide-react'
import { clsx } from 'clsx'
import { CalendarEvent, CreateEventPayload, UpdateEventPayload, useCreateEvent, useUpdateEvent, useDeleteEvent } from '../api/calendar'
import { useCalendarWithRealtime } from '../hooks/useCalendar'
import CalendarTimeline from '../components/Calendar/CalendarTimeline'
import CalendarGrid from '../components/Calendar/CalendarGrid'
import EventModal from '../components/Calendar/EventModal'
import { useScreenUpdates } from '../store/screenController'

export default function CalendarView() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [view, setView] = useState<'week' | 'day'>('week')
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const headerRef = useRef<HTMLDivElement>(null)

  // Agent integration
  const { previews, isAgentFocused } = useScreenUpdates('/calendar')

  // Calculate date range for current view
  const startDate = new Date(currentDate)
  if (view === 'week') {
    startDate.setDate(startDate.getDate() - startDate.getDay())
  } else {
    startDate.setHours(0, 0, 0, 0)
  }

  const endDate = new Date(startDate)
  if (view === 'week') {
    endDate.setDate(endDate.getDate() + 7)
  } else {
    endDate.setDate(endDate.getDate() + 1)
  }

  // Use real-time calendar hook
  const { events, isLoading, refresh, isRefreshing } = useCalendarWithRealtime(startDate, endDate)

  // Mutations
  const createEvent = useCreateEvent()
  const updateEvent = useUpdateEvent()
  const deleteEvent = useDeleteEvent()

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

  const handleSaveEvent = (eventData: CreateEventPayload | UpdateEventPayload) => {
    if (selectedEvent) {
      updateEvent.mutate({
        eventId: selectedEvent.id,
        updates: eventData as UpdateEventPayload,
      })
    } else {
      createEvent.mutate(eventData as CreateEventPayload)
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

  // Loading state
  if (isLoading && events.length === 0) {
    return (
      <div className="flex justify-center items-center h-full">
        <RefreshCw size={20} className="animate-spin text-zinc-600" />
      </div>
    )
  }

  return (
    <div data-calendar-page className="h-full flex flex-col gap-4 pb-16">
      {/* Header */}
      <div ref={headerRef} className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-medium text-zinc-200">Calendar</h1>
          {/* View Toggle */}
          <div className="flex items-center gap-0.5 bg-zinc-900/50 border border-zinc-800/50 rounded-lg p-0.5">
            <button
              onClick={() => setView('week')}
              className={clsx(
                "px-2.5 py-1 text-xs rounded-md transition-all",
                view === 'week' ? "bg-zinc-800 text-zinc-200" : "text-zinc-500 hover:text-zinc-400"
              )}
            >
              Week
            </button>
            <button
              onClick={() => setView('day')}
              className={clsx(
                "px-2.5 py-1 text-xs rounded-md transition-all",
                view === 'day' ? "bg-zinc-800 text-zinc-200" : "text-zinc-500 hover:text-zinc-400"
              )}
            >
              Day
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Date Navigation */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => navigateDate('prev')}
              className="p-1.5 hover:bg-zinc-800/50 rounded-lg transition-colors text-zinc-500 hover:text-zinc-300"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-sm font-medium text-zinc-300 min-w-[140px] text-center">
              {currentDate.toLocaleDateString('en-US', {
                month: 'long',
                year: 'numeric',
                ...(view === 'day' ? { day: 'numeric' } : {})
              })}
            </span>
            <button
              onClick={() => navigateDate('next')}
              className="p-1.5 hover:bg-zinc-800/50 rounded-lg transition-colors text-zinc-500 hover:text-zinc-300"
            >
              <ChevronRight size={16} />
            </button>
          </div>

          {/* Refresh */}
          <button
            onClick={() => refresh()}
            disabled={isRefreshing}
            className="p-2 rounded-lg border border-zinc-800/50 hover:bg-zinc-800/30 transition-colors text-zinc-500 disabled:opacity-50"
          >
            <RefreshCw size={14} className={clsx(isRefreshing && "animate-spin")} />
          </button>

          {/* New Event */}
          <button
            data-calendar-new-event
            onClick={handleNewEvent}
            className={clsx(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all border",
              "bg-blue-600/80 hover:bg-blue-600 text-white border-blue-500/30",
              isAgentFocused && "ring-1 ring-blue-400/50"
            )}
          >
            <Plus size={14} />
            New Event
          </button>
        </div>
      </div>

      {/* Calendar Content */}
      <div className={clsx(
        "flex-1 flex flex-col overflow-hidden rounded-xl border bg-zinc-900/30 backdrop-blur-sm",
        isAgentFocused ? "border-blue-500/30" : "border-zinc-800/50"
      )}>
        {view === 'week' ? (
          <>
            {/* Days Header */}
            <div data-calendar-header className="grid grid-cols-7 border-b border-zinc-800/50">
              {weekDays.map((day, i) => {
                const isToday = new Date().toDateString() === day.toDateString()
                return (
                  <div key={i} className="py-3 text-center border-r border-zinc-800/30 last:border-r-0">
                    <div className="text-[10px] text-zinc-600 uppercase tracking-wide mb-1">
                      {day.toLocaleDateString('en-US', { weekday: 'short' })}
                    </div>
                    <div className={clsx(
                      "text-base font-medium mx-auto w-8 h-8 flex items-center justify-center rounded-full transition-all",
                      isToday ? "bg-blue-600 text-white" : "text-zinc-300"
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

        {/* Agent Preview Overlay */}
        <AnimatePresence>
          {previews.length > 0 && previews[0].type === 'calendar_event' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 pointer-events-none"
            >
              <EventPreviewGhost event={previews[0].data} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {events.length === 0 && !isLoading && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-zinc-800/30 border border-zinc-800/50 flex items-center justify-center">
              <CalendarDays size={20} className="text-zinc-600" />
            </div>
            <p className="text-sm text-zinc-500">No events this {view}</p>
          </div>
        </div>
      )}

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

// Ghost preview for agent-proposed events
function EventPreviewGhost({ event }: { event: any }) {
  if (!event) return null

  return (
    <div className="absolute inset-4 flex items-center justify-center">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-blue-500/10 border-2 border-dashed border-blue-400/50 rounded-xl p-6 max-w-sm"
      >
        <div className="text-sm text-blue-300 mb-1">Proposed Event</div>
        <div className="text-lg text-zinc-200 font-medium">{event.title || 'New Event'}</div>
        {event.start && (
          <div className="text-xs text-zinc-500 mt-2">
            {new Date(event.start).toLocaleString()}
          </div>
        )}
      </motion.div>
    </div>
  )
}
