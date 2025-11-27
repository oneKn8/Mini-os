export interface CalendarEvent {
  id: string
  title: string
  description: string
  start: string
  end: string
  location?: string
  source_id: string
}

export interface CreateEventPayload {
  title: string
  start: Date
  end: Date
  description?: string
  location?: string
}

export interface UpdateEventPayload {
  title?: string
  start?: Date
  end?: Date
  description?: string
  location?: string
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export async function fetchEvents(startDate?: Date, endDate?: Date): Promise<CalendarEvent[]> {
  const params = new URLSearchParams()
  if (startDate) params.append('start_date', startDate.toISOString())
  if (endDate) params.append('end_date', endDate.toISOString())
  
  const response = await fetch(`/api/calendar/events?${params.toString()}`)
  if (!response.ok) {
    throw new Error('Failed to fetch events')
  }
  return response.json()
}

export async function createEvent(event: CreateEventPayload): Promise<unknown> {
  const response = await fetch('/api/calendar/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event)
  })
  if (!response.ok) {
    throw new Error('Failed to create event')
  }
  return response.json()
}

export async function updateEvent(eventId: string, updates: UpdateEventPayload): Promise<unknown> {
  const response = await fetch(`/api/calendar/events/${eventId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  })
  if (!response.ok) {
    throw new Error('Failed to update event')
  }
  return response.json()
}

export async function deleteEvent(eventId: string): Promise<void> {
  const response = await fetch(`/api/calendar/events/${eventId}`, {
    method: 'DELETE'
  })
  if (!response.ok) {
    throw new Error('Failed to delete event')
  }
}

// React Query hooks
export function useCalendarEvents(startDate?: Date, endDate?: Date) {
  return useQuery({
    queryKey: ['calendar', 'events', startDate?.toISOString(), endDate?.toISOString()],
    queryFn: () => fetchEvents(startDate, endDate),
    refetchInterval: 60000, // Refetch every minute
  })
}

export function useCreateEvent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (event: CreateEventPayload) => createEvent(event),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
    },
  })
}

export function useUpdateEvent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ eventId, updates }: { eventId: string; updates: UpdateEventPayload }) =>
      updateEvent(eventId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
    },
  })
}

export function useDeleteEvent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (eventId: string) => deleteEvent(eventId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
    },
  })
}

export function useRefreshCalendar() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/sync/refresh-calendar', { method: 'POST' })
      if (!response.ok) {
        throw new Error('Failed to refresh calendar')
      }
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
    },
  })
}
