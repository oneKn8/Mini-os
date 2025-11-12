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
}

export async function fetchInboxItems(filter: string): Promise<InboxItem[]> {
  const response = await api.get('/inbox', { params: { filter } })
  return response.data
}

