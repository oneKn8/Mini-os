export interface AgentRun {
  id: string
  agent_name: string
  context: string
  status: string
  duration_ms: number
  error_message?: string
  created_at: string
  completed_at?: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  input_summary?: any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  output_summary?: any
}

export interface AgentRunListResponse {
  items: AgentRun[]
  total: number
  page: number
  limit: number
}

export interface AgentSummary {
  total_runs: number
  runs_by_agent: Record<string, number>
  success_rate: number
  recent_failures: Array<{
    id: string
    agent_name: string
    error_message: string
    created_at: string
  }>
}

export async function fetchAgentRuns(
  page: number = 1, 
  limit: number = 20, 
  agentName?: string, 
  status?: string
): Promise<AgentRunListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString()
  })
  
  if (agentName) params.append('agent_name', agentName)
  if (status) params.append('status', status)
  
  const response = await fetch(`/api/agents/runs?${params.toString()}`)
  if (!response.ok) {
    throw new Error('Failed to fetch agent runs')
  }
  return response.json()
}

export async function fetchAgentRunDetails(runId: string): Promise<AgentRun> {
  const response = await fetch(`/api/agents/runs/${runId}`)
  if (!response.ok) {
    throw new Error('Failed to fetch agent run details')
  }
  return response.json()
}

export async function fetchAgentSummary(): Promise<AgentSummary> {
  const response = await fetch('/api/agents/summary')
  if (!response.ok) {
    throw new Error('Failed to fetch agent summary')
  }
  return response.json()
}
