import { useEffect } from 'react'
import { useInbox, useRefreshInbox } from '../api/inbox'
import { useRealtime } from '../contexts/RealtimeContext'

export function useInboxWithRealtime(filter?: string) {
  const { data, isLoading, error, refetch } = useInbox(filter)
  const refreshMutation = useRefreshInbox()
  const { sseInboxLastMessage } = useRealtime()

  // Listen for real-time inbox updates
  useEffect(() => {
    if (sseInboxLastMessage?.type === 'items_synced') {
      // Refetch when new items are synced
      refetch()
    }
  }, [sseInboxLastMessage, refetch])

  return {
    items: data?.items || [],
    nextCursor: data?.next_cursor || null,
    isLoading,
    error,
    refetch,
    refresh: refreshMutation.mutate,
    isRefreshing: refreshMutation.isPending,
  }
}
