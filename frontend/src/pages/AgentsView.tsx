import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Terminal, 
  ChevronRight, 
  Search,
  AlertTriangle
} from 'lucide-react'
import { clsx } from 'clsx'
import GlassCard from '../components/UI/GlassCard'
import { fetchAgentRuns, fetchAgentSummary, AgentRun, AgentSummary } from '../api/agents'

export default function AgentsView() {
  const [runs, setRuns] = useState<AgentRun[]>([])
  const [summary, setSummary] = useState<AgentSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null)
  const [filterAgent, setFilterAgent] = useState<string>('all')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [runsData, summaryData] = await Promise.all([
        fetchAgentRuns(1, 50),
        fetchAgentSummary()
      ])
      setRuns(runsData.items)
      setSummary(summaryData)
    } catch (error) {
      console.error('Failed to load agent data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredRuns = runs.filter(r => filterAgent === 'all' || r.agent_name === filterAgent)

  const StatusBadge = ({ status }: { status: string }) => {
    const styles = {
      success: "bg-accent-success/10 text-accent-success border-accent-success/20",
      error: "bg-accent-error/10 text-accent-error border-accent-error/20",
      running: "bg-accent-primary/10 text-accent-primary border-accent-primary/20 animate-pulse"
    }[status] || "bg-text-tertiary/10 text-text-tertiary"

    return (
      <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono border ${styles}`}>
        {status}
      </span>
    )
  }

  return (
    <div className="h-full flex flex-col gap-6 pb-20">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-text-primary text-glow font-mono tracking-tight">
            <span className="text-accent-primary">&gt;</span> AGENT_OPS
          </h1>
          <div className="h-2 w-2 rounded-full bg-accent-success animate-pulse shadow-[0_0_8px_#12b886]"></div>
        </div>
      </div>

      {/* Summary Console */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlassCard className="p-4 flex flex-col gap-1" variant="dark" noBorder>
          <span className="text-xs font-mono text-text-tertiary uppercase">Total Executions</span>
          <span className="text-2xl font-mono font-bold text-white">{summary?.total_runs || 0}</span>
        </GlassCard>
        <GlassCard className="p-4 flex flex-col gap-1" variant="dark" noBorder>
          <span className="text-xs font-mono text-text-tertiary uppercase">Success Rate</span>
          <span className="text-2xl font-mono font-bold text-accent-success">{summary?.success_rate || 0}%</span>
        </GlassCard>
        <GlassCard className="p-4 flex flex-col gap-1" variant="dark" noBorder>
          <span className="text-xs font-mono text-text-tertiary uppercase">Active Agents</span>
          <span className="text-2xl font-mono font-bold text-accent-info">{Object.keys(summary?.runs_by_agent || {}).length}</span>
        </GlassCard>
        <GlassCard className="p-4 flex flex-col gap-1" variant="dark" noBorder>
          <span className="text-xs font-mono text-text-tertiary uppercase">System Load</span>
          <div className="flex items-end gap-1 h-8 mt-1">
            {[40, 70, 30, 80, 50, 90, 20, 60].map((h, i) => (
              <div key={i} className="w-1 bg-accent-primary/50" style={{ height: `${h}%` }}></div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Main Terminal Area */}
      <GlassCard className="flex-1 flex flex-col min-h-0 overflow-hidden font-mono text-sm" variant="dark">
        
        {/* Toolbar */}
        <div className="flex items-center gap-4 p-3 border-b border-white/10 bg-black/40">
          <Terminal size={16} className="text-text-tertiary" />
          <div className="flex gap-2">
            {['all', 'orchestrator', 'email_agent', 'calendar_agent'].map(agent => (
              <button
                key={agent}
                onClick={() => setFilterAgent(agent)}
                className={clsx(
                  "px-3 py-1 rounded text-xs transition-colors",
                  filterAgent === agent ? "bg-white/10 text-white" : "text-text-tertiary hover:text-white"
                )}
              >
                {agent}
              </button>
            ))}
          </div>
          <div className="ml-auto flex items-center gap-2 bg-black/20 px-2 py-1 rounded border border-white/5">
            <Search size={12} className="text-text-tertiary" />
            <input 
              type="text" 
              placeholder="Grep logs..." 
              className="bg-transparent border-none outline-none text-xs text-white placeholder-text-tertiary w-32"
            />
          </div>
        </div>

        {/* Logs List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {loading ? (
            <div className="text-text-tertiary p-4">Initializing stream...</div>
          ) : (
            filteredRuns.map((run) => (
              <div key={run.id} className="group">
                <div 
                  onClick={() => setExpandedRunId(expandedRunId === run.id ? null : run.id)}
                  className={clsx(
                    "flex items-center gap-4 p-2 rounded cursor-pointer transition-colors",
                    expandedRunId === run.id ? "bg-white/10" : "hover:bg-white/5"
                  )}
                >
                  <ChevronRight size={14} className={clsx("text-text-tertiary transition-transform", expandedRunId === run.id && "rotate-90")} />
                  <span className="text-text-tertiary w-32">{new Date(run.created_at).toISOString().slice(11, 19)}</span>
                  <span className="text-accent-info w-32">{run.agent_name}</span>
                  <span className="text-white/80 flex-1 truncate">{run.context}</span>
                  <span className="text-text-tertiary w-20 text-right">{run.duration_ms}ms</span>
                  <StatusBadge status={run.status} />
                </div>

                <AnimatePresence>
                  {expandedRunId === run.id && (
                    <motion.div 
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden pl-10 pr-4 border-l border-white/10 ml-5"
                    >
                      <div className="py-4 space-y-4 text-xs text-text-secondary">
                        <div>
                          <div className="text-text-tertiary mb-1 uppercase">Input Summary</div>
                          <pre className="bg-black/40 p-3 rounded border border-white/5 overflow-x-auto">
                            {JSON.stringify(run.input_summary, null, 2) || "No input data"}
                          </pre>
                        </div>
                        
                        {run.error_message && (
                           <div className="p-3 bg-accent-error/10 border border-accent-error/20 rounded text-accent-error">
                             <div className="flex items-center gap-2 mb-1 font-bold">
                               <AlertTriangle size={14} />
                               Error Output
                             </div>
                             {run.error_message}
                           </div>
                        )}

                        <div>
                          <div className="text-text-tertiary mb-1 uppercase">Output Summary</div>
                          <pre className="bg-black/40 p-3 rounded border border-white/5 overflow-x-auto text-accent-success/80">
                            {JSON.stringify(run.output_summary, null, 2) || "No output data"}
                          </pre>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))
          )}
        </div>
      </GlassCard>
    </div>
  )
}
