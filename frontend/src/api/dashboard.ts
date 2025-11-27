export interface DashboardStats {
  total_items: number
  items_by_provider: Record<string, number>
  items_by_importance: Record<string, number>
  items_by_category: Record<string, number>
  pending_actions: number
  agent_stats: {
    total_runs: number
    success_rate: number
    avg_duration_ms: number
    runs_by_agent: Record<string, number>
    recent_runs: Array<{
      id: string
      agent_name: string
      context: string
      status: string
      duration_ms: number
      created_at: string
    }>
  }
  connected_accounts: number
  recent_sync_activity: Array<{
    id: string
    context: string
    status: string
    created_at: string
  }>
}

import { useQuery } from '@tanstack/react-query'

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const response = await fetch('/api/dashboard/stats')
  if (!response.ok) {
    throw new Error('Failed to fetch dashboard stats')
  }
  return response.json()
}

// React Query hooks
export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: fetchDashboardStats,
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}
