import { motion } from 'framer-motion'
import { Calendar, Clock, MapPin, X, Check, Edit2 } from 'lucide-react'
import { useState } from 'react'

interface ApprovalCardProps {
    proposal: {
        id: string
        agent_name: string
        action_type: string
        risk_level: string
        explanation: string
        payload: any
    }
    onApprove: (id: string) => void
    onReject: (id: string) => void
}

export default function ApprovalCard({ proposal, onApprove, onReject }: ApprovalCardProps) {
    const { payload, explanation } = proposal
    const [isExpanded, setIsExpanded] = useState(true)

    const isEmail = proposal.action_type === 'create_email_draft'
    const isEvent = proposal.action_type === 'create_calendar_event'

    return (
        <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="rounded-xl border border-border-light bg-surface shadow-sm overflow-hidden my-3"
        >
            {/* Header */}
            <div className="bg-bg-secondary/50 px-4 py-3 border-b border-border-light flex justify-between items-start">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-accent-warning/10 text-accent-warning">
                            Approval Needed
                        </span>
                        <span className="text-xs text-text-tertiary capitalize">{proposal.agent_name}</span>
                    </div>
                    <p className="text-sm font-medium text-text-primary">{explanation}</p>
                </div>
            </div>

            {/* Content Preview */}
            <div className="p-4 space-y-3">
                {isEmail && (
                    <div className="space-y-2 text-sm">
                        <div className="grid grid-cols-[50px_1fr] gap-2">
                            <span className="text-text-tertiary">To:</span>
                            <span className="font-medium text-text-primary">{payload.to}</span>
                        </div>
                        <div className="grid grid-cols-[50px_1fr] gap-2">
                            <span className="text-text-tertiary">Subj:</span>
                            <span className="font-medium text-text-primary">{payload.subject}</span>
                        </div>
                        <div className="mt-2 p-3 bg-bg-secondary rounded-lg border border-border-light text-text-secondary whitespace-pre-wrap max-h-32 overflow-y-auto text-xs">
                            {payload.body}
                        </div>
                    </div>
                )}

                {isEvent && (
                    <div className="space-y-3 text-sm">
                         <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-accent-primary/10 flex items-center justify-center text-accent-primary">
                                <Calendar size={20} />
                            </div>
                            <div>
                                <div className="font-semibold text-text-primary">{payload.title}</div>
                                <div className="flex items-center gap-2 text-xs text-text-tertiary mt-0.5">
                                    <Clock size={12} />
                                    <span>{new Date(payload.start).toLocaleString()}</span>
                                </div>
                            </div>
                         </div>
                         
                         {payload.description && (
                            <p className="text-xs text-text-secondary bg-bg-secondary p-2 rounded border border-border-light">
                                {payload.description}
                            </p>
                         )}
                         
                         {payload.location && (
                             <div className="flex items-center gap-2 text-xs text-text-secondary">
                                 <MapPin size={12} />
                                 <span>{payload.location}</span>
                             </div>
                         )}
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className="p-3 bg-bg-secondary border-t border-border-light flex gap-2">
                <button 
                    onClick={() => onReject(proposal.id)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-border-medium text-text-secondary hover:bg-surface hover:text-text-primary transition-colors text-sm font-medium"
                >
                    <X size={16} />
                    Reject
                </button>
                <button 
                    onClick={() => onApprove(proposal.id)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-accent-primary text-white hover:bg-accent-primary-hover transition-colors text-sm font-medium shadow-sm"
                >
                    <Check size={16} />
                    Approve
                </button>
            </div>
        </motion.div>
    )
}

