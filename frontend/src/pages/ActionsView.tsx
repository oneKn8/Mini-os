import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
    Mail, 
    Calendar, 
    CheckSquare, 
    Clock, 
    CheckCircle2, 
    XCircle, 
    Zap
} from 'lucide-react'
import GlassCard from '../components/UI/GlassCard'

interface Action {
  id: string
  type: 'email_reply' | 'calendar_event' | 'task_create' | 'reminder'
  title: string
  description: string
  proposed_by: string
  confidence: number
  created_at: string
  status: 'pending' | 'approved' | 'rejected'
  preview?: {
    to?: string
    subject?: string
    body?: string
    time?: string
    location?: string
  }
}

export default function ActionsView() {
  const [actions, setActions] = useState<Action[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchActions()
  }, [])

  const fetchActions = async () => {
    try {
      const response = await fetch('/api/actions/pending')
      if (response.ok) {
        const data = await response.json()
        setActions(Array.isArray(data) ? data : [])
      }
    } catch (error) {
      console.error('Failed to fetch actions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (actionId: string) => {
    try {
      await fetch(`/api/actions/${actionId}/approve`, { method: 'POST' })
      setActions(actions.filter(a => a.id !== actionId))
    } catch (error) {
      console.error('Failed to approve action:', error)
    }
  }

  const handleReject = async (actionId: string) => {
    try {
      await fetch(`/api/actions/${actionId}/reject`, { method: 'POST' })
      setActions(actions.filter(a => a.id !== actionId))
    } catch (error) {
      console.error('Failed to reject action:', error)
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'email_reply': return <Mail size={20} className="text-accent-primary" />
      case 'calendar_event': return <Calendar size={20} className="text-accent-secondary" />
      case 'task_create': return <CheckSquare size={20} className="text-accent-success" />
      case 'reminder': return <Clock size={20} className="text-accent-warning" />
      default: return <CheckCircle2 size={20} className="text-accent-primary" />
    }
  }

  return (
    <div className="space-y-8 pb-20">
      <div className="flex items-center gap-3">
        <h1 className="text-3xl font-bold text-white text-glow">Pending Actions</h1>
        <div className="bg-accent-warning/20 text-accent-warning px-3 py-1 rounded-full text-sm font-bold border border-accent-warning/30">
            {actions.length} Waiting
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-accent-primary border-t-transparent"></div>
        </div>
      ) : actions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center opacity-50">
           <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-6">
              <Zap size={32} className="text-text-tertiary" />
           </div>
           <h3 className="text-xl font-bold text-white">All Caught Up</h3>
           <p className="text-text-secondary mt-2">No pending actions requiring your approval.</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3">
           {actions.map((action, index) => (
             <motion.div
               key={action.id}
               initial={{ opacity: 0, y: 20 }}
               animate={{ opacity: 1, y: 0 }}
               transition={{ delay: index * 0.1 }}
             >
               <GlassCard className="flex flex-col h-full" hoverEffect>
                  {/* Header */}
                  <div className="p-6 border-b border-white/5">
                     <div className="flex justify-between items-start mb-4">
                        <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                           {getTypeIcon(action.type)}
                        </div>
                        <div className="flex flex-col items-end">
                           <span className="text-[10px] uppercase text-text-tertiary tracking-widest font-bold">Confidence</span>
                           <span className={`text-lg font-bold ${action.confidence > 0.8 ? 'text-accent-success' : 'text-accent-warning'}`}>
                             {Math.round(action.confidence * 100)}%
                           </span>
                        </div>
                     </div>
                     <h3 className="text-lg font-bold text-white line-clamp-2">{action.title}</h3>
                     <div className="flex items-center gap-2 mt-2 text-xs text-text-secondary">
                        <span className="text-text-tertiary">Proposed by</span>
                        <span className="text-accent-info">{action.proposed_by}</span>
                     </div>
                  </div>

                  {/* Body */}
                  <div className="p-6 flex-1 text-sm text-text-secondary space-y-4">
                     <p>{action.description}</p>
                     
                     {action.preview && (
                       <div className="bg-black/30 rounded-lg p-3 border border-white/5 space-y-2">
                          {action.preview.to && (
                            <div className="flex gap-2 text-xs">
                               <span className="text-text-tertiary w-12">To:</span>
                               <span className="text-white">{action.preview.to}</span>
                            </div>
                          )}
                          {action.preview.subject && (
                            <div className="flex gap-2 text-xs">
                               <span className="text-text-tertiary w-12">Subject:</span>
                               <span className="text-white">{action.preview.subject}</span>
                            </div>
                          )}
                          {action.preview.time && (
                            <div className="flex gap-2 text-xs">
                               <span className="text-text-tertiary w-12">Time:</span>
                               <span className="text-white">{action.preview.time}</span>
                            </div>
                          )}
                       </div>
                     )}
                  </div>

                  {/* Footer Actions */}
                  <div className="p-4 border-t border-white/5 grid grid-cols-2 gap-3">
                     <button 
                       onClick={() => handleReject(action.id)}
                       className="py-2.5 rounded-xl border border-white/10 hover:bg-accent-error/20 hover:border-accent-error/50 hover:text-accent-error transition-all font-medium text-sm flex items-center justify-center gap-2"
                     >
                        <XCircle size={16} />
                        Reject
                     </button>
                     <button 
                       onClick={() => handleApprove(action.id)}
                       className="py-2.5 rounded-xl bg-accent-primary hover:bg-accent-primary-hover text-white shadow-[0_0_15px_rgba(76,110,245,0.3)] transition-all font-bold text-sm flex items-center justify-center gap-2"
                     >
                        <CheckCircle2 size={16} />
                        Approve
                     </button>
                  </div>
               </GlassCard>
             </motion.div>
           ))}
        </div>
      )}
    </div>
  )
}
