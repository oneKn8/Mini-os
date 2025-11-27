import React from 'react'
import { Loader2 } from 'lucide-react'

export interface AgentStatus {
  id: string
  name: string
  status: 'idle' | 'active' | 'completed' | 'error'
  capabilities: string[]
  toolsUsed: number
  currentTool?: string
  startTime?: number
  endTime?: number
  error?: string
}

interface AgentStatusPanelProps {
  agents: AgentStatus[]
  className?: string
  compact?: boolean
}

/**
 * Minimal agent status indicator - clean, no layout shifts.
 */
export const AgentStatusPanel: React.FC<AgentStatusPanelProps> = ({
  agents,
  className = '',
}) => {
  const activeAgent = agents.find(a => a.status === 'active')
  
  if (!activeAgent) return null

  return (
    <div className={`flex items-center gap-2 text-xs text-zinc-500 ${className}`}>
      <Loader2 className="w-3 h-3 animate-spin" />
      <span>
        {activeAgent.currentTool 
          ? `Using ${activeAgent.currentTool}...`
          : 'Thinking...'}
      </span>
    </div>
  )
}

export default AgentStatusPanel
