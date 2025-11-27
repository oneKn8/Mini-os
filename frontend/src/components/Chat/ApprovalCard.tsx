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
          <span className="text-xs text-amber-500 font-medium">Needs approval</span>
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
                  className="flex-1 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
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
                  className="flex-1 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
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
                className="w-full px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600 resize-none"
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
                  className="flex-1 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-zinc-600"
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

      {/* Actions */}
      <div className="px-4 py-3 border-t border-zinc-800/50 flex justify-end gap-2">
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
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-zinc-700 text-zinc-100 rounded hover:bg-zinc-600 transition-colors"
            >
              <Save size={12} />
              Save & Approve
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => onReject(proposal.id)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs text-zinc-400 hover:text-red-400 transition-colors"
            >
              <X size={12} />
              Reject
            </button>
            <button
              onClick={() => onApprove(proposal.id)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-zinc-700 text-zinc-100 rounded hover:bg-zinc-600 transition-colors"
            >
              <Check size={12} />
              Approve
            </button>
          </>
        )}
      </div>
    </div>
  )
}
