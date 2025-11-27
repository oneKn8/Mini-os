import { useEffect } from 'react'
import { useCalendarEvents, useRefreshCalendar } from '../api/calendar'
import { useRealtime } from '../contexts/RealtimeContext'

export function useCalendarWithRealtime(startDate?: Date, endDate?: Date) {
  const { data, isLoading, error, refetch } = useCalendarEvents(startDate, endDate)
  const refreshMutation = useRefreshCalendar()
  const { sseCalendarLastMessage } = useRealtime()

  // Listen for real-time calendar updates
  useEffect(() => {
    if (sseCalendarLastMessage) {
      const messageType = sseCalendarLastMessage.type
      if (['event_created', 'event_updated', 'event_deleted', 'events_synced'].includes(messageType)) {
        // Refetch when calendar events change
        refetch()
      }
    }
  }, [sseCalendarLastMessage, refetch])

  return {
    events: data || [],
    isLoading,
    error,
    refetch,
    refresh: refreshMutation.mutate,
    isRefreshing: refreshMutation.isPending,
  }
}

