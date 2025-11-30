import { useState, useRef, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronLeft, ChevronRight, Plus, RefreshCw, Search, List, Grid3x3 } from 'lucide-react'
import { clsx } from 'clsx'
import { CalendarEvent, CreateEventPayload, UpdateEventPayload, useCreateEvent, useUpdateEvent, useDeleteEvent } from '../api/calendar'
import { useCalendarWithRealtime } from '../hooks/useCalendar'
import EventModal from '../components/Calendar/EventModal'
import { useScreenUpdates } from '../store/screenController'

const HOURS = Array.from({ length: 24 }, (_, i) => i)
const HOUR_HEIGHT = 60

export default function CalendarView() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [view, setView] = useState<'day' | 'week' | 'month'>('week')
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showMiniCal, setShowMiniCal] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)
  const { isAgentFocused } = useScreenUpdates('/calendar')

  const { startDate, endDate, weekDays } = useMemo(() => {
    const start = new Date(currentDate)
    let end = new Date(currentDate)
    let days: Date[] = []

    if (view === 'week') {
      start.setDate(start.getDate() - start.getDay())
      end = new Date(start)
      end.setDate(end.getDate() + 7)
      days = Array.from({ length: 7 }, (_, i) => {
        const d = new Date(start)
        d.setDate(d.getDate() + i)
        return d
      })
    } else if (view === 'day') {
      start.setHours(0, 0, 0, 0)
      end = new Date(start)
      end.setDate(end.getDate() + 1)
      days = [new Date(start)]
    } else {
      start.setDate(1)
      end = new Date(start)
      end.setMonth(end.getMonth() + 1)
      const firstDay = start.getDay()
      const lastDate = new Date(end.getTime() - 1).getDate()
      const totalDays = firstDay + lastDate
      const weeks = Math.ceil(totalDays / 7)
      days = Array.from({ length: weeks * 7 }, (_, i) => {
        const d = new Date(start)
        d.setDate(d.getDate() - firstDay + i)
        return d
      })
    }
    return { startDate: start, endDate: end, weekDays: days }
  }, [currentDate, view])

  const { events, isLoading, refresh, isRefreshing } = useCalendarWithRealtime(startDate, endDate)
  const createEvent = useCreateEvent()
  const updateEvent = useUpdateEvent()
  const deleteEvent = useDeleteEvent()

  useEffect(() => {
    if (scrollRef.current && view !== 'month') {
      const now = new Date()
      const currentHour = now.getHours()
      const scrollPosition = Math.max(0, (currentHour - 2) * HOUR_HEIGHT)
      scrollRef.current.scrollTop = scrollPosition
    }
  }, [view])

  const filteredEvents = useMemo(() => {
    if (!searchQuery) return events
    const query = searchQuery.toLowerCase()
    return events.filter(e => e.title.toLowerCase().includes(query) || e.description?.toLowerCase().includes(query))
  }, [events, searchQuery])

  const handleEventClick = (event: CalendarEvent) => { setSelectedEvent(event); setIsModalOpen(true) }
  const handleNewEvent = () => { setSelectedEvent(null); setIsModalOpen(true) }
  const handleSaveEvent = (eventData: CreateEventPayload | UpdateEventPayload) => {
    if (selectedEvent) {
      updateEvent.mutate({ eventId: selectedEvent.id, updates: eventData as UpdateEventPayload })
    } else {
      createEvent.mutate(eventData as CreateEventPayload)
    }
  }
  const handleDeleteEvent = (eventId: string) => { deleteEvent.mutate(eventId) }
  const navigateDate = (direction: 'prev' | 'next') => {
    setCurrentDate((prev) => {
      const newDate = new Date(prev)
      if (view === 'week') newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7))
      else if (view === 'day') newDate.setDate(newDate.getDate() + (direction === 'next' ? 1 : -1))
      else newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1))
      return newDate
    })
  }
  const goToToday = () => setCurrentDate(new Date())

  const { allDayEvents, timedEvents } = useMemo(() => {
    const allDay: CalendarEvent[] = []
    const timed: CalendarEvent[] = []
    filteredEvents.forEach(event => {
      const start = new Date(event.start)
      const end = new Date(event.end)
      const duration = (end.getTime() - start.getTime()) / (1000 * 60 * 60)
      if (duration >= 23 || (start.getHours() === 0 && start.getMinutes() === 0)) allDay.push(event)
      else timed.push(event)
    })
    return { allDayEvents: allDay, timedEvents: timed }
  }, [filteredEvents])

  if (isLoading && events.length === 0) {
    return <div className="flex justify-center items-center h-full"><RefreshCw size={20} className="animate-spin text-zinc-600" /></div>
  }

  return (
    <div className="h-full flex gap-4">
      <AnimatePresence>
        {showMiniCal && (
          <motion.div initial={{ width: 0, opacity: 0 }} animate={{ width: 280, opacity: 1 }} exit={{ width: 0, opacity: 0 }} className="flex-shrink-0 space-y-4">
            <div className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-4">
              <MiniCalendar currentDate={currentDate} onDateSelect={setCurrentDate} events={events} />
            </div>
            <div className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-4 max-h-96 overflow-y-auto">
              <h3 className="text-sm font-semibold text-zinc-300 mb-3 flex items-center gap-2"><List size={14} />Upcoming</h3>
              <div className="space-y-2">
                {events.slice(0, 10).map(event => (
                  <button key={event.id} onClick={() => handleEventClick(event)} className="w-full text-left p-2 rounded-lg hover:bg-zinc-800/50 transition-colors">
                    <p className="text-xs text-zinc-200 font-medium truncate">{event.title}</p>
                    <p className="text-[10px] text-zinc-500">{new Date(event.start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</p>
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <button onClick={goToToday} className="px-3 py-1.5 rounded-lg border border-zinc-800/50 hover:bg-zinc-800/30 transition-colors text-sm text-zinc-300 font-medium">Today</button>
            <div className="flex items-center gap-1">
              <button onClick={() => navigateDate('prev')} className="p-1.5 hover:bg-zinc-800/50 rounded-lg transition-colors text-zinc-500 hover:text-zinc-300"><ChevronLeft size={18} /></button>
              <span className="text-lg font-semibold text-zinc-200 min-w-[200px] text-center">
                {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric', ...(view === 'day' ? { day: 'numeric' } : {}) })}
              </span>
              <button onClick={() => navigateDate('next')} className="p-1.5 hover:bg-zinc-800/50 rounded-lg transition-colors text-zinc-500 hover:text-zinc-300"><ChevronRight size={18} /></button>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative"><Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" /><input type="text" placeholder="Search events..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9 pr-3 py-1.5 rounded-lg border border-zinc-800/50 bg-zinc-900/30 text-sm text-zinc-300 placeholder-zinc-600 focus:outline-none focus:border-zinc-700 w-48" /></div>
            <div className="flex items-center gap-0.5 bg-zinc-900/50 border border-zinc-800/50 rounded-lg p-0.5">
              <button onClick={() => setView('day')} className={clsx("px-3 py-1.5 text-xs rounded-md transition-all font-medium", view === 'day' ? "bg-zinc-800 text-zinc-200" : "text-zinc-500 hover:text-zinc-400")}>Day</button>
              <button onClick={() => setView('week')} className={clsx("px-3 py-1.5 text-xs rounded-md transition-all font-medium", view === 'week' ? "bg-zinc-800 text-zinc-200" : "text-zinc-500 hover:text-zinc-400")}>Week</button>
              <button onClick={() => setView('month')} className={clsx("px-3 py-1.5 text-xs rounded-md transition-all font-medium", view === 'month' ? "bg-zinc-800 text-zinc-200" : "text-zinc-500 hover:text-zinc-400")}>Month</button>
            </div>
            <button onClick={() => setShowMiniCal(!showMiniCal)} className="p-2 rounded-lg border border-zinc-800/50 hover:bg-zinc-800/30 transition-colors text-zinc-500"><Grid3x3 size={14} /></button>
            <button onClick={() => refresh()} disabled={isRefreshing} className="p-2 rounded-lg border border-zinc-800/50 hover:bg-zinc-800/30 transition-colors text-zinc-500 disabled:opacity-50"><RefreshCw size={14} className={clsx(isRefreshing && "animate-spin")} /></button>
            <button onClick={handleNewEvent} className={clsx("flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all border bg-blue-600/80 hover:bg-blue-600 text-white border-blue-500/30", isAgentFocused && "ring-1 ring-blue-400/50")}><Plus size={14} />New Event</button>
          </div>
        </div>

        <div data-component="calendar-view" className={clsx("flex-1 flex flex-col overflow-hidden rounded-xl border bg-zinc-900/30 backdrop-blur-sm relative", isAgentFocused ? "border-blue-500/30" : "border-zinc-800/50")}>
          {view === 'month' ? (
            <MonthView weekDays={weekDays} events={filteredEvents} currentMonth={currentDate.getMonth()} onEventClick={handleEventClick} />
          ) : (
            <>
              <div className="sticky top-0 bg-zinc-900/95 backdrop-blur-sm border-b border-zinc-800/50 z-20">
                <div className="grid grid-cols-[60px_1fr]">
                  <div className="border-r border-zinc-800/30" />
                  <div className={clsx("grid", view === 'week' ? 'grid-cols-7' : 'grid-cols-1')}>
                    {weekDays.map((day, i) => {
                      const isToday = new Date().toDateString() === day.toDateString()
                      return (
                        <div key={i} className="py-3 text-center border-r border-zinc-800/30 last:border-r-0">
                          <div className="text-[10px] text-zinc-600 uppercase tracking-wide mb-1">{day.toLocaleDateString('en-US', { weekday: 'short' })}</div>
                          <div className={clsx("text-sm font-medium mx-auto w-7 h-7 flex items-center justify-center rounded-full transition-all", isToday ? "bg-blue-600 text-white" : "text-zinc-300")}>{day.getDate()}</div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
              {allDayEvents.length > 0 && (
                <div className="border-b border-zinc-800/50 bg-zinc-900/20 z-10">
                  <div className="grid grid-cols-[60px_1fr]">
                    <div className="p-2 text-[10px] text-zinc-600 uppercase tracking-wide border-r border-zinc-800/30 flex items-center">All Day</div>
                    <div className={clsx("grid min-h-[50px]", view === 'week' ? 'grid-cols-7' : 'grid-cols-1')}>
                      {weekDays.map((day, i) => (
                        <div key={i} className="border-r border-zinc-800/30 last:border-r-0 p-1.5 space-y-1">
                          {allDayEvents.filter(e => new Date(e.start).toDateString() === day.toDateString()).map(event => (
                            <button key={event.id} onClick={() => handleEventClick(event)} className="w-full text-left px-2 py-1 rounded bg-blue-500/20 border border-blue-500/30 hover:bg-blue-500/30 transition-colors">
                              <p className="text-[10px] text-blue-300 font-medium truncate">{event.title}</p>
                            </button>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div ref={scrollRef} className="flex-1 overflow-y-auto">
                <div className="grid grid-cols-[60px_1fr]">
                  <div className="border-r border-zinc-800/30">
                    {HOURS.map(hour => (
                      <div key={hour} className="border-b border-zinc-800/20 text-right pr-2 flex items-start pt-0.5" style={{ height: HOUR_HEIGHT + 'px' }}>
                        <span className="text-[10px] text-zinc-600 font-medium">{hour === 0 ? '12 AM' : hour < 12 ? hour + ' AM' : hour === 12 ? '12 PM' : (hour - 12) + ' PM'}</span>
                      </div>
                    ))}
                  </div>
                  <div className={clsx("grid relative", view === 'week' ? 'grid-cols-7' : 'grid-cols-1')}>
                    <div className="absolute inset-0 pointer-events-none z-0">{HOURS.map(hour => <div key={hour} className="border-b border-zinc-800/20" style={{ height: HOUR_HEIGHT + 'px' }} />)}</div>
                    {weekDays.map((day, dayIndex) => {
                      const isToday = new Date().toDateString() === day.toDateString()
                      const dayEvents = timedEvents.filter(e => new Date(e.start).toDateString() === day.toDateString())
                      return (
                        <div key={dayIndex} className={clsx("relative border-r border-zinc-800/30 last:border-r-0", isToday && "bg-blue-500/5")} style={{ height: (HOURS.length * HOUR_HEIGHT) + 'px' }}>
                          {isToday && <CurrentTimeIndicator />}
                          {dayEvents.map(event => <EventBlock key={event.id} event={event} onClick={() => handleEventClick(event)} />)}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
      <EventModal event={selectedEvent} isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onSave={handleSaveEvent} onDelete={selectedEvent ? () => handleDeleteEvent(selectedEvent.id) : undefined} />
    </div>
  )
}

function EventBlock({ event, onClick }: { event: CalendarEvent; onClick: () => void }) {
  const start = new Date(event.start)
  const end = new Date(event.end)
  const startHour = start.getHours() + start.getMinutes() / 60
  const duration = (end.getTime() - start.getTime()) / (1000 * 60 * 60)
  return (
    <button onClick={onClick} className="absolute left-1 right-1 rounded px-2 py-1 bg-blue-500/20 border-l-2 border-blue-500 hover:bg-blue-500/30 transition-colors overflow-hidden z-10 text-left" style={{ top: (startHour * HOUR_HEIGHT) + 'px', height: Math.max(duration * HOUR_HEIGHT, 24) + 'px' }}>
      <p className="text-[11px] text-blue-200 font-semibold truncate">{event.title}</p>
      {duration * HOUR_HEIGHT > 30 && <p className="text-[9px] text-blue-400/80">{start.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}</p>}
    </button>
  )
}

function CurrentTimeIndicator() {
  const [now, setNow] = useState(new Date())
  useEffect(() => { const interval = setInterval(() => setNow(new Date()), 60000); return () => clearInterval(interval) }, [])
  const hours = now.getHours() + now.getMinutes() / 60
  return <div className="absolute left-0 right-0 z-20 pointer-events-none" style={{ top: (hours * HOUR_HEIGHT) + 'px' }}><div className="flex items-center"><div className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-lg" /><div className="flex-1 h-[2px] bg-red-500 shadow-sm" /></div></div>
}

function MiniCalendar({ currentDate, onDateSelect, events }: { currentDate: Date; onDateSelect: (date: Date) => void; events: CalendarEvent[] }) {
  const [viewDate, setViewDate] = useState(new Date(currentDate))
  const daysInMonth = useMemo(() => {
    const year = viewDate.getFullYear()
    const month = viewDate.getMonth()
    const firstDay = new Date(year, month, 1).getDay()
    const lastDate = new Date(year, month + 1, 0).getDate()
    return Array.from({ length: 42 }, (_, i) => {
      const dayNum = i - firstDay + 1
      if (dayNum < 1 || dayNum > lastDate) return null
      return new Date(year, month, dayNum)
    })
  }, [viewDate])
  const hasEvents = (date: Date | null) => {
    if (!date) return false
    return events.some(e => new Date(e.start).toDateString() === date.toDateString())
  }
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <button onClick={() => setViewDate(new Date(viewDate.setMonth(viewDate.getMonth() - 1)))} className="p-1 hover:bg-zinc-800/50 rounded transition-colors"><ChevronLeft size={14} className="text-zinc-500" /></button>
        <span className="text-xs font-semibold text-zinc-300">{viewDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</span>
        <button onClick={() => setViewDate(new Date(viewDate.setMonth(viewDate.getMonth() + 1)))} className="p-1 hover:bg-zinc-800/50 rounded transition-colors"><ChevronRight size={14} className="text-zinc-500" /></button>
      </div>
      <div className="grid grid-cols-7 gap-1">
        {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => <div key={i} className="text-center text-[9px] text-zinc-600 font-semibold py-1">{day}</div>)}
        {daysInMonth.map((date, i) => {
          if (!date) return <div key={i} />
          const isToday = new Date().toDateString() === date.toDateString()
          const isSelected = currentDate.toDateString() === date.toDateString()
          return (
            <button key={i} onClick={() => onDateSelect(date)} className={clsx("aspect-square text-[10px] rounded-md transition-all relative font-medium", isToday && "bg-blue-600 text-white", !isToday && isSelected && "bg-zinc-800 text-zinc-200", !isToday && !isSelected && "text-zinc-400 hover:bg-zinc-800/50")}>
              {date.getDate()}
              {hasEvents(date) && !isToday && <div className="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-blue-500" />}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function MonthView({ weekDays, events, currentMonth, onEventClick }: { weekDays: Date[]; events: CalendarEvent[]; currentMonth: number; onEventClick: (event: CalendarEvent) => void }) {
  const weeks = []
  for (let i = 0; i < weekDays.length; i += 7) weeks.push(weekDays.slice(i, i + 7))
  return (
    <div className="flex-1 flex flex-col">
      <div className="grid grid-cols-7 border-b border-zinc-800/50 bg-zinc-900/40">
        {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map(day => (
          <div key={day} className="p-3 text-center border-r border-zinc-800/30 last:border-r-0"><span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">{day}</span></div>
        ))}
      </div>
      <div className="flex-1 flex flex-col">
        {weeks.map((week, weekIndex) => (
          <div key={weekIndex} className="flex-1 grid grid-cols-7 border-b border-zinc-800/30 last:border-b-0">
            {week.map((day, dayIndex) => {
              const isToday = new Date().toDateString() === day.toDateString()
              const isCurrentMonth = day.getMonth() === currentMonth
              const dayEvents = events.filter(e => new Date(e.start).toDateString() === day.toDateString())
              return (
                <div key={dayIndex} className={clsx("border-r border-zinc-800/30 last:border-r-0 p-2 min-h-[100px]", !isCurrentMonth && "bg-zinc-900/20", isToday && "bg-blue-500/5")}>
                  <div className={clsx("text-sm font-semibold mb-2", isToday && "w-7 h-7 bg-blue-600 text-white rounded-full flex items-center justify-center", !isToday && (isCurrentMonth ? "text-zinc-300" : "text-zinc-600"))}>{day.getDate()}</div>
                  <div className="space-y-1">
                    {dayEvents.slice(0, 3).map(event => (
                      <button key={event.id} onClick={() => onEventClick(event)} className="w-full text-left px-2 py-1 rounded text-[10px] bg-blue-500/20 border-l-2 border-blue-500 text-blue-300 hover:bg-blue-500/30 truncate font-medium">{event.title}</button>
                    ))}
                    {dayEvents.length > 3 && <p className="text-[9px] text-zinc-500 pl-2">+{dayEvents.length - 3} more</p>}
                  </div>
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
