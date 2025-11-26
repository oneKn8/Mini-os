import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
    ChevronLeft, 
    ChevronRight, 
    MapPin,
    Plus,
    MoreHorizontal,
    RefreshCw
} from 'lucide-react'
import { clsx } from 'clsx'
import GlassCard from '../components/UI/GlassCard'
import { fetchEvents, CalendarEvent } from '../api/calendar'

export default function CalendarView() {
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [currentDate, setCurrentDate] = useState(new Date())
  const [view, setView] = useState<'week' | 'month'>('week')
  const [syncMessage, setSyncMessage] = useState<string | null>(null)

  useEffect(() => {
    loadEvents()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentDate])

  const loadEvents = async () => {
    try {
      setLoading(true)
      // Calculate start/end of current view
      const start = new Date(currentDate)
      start.setDate(start.getDate() - start.getDay()) // Start of week (Sunday)
      const end = new Date(start)
      end.setDate(end.getDate() + 7) // End of week

      const data = await fetchEvents(start, end)
      setEvents(data)
    } catch (error) {
      console.error('Failed to fetch events:', error)
    } finally {
      setLoading(false)
    }
  }

  const refreshCalendar = async () => {
    setSyncing(true)
    setSyncMessage(null)
    try {
      // First, trigger sync from Google Calendar
      const syncResponse = await fetch('/api/sync/refresh-calendar', { method: 'POST' })
      const syncData = await syncResponse.json()
      
      if (syncData.status === 'no_accounts') {
        setSyncMessage(syncData.message)
      } else if (syncData.synced_items > 0) {
        setSyncMessage(`Synced ${syncData.synced_items} events`)
      } else {
        setSyncMessage('Already up to date')
      }
      
      // Then fetch the updated events
      await loadEvents()
      
      // Clear message after 3 seconds
      setTimeout(() => setSyncMessage(null), 3000)
    } catch (error) {
      console.error('Failed to refresh calendar:', error)
      setSyncMessage('Sync failed. Please try again.')
      setTimeout(() => setSyncMessage(null), 3000)
    } finally {
      setSyncing(false)
    }
  }

  if (loading && events.length === 0) {
    return <div className="flex justify-center p-10"><div className="animate-spin h-8 w-8 border-2 border-white/20 border-t-white rounded-full"></div></div>
  }

  const weekDays = Array.from({ length: 7 }).map((_, i) => {
    const d = new Date(currentDate)
    d.setDate(d.getDate() - d.getDay() + i)
    return d
  })

  const getEventsForDay = (date: Date) => {
    return events.filter(e => {
      const eventDate = new Date(e.start)
      return eventDate.getDate() === date.getDate() &&
             eventDate.getMonth() === date.getMonth() &&
             eventDate.getFullYear() === date.getFullYear()
    })
  }

  return (
    <div className="h-full flex flex-col gap-6 pb-20">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
           <h1 className="text-3xl font-bold text-white text-glow">Calendar</h1>
           <div className="flex items-center gap-2 bg-surface border border-white/10 rounded-lg p-1">
             <button 
               onClick={() => setView('week')}
               className={clsx("px-3 py-1 rounded-md text-sm transition-colors", view === 'week' ? "bg-white/10 text-white" : "text-text-tertiary hover:text-white")}
             >
               Week
             </button>
             <button 
               onClick={() => setView('month')}
               className={clsx("px-3 py-1 rounded-md text-sm transition-colors", view === 'month' ? "bg-white/10 text-white" : "text-text-tertiary hover:text-white")}
             >
               Month
             </button>
           </div>
        </div>
        
        <div className="flex items-center gap-4">
           {syncMessage && (
             <span className="text-xs text-accent-primary animate-pulse">
               {syncMessage}
             </span>
           )}
           <div className="flex items-center gap-2">
             <button onClick={() => setCurrentDate(new Date(currentDate.setDate(currentDate.getDate() - 7)))} className="p-2 hover:bg-white/10 rounded-full transition-colors text-white">
               <ChevronLeft size={20} />
             </button>
             <span className="text-lg font-medium text-white min-w-[150px] text-center">
               {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
             </span>
             <button onClick={() => setCurrentDate(new Date(currentDate.setDate(currentDate.getDate() + 7)))} className="p-2 hover:bg-white/10 rounded-full transition-colors text-white">
               <ChevronRight size={20} />
             </button>
           </div>
           <button 
             onClick={refreshCalendar} 
             disabled={syncing}
             className="p-2 rounded-lg bg-surface hover:bg-surface-hover border border-border-light transition-colors disabled:opacity-50"
             title="Sync from Google Calendar"
           >
             <RefreshCw size={18} className={clsx((syncing || loading) && "animate-spin", "text-white")} />
           </button>
           <button className="flex items-center gap-2 bg-accent-primary hover:bg-accent-primary-hover text-white px-4 py-2 rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(76,110,245,0.3)]">
             <Plus size={18} />
             New Event
           </button>
        </div>
      </div>

      {/* Calendar Grid (Week View) */}
      <GlassCard className="flex-1 flex flex-col overflow-hidden" noBorder>
        {/* Days Header */}
        <div className="grid grid-cols-7 border-b border-white/5 bg-black/20">
          {weekDays.map((day, i) => {
            const isToday = new Date().toDateString() === day.toDateString()
            return (
              <div key={i} className="py-4 text-center border-r border-white/5 last:border-r-0">
                <div className="text-xs text-text-tertiary uppercase mb-1">{day.toLocaleDateString('en-US', { weekday: 'short' })}</div>
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

        {/* Time Grid */}
        <div className="flex-1 overflow-y-auto grid grid-cols-7 divide-x divide-white/5 relative">
           {/* Background lines for hours could go here */}
           {weekDays.map((day, i) => {
             const dayEvents = getEventsForDay(day)
             return (
               <div key={i} className="relative min-h-[600px] p-2 space-y-2">
                 {dayEvents.map((event) => (
                   <motion.div
                     key={event.id}
                     initial={{ opacity: 0, scale: 0.9 }}
                     animate={{ opacity: 1, scale: 1 }}
                     className="p-3 rounded-lg bg-accent-secondary/20 border border-accent-secondary/30 hover:bg-accent-secondary/30 transition-colors cursor-pointer group"
                   >
                     <div className="flex justify-between items-start mb-1">
                       <span className="text-xs font-bold text-accent-secondary">
                         {new Date(event.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                       </span>
                       {event.location && <MapPin size={12} className="text-text-tertiary" />}
                     </div>
                     <h4 className="text-sm font-bold text-white line-clamp-2">{event.title}</h4>
                     
                     <div className="opacity-0 group-hover:opacity-100 absolute top-2 right-2 transition-opacity">
                        <button className="p-1 hover:bg-black/40 rounded text-white">
                          <MoreHorizontal size={14} />
                        </button>
                     </div>
                   </motion.div>
                 ))}
                 
                 {/* Time indicator line if today */}
                 {new Date().toDateString() === day.toDateString() && (
                   <div 
                     className="absolute w-full border-t-2 border-accent-error z-10 pointer-events-none"
                     style={{ 
                       top: `${(new Date().getHours() * 60 + new Date().getMinutes()) / (24 * 60) * 100}%` 
                     }}
                   >
                     <div className="absolute -left-1 -top-1.5 w-3 h-3 rounded-full bg-accent-error"></div>
                   </div>
                 )}
               </div>
             )
           })}
        </div>
      </GlassCard>
    </div>
  )
}
