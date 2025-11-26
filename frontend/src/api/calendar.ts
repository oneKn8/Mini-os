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
