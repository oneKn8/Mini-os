import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
    Mail, 
    Calendar, 
    CheckSquare, 
    Clock, 
    CheckCircle2, 
    XCircle, 
    User, 
    MapPin,
    MessageSquare,
    Filter
} from 'lucide-react'
import { clsx } from 'clsx'

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
  const [filter, setFilter] = useState<'pending' | 'all'>('pending')

  useEffect(() => {
    fetchActions()
  }, [])

  const fetchActions = async () => {
    try {
      const response = await fetch('/api/actions')
      if (response.ok) {
        const data = await response.json()
        setActions(data.actions || [])
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
      setActions(actions.map(a => a.id === actionId ? { ...a, status: 'approved' } : a))
    } catch (error) {
      console.error('Failed to approve action:', error)
    }
  }

  const handleReject = async (actionId: string) => {
    try {
      await fetch(`/api/actions/${actionId}/reject`, { method: 'POST' })
      setActions(actions.map(a => a.id === actionId ? { ...a, status: 'rejected' } : a))
    } catch (error) {
      console.error('Failed to reject action:', error)
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'email_reply': return <Mail size={18} className="text-accent-primary" />
      case 'calendar_event': return <Calendar size={18} className="text-accent-secondary" />
      case 'task_create': return <CheckSquare size={18} className="text-accent-success" />
      case 'reminder': return <Clock size={18} className="text-accent-warning" />
      default: return <CheckCircle2 size={18} className="text-accent-primary" />
    }
  }
  
  const filteredActions = actions.filter(a => 
    filter === 'all' || a.status === 'pending'
  )

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }
  
  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  }

  if (loading) {
      return (
        <div className="flex h-[60vh] items-center justify-center">
            <div className="spinner-large text-accent-primary"></div>
        </div>
      )
  }

  return (
    <div className="space-y-8 pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h1 className="text-3xl font-bold text-text-primary">Proposed Actions</h1>
        
        <div className="flex bg-surface p-1 rounded-xl border border-border-light shadow-sm">
          <button
            onClick={() => setFilter('pending')}
            className={clsx(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all",
              filter === 'pending' 
                ? "bg-bg-secondary text-text-primary shadow-sm" 
                : "text-text-secondary hover:text-text-primary"
            )}
          >
            Pending ({actions.filter(a => a.status === 'pending').length})
          </button>
          <button
            onClick={() => setFilter('all')}
            className={clsx(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all",
              filter === 'all' 
                ? "bg-bg-secondary text-text-primary shadow-sm" 
                : "text-text-secondary hover:text-text-primary"
            )}
          >
            All ({actions.length})
          </button>
        </div>
      </div>

      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid gap-6 md:grid-cols-2 lg:grid-cols-2"
      >
        {filteredActions.map((action) => (
          <motion.div
            key={action.id}
            variants={item}
            className={clsx(
              "group relative flex flex-col rounded-2xl border bg-surface p-6 transition-all",
              action.status === 'pending' 
                ? "border-border-light shadow-sm hover:shadow-md hover:border-accent-primary/30" 
                : "border-border-light opacity-70 bg-bg-secondary/30"
            )}
          >
             <div className="mb-4 flex items-start justify-between">
                <div className="flex items-center gap-3">
                    <div className={clsx(
                        "flex h-10 w-10 items-center justify-center rounded-full bg-bg-secondary",
                        action.type === 'email_reply' && "bg-accent-primary/10",
                        action.type === 'calendar_event' && "bg-accent-secondary/10",
                        action.type === 'task_create' && "bg-accent-success/10",
                        action.type === 'reminder' && "bg-accent-warning/10"
                    )}>
                        {getTypeIcon(action.type)}
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-medium uppercase tracking-wider text-text-tertiary">
                                {action.type.replace('_', ' ')}
                            </span>
                            <span className="rounded-full bg-accent-success/10 px-1.5 py-0.5 text-[10px] font-medium text-accent-success">
                                {Math.round(action.confidence * 100)}% match
                            </span>
                        </div>
                        <div className="text-xs text-text-tertiary mt-0.5">
                            Proposed by <span className="font-medium text-text-secondary">{action.proposed_by}</span>
                        </div>
                    </div>
                </div>
             </div>

             <h3 className="text-lg font-bold text-text-primary mb-2">{action.title}</h3>
             <p className="text-text-secondary text-sm mb-6">{action.description}</p>

             {action.preview && (
                 <div className="mb-6 rounded-xl bg-bg-secondary/50 p-4 text-sm border border-border-light space-y-2">
                    {action.preview.to && (
                        <div className="flex gap-2">
                            <User size={14} className="text-text-tertiary mt-1" />
                            <div><span className="text-text-tertiary">To:</span> <span className="text-text-primary">{action.preview.to}</span></div>
                        </div>
                    )}
                    {action.preview.subject && (
                        <div className="flex gap-2">
                            <MessageSquare size={14} className="text-text-tertiary mt-1" />
                            <div><span className="text-text-tertiary">Subject:</span> <span className="text-text-primary">{action.preview.subject}</span></div>
                        </div>
                    )}
                    {action.preview.time && (
                        <div className="flex gap-2">
                            <Clock size={14} className="text-text-tertiary mt-1" />
                            <div><span className="text-text-tertiary">Time:</span> <span className="text-text-primary">{action.preview.time}</span></div>
                        </div>
                    )}
                    {action.preview.location && (
                        <div className="flex gap-2">
                            <MapPin size={14} className="text-text-tertiary mt-1" />
                            <div><span className="text-text-tertiary">Location:</span> <span className="text-text-primary">{action.preview.location}</span></div>
                        </div>
                    )}
                    {action.preview.body && (
                        <div className="mt-2 pl-2 border-l-2 border-border-medium text-text-secondary italic text-xs line-clamp-3">
                            "{action.preview.body}"
                        </div>
                    )}
                 </div>
             )}

             <div className="mt-auto pt-4 border-t border-border-light flex items-center justify-end gap-3">
                {action.status === 'pending' ? (
                    <>
                        <button
                            onClick={() => handleReject(action.id)}
                            className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-text-secondary hover:bg-bg-secondary hover:text-accent-error transition-colors"
                        >
                            <XCircle size={16} />
                            Reject
                        </button>
                        <button
                            onClick={() => handleApprove(action.id)}
                            className="flex items-center gap-2 rounded-lg bg-accent-primary px-4 py-2 text-sm font-medium text-white hover:bg-accent-primary-hover shadow-sm hover:shadow transition-all"
                        >
                            <CheckCircle2 size={16} />
                            Approve
                        </button>
                    </>
                ) : (
                    <div className={clsx(
                        "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium",
                        action.status === 'approved' ? "bg-accent-success/10 text-accent-success" : "bg-accent-error/10 text-accent-error"
                    )}>
                        {action.status === 'approved' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                        <span className="capitalize">{action.status}</span>
                    </div>
                )}
             </div>
          </motion.div>
        ))}

        {filteredActions.length === 0 && (
          <div className="col-span-full flex flex-col items-center justify-center py-20 rounded-3xl border border-dashed border-border-dark/30 bg-surface/50">
             <div className="mb-4 rounded-full bg-bg-secondary p-4">
                <CheckCircle2 size={32} className="text-text-muted" />
             </div>
             <h3 className="text-lg font-semibold text-text-primary">No {filter === 'pending' ? 'pending' : ''} actions</h3>
             <p className="text-text-secondary">AI agents will propose actions here for your review</p>
          </div>
        )}
      </motion.div>
    </div>
  )
}
