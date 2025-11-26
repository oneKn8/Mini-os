import { motion } from 'framer-motion'
import { Calendar, Clock, MapPin, X, Check, Edit2, Save } from 'lucide-react'
import { useState } from 'react'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface ApprovalCardProps {
    proposal: {
        id: string
        agent_name: string
        action_type: string
        risk_level: string
        explanation: string
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        payload: any
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onApprove: (id: string, editedPayload?: any) => void
    onReject: (id: string) => void
}

export default function ApprovalCard({ proposal, onApprove, onReject }: ApprovalCardProps) {
    const { payload, explanation } = proposal
    const [isEditing, setIsEditing] = useState(false)
    const [editedPayload, setEditedPayload] = useState(payload)

    const isEmail = proposal.action_type === 'create_email_draft'
    const isEvent = proposal.action_type === 'create_calendar_event'

    const handleSave = () => {
        setIsEditing(false)
        onApprove(proposal.id, editedPayload)
    }

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
                {!isEditing && (
                    <button
                        onClick={() => setIsEditing(true)}
                        className="p-1.5 rounded-lg text-text-tertiary hover:text-text-primary hover:bg-bg-secondary transition-colors"
                        title="Edit draft"
                    >
                        <Edit2 size={16} />
                    </button>
                )}
            </div>

            {/* Content Preview/Editor */}
            <div className="p-4 space-y-3">
                {isEmail && (
                    <div className="space-y-3 text-sm">
                        <div className="grid grid-cols-[60px_1fr] gap-2 items-center">
                            <span className="text-text-tertiary">To:</span>
                            {isEditing ? (
                                <input
                                    type="email"
                                    value={editedPayload.to || ''}
                                    onChange={(e) => setEditedPayload({ ...editedPayload, to: e.target.value })}
                                    className="px-2 py-1.5 rounded border border-border-medium bg-bg-secondary text-text-primary text-sm focus:border-accent-primary focus:outline-none"
                                />
                            ) : (
                                <span className="font-medium text-text-primary">{payload.to}</span>
                            )}
                        </div>
                        <div className="grid grid-cols-[60px_1fr] gap-2 items-center">
                            <span className="text-text-tertiary">Subj:</span>
                            {isEditing ? (
                                <input
                                    type="text"
                                    value={editedPayload.subject || ''}
                                    onChange={(e) => setEditedPayload({ ...editedPayload, subject: e.target.value })}
                                    className="px-2 py-1.5 rounded border border-border-medium bg-bg-secondary text-text-primary text-sm focus:border-accent-primary focus:outline-none"
                                />
                            ) : (
                                <span className="font-medium text-text-primary">{payload.subject}</span>
                            )}
                        </div>
                        <div className="space-y-1">
                            <span className="text-text-tertiary text-xs">Body:</span>
                            {isEditing ? (
                                <textarea
                                    value={editedPayload.body || ''}
                                    onChange={(e) => setEditedPayload({ ...editedPayload, body: e.target.value })}
                                    rows={6}
                                    className="w-full px-2 py-1.5 rounded border border-border-medium bg-bg-secondary text-text-primary text-sm focus:border-accent-primary focus:outline-none resize-y"
                                />
                            ) : (
                                <div className="mt-1 p-3 bg-bg-secondary rounded-lg border border-border-light text-text-secondary whitespace-pre-wrap max-h-32 overflow-y-auto text-xs">
                                    {payload.body}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {isEvent && (
                    <div className="space-y-3 text-sm">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-accent-primary/10 flex items-center justify-center text-accent-primary shrink-0">
                                <Calendar size={20} />
                            </div>
                            <div className="flex-1">
                                {isEditing ? (
                                    <input
                                        type="text"
                                        value={editedPayload.title || ''}
                                        onChange={(e) => setEditedPayload({ ...editedPayload, title: e.target.value })}
                                        className="w-full px-2 py-1.5 rounded border border-border-medium bg-bg-secondary text-text-primary text-sm font-semibold focus:border-accent-primary focus:outline-none"
                                        placeholder="Event title"
                                    />
                                ) : (
                                    <div className="font-semibold text-text-primary">{payload.title}</div>
                                )}
                                <div className="flex items-center gap-2 text-xs text-text-tertiary mt-0.5">
                                    <Clock size={12} />
                                    {isEditing ? (
                                        <div className="flex gap-2">
                                            <input
                                                type="datetime-local"
                                                value={editedPayload.start ? new Date(editedPayload.start).toISOString().slice(0, 16) : ''}
                                                onChange={(e) => setEditedPayload({ ...editedPayload, start: new Date(e.target.value).toISOString() })}
                                                className="px-2 py-1 rounded border border-border-medium bg-bg-secondary text-text-primary text-xs focus:border-accent-primary focus:outline-none"
                                            />
                                        </div>
                                    ) : (
                                        <span>{new Date(payload.start).toLocaleString()}</span>
                                    )}
                                </div>
                            </div>
                        </div>
                        
                        {isEditing ? (
                            <div className="space-y-2">
                                <div>
                                    <span className="text-text-tertiary text-xs">Description:</span>
                                    <textarea
                                        value={editedPayload.description || ''}
                                        onChange={(e) => setEditedPayload({ ...editedPayload, description: e.target.value })}
                                        rows={3}
                                        className="w-full mt-1 px-2 py-1.5 rounded border border-border-medium bg-bg-secondary text-text-primary text-xs focus:border-accent-primary focus:outline-none resize-y"
                                    />
                                </div>
                                <div>
                                    <span className="text-text-tertiary text-xs">Location:</span>
                                    <input
                                        type="text"
                                        value={editedPayload.location || ''}
                                        onChange={(e) => setEditedPayload({ ...editedPayload, location: e.target.value })}
                                        className="w-full mt-1 px-2 py-1.5 rounded border border-border-medium bg-bg-secondary text-text-primary text-xs focus:border-accent-primary focus:outline-none"
                                    />
                                </div>
                            </div>
                        ) : (
                            <>
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
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className="p-3 bg-bg-secondary border-t border-border-light flex gap-2">
                {isEditing ? (
                    <>
                        <button 
                            onClick={() => { setIsEditing(false); setEditedPayload(payload); }}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-border-medium text-text-secondary hover:bg-surface hover:text-text-primary transition-colors text-sm font-medium"
                        >
                            <X size={16} />
                            Cancel
                        </button>
                        <button 
                            onClick={handleSave}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-accent-primary text-white hover:bg-accent-primary-hover transition-colors text-sm font-medium shadow-sm"
                        >
                            <Save size={16} />
                            Save & Approve
                        </button>
                    </>
                ) : (
                    <>
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
                    </>
                )}
            </div>
        </motion.div>
    )
}
