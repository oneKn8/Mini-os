import { Calendar, Mail, X, Check, Edit2, Save } from 'lucide-react'
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
  onApprove: (id: string, editedPayload?: any, skipFuture?: boolean) => void
  onReject: (id: string) => void
}

export default function ApprovalCard({ proposal, onApprove, onReject }: ApprovalCardProps) {
  const { payload, explanation } = proposal
  const [isEditing, setIsEditing] = useState(false)
  const [editedPayload, setEditedPayload] = useState(payload)
  const [dontAskAgain, setDontAskAgain] = useState(false)

  const isEmail = proposal.action_type === 'create_email_draft'
  const isEvent = proposal.action_type === 'create_calendar_event'

  // Friendly action type labels
  const actionLabels: Record<string, string> = {
    create_email_draft: 'email drafts',
    create_calendar_event: 'calendar events',
    send_email: 'sending emails',
  }
  const actionLabel = actionLabels[proposal.action_type] || proposal.action_type.replace(/_/g, ' ')

  const handleApprove = () => {
    onApprove(proposal.id, isEditing ? editedPayload : undefined, dontAskAgain)
  }

  const handleSave = () => {
    setIsEditing(false)
    onApprove(proposal.id, editedPayload, dontAskAgain)
  }

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString('en-US', {
        weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
      })
    } catch { return dateStr }
  }

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-zinc-800/50 flex justify-between items-start">
        <div className="flex items-center gap-2">
          {isEvent ? <Calendar size={14} className="text-zinc-500" /> : <Mail size={14} className="text-zinc-500" />}
          <span className="text-xs text-amber-500/80 font-medium">Needs approval</span>
        </div>
        {!isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            className="p-1 text-zinc-600 hover:text-zinc-400 transition-colors"
          >
            <Edit2 size={14} />
          </button>
        )}
      </div>

      {/* Content */}
      <div className="p-4 space-y-3 text-sm">
        <p className="text-zinc-300">{explanation}</p>

        {isEmail && (
          <div className="space-y-2 text-xs">
            <div className="flex gap-2">
              <span className="text-zinc-600 w-10">To:</span>
              {isEditing ? (
                <input
                  value={editedPayload.to || ''}
                  onChange={(e) => setEditedPayload({ ...editedPayload, to: e.target.value })}
                  className="flex-1 px-2 py-1 bg-zinc-800/50 border border-zinc-700/50 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                />
              ) : (
                <span className="text-zinc-300">{payload.to}</span>
              )}
            </div>
            <div className="flex gap-2">
              <span className="text-zinc-600 w-10">Subj:</span>
              {isEditing ? (
                <input
                  value={editedPayload.subject || ''}
                  onChange={(e) => setEditedPayload({ ...editedPayload, subject: e.target.value })}
                  className="flex-1 px-2 py-1 bg-zinc-800/50 border border-zinc-700/50 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                />
              ) : (
                <span className="text-zinc-300">{payload.subject}</span>
              )}
            </div>
            {isEditing && (
              <textarea
                value={editedPayload.body || ''}
                onChange={(e) => setEditedPayload({ ...editedPayload, body: e.target.value })}
                rows={4}
                className="w-full px-2 py-1 bg-zinc-800/50 border border-zinc-700/50 rounded text-zinc-200 focus:outline-none focus:border-zinc-600 resize-none"
              />
            )}
          </div>
        )}

        {isEvent && (
          <div className="space-y-2 text-xs">
            <div className="flex gap-2">
              <span className="text-zinc-600 w-10">Title:</span>
              {isEditing ? (
                <input
                  value={editedPayload.title || ''}
                  onChange={(e) => setEditedPayload({ ...editedPayload, title: e.target.value })}
                  className="flex-1 px-2 py-1 bg-zinc-800/50 border border-zinc-700/50 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
                />
              ) : (
                <span className="text-zinc-300">{payload.title}</span>
              )}
            </div>
            <div className="flex gap-2">
              <span className="text-zinc-600 w-10">When:</span>
              <span className="text-zinc-300">{formatDate(payload.start || payload.start_time)}</span>
            </div>
            {payload.location && (
              <div className="flex gap-2">
                <span className="text-zinc-600 w-10">Where:</span>
                <span className="text-zinc-300">{payload.location}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Don't ask again checkbox */}
      <div className="px-4 pb-2">
        <label className="flex items-center gap-2 cursor-pointer group">
          <input
            type="checkbox"
            checked={dontAskAgain}
            onChange={(e) => setDontAskAgain(e.target.checked)}
            className="w-3.5 h-3.5 rounded border-zinc-700 bg-zinc-800/50 text-zinc-500 
                       focus:ring-0 focus:ring-offset-0 cursor-pointer"
          />
          <span className="text-xs text-zinc-500 group-hover:text-zinc-400 transition-colors">
            Don't ask again for {actionLabel}
          </span>
        </label>
      </div>

      {/* Actions */}
      <div className="px-4 py-3 border-t border-zinc-800/50 flex justify-between items-center">
        <span className="text-xs text-zinc-600">Press Enter to approve</span>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <button
                onClick={() => { setIsEditing(false); setEditedPayload(payload) }}
                className="px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="flex items-center gap-1 px-3 py-1.5 text-xs bg-zinc-800 text-zinc-200 rounded 
                           border border-zinc-700/50 hover:bg-zinc-700 transition-colors"
              >
                <Save size={12} />
                Save & Approve
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => onReject(proposal.id)}
                className="flex items-center gap-1 px-3 py-1.5 text-xs text-zinc-500 hover:text-red-400 transition-colors"
              >
                <X size={12} />
                Reject
              </button>
              <button
                onClick={handleApprove}
                className="flex items-center gap-1 px-3 py-1.5 text-xs bg-zinc-800 text-zinc-200 rounded 
                           border border-zinc-700/50 hover:bg-zinc-700 transition-colors"
              >
                <Check size={12} />
                Approve
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
