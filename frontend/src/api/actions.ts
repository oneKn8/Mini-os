import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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

// React Query hooks
export function usePendingActions() {
  return useQuery({
    queryKey: ['actions', 'pending'],
    queryFn: fetchPendingActions,
    refetchInterval: 10000, // Refetch every 10 seconds
  })
}

export function useApproveAction() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (actionId: string) => approveAction(actionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useRejectAction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (actionId: string) => rejectAction(actionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

