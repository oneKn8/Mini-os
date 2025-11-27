import { useEffect } from 'react'
import { useDashboardStats } from '../api/dashboard'
import { useRealtime } from '../contexts/RealtimeContext'

export function useDashboardWithRealtime() {
  const { data, isLoading, error, refetch } = useDashboardStats()
  const { wsLastMessage, sseInboxLastMessage, sseCalendarLastMessage } = useRealtime()

  // Listen for real-time updates that affect dashboard
  useEffect(() => {
    if (wsLastMessage?.type === 'action_update' || 
        sseInboxLastMessage || 
        sseCalendarLastMessage) {
      // Refetch dashboard stats when actions, inbox, or calendar change
      refetch()
    }
  }, [wsLastMessage, sseInboxLastMessage, sseCalendarLastMessage, refetch])

  return {
    stats: data,
    isLoading,
    error,
    refetch,
  }
}

