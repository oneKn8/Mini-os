import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export async function fetchPendingActions() {
  const response = await api.get('/actions/pending')
  return response.data
}

export async function approveAction(actionId: string) {
  const response = await api.post(`/actions/${actionId}/approve`)
  return response.data
}

export async function rejectAction(actionId: string) {
  const response = await api.post(`/actions/${actionId}/reject`)
  return response.data
}

