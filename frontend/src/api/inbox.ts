import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export interface InboxItem {
  id: string
  source_type: string
  title: string
  body_preview: string
  sender?: string
  received_at: string
  importance: 'critical' | 'high' | 'medium' | 'low' | 'ignore'
  category: string
  due_datetime?: string
  suggested_action?: string
  read?: boolean
}

export async function fetchInboxItems(filter?: string): Promise<InboxItem[]> {
  const response = await api.get('/inbox', { params: filter ? { filter } : {} })
  return response.data
}

export async function fetchInboxItem(itemId: string): Promise<InboxItem & { body_full?: string; labels?: string[] }> {
  const response = await api.get(`/inbox/${itemId}`)
  return response.data
}

// React Query hooks
export function useInbox(filter?: string) {
  return useQuery({
    queryKey: ['inbox', filter],
    queryFn: () => fetchInboxItems(filter),
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function useInboxItem(itemId: string | null) {
  return useQuery({
    queryKey: ['inbox', itemId],
    queryFn: () => fetchInboxItem(itemId!),
    enabled: !!itemId,
  })
}

export function useRefreshInbox() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/sync/refresh-inbox')
      return response.data
    },
    onSuccess: () => {
      // Invalidate and refetch inbox queries
      queryClient.invalidateQueries({ queryKey: ['inbox'] })
    },
  })
}

