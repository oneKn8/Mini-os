import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { X, Edit2, Check, Mail, AlertCircle } from 'lucide-react'
import { clsx } from 'clsx'

interface EmailDraft {
  id: string
  to: string
  subject: string
  body: string
  action_type: string
  agent_name?: string
  explanation?: string
  risk_level?: string
  isManualReply?: boolean
  fromPreviewId?: string
}

interface EmailComposerProps {
  draft: EmailDraft | null
  onSend: (id: string, editedDraft?: Partial<EmailDraft>) => Promise<void>
  onReject: (id: string) => Promise<void>
  onClose: () => void
  isManualReply?: boolean
}

export default function EmailComposer({ draft, onSend, onReject, onClose, isManualReply = false }: EmailComposerProps) {
  const [isEditing, setIsEditing] = useState(isManualReply)
  const [editedDraft, setEditedDraft] = useState<EmailDraft | null>(draft)
  const [isSending, setIsSending] = useState(false)

  useEffect(() => {
    setEditedDraft(draft)
    setIsEditing(isManualReply)
  }, [draft, isManualReply])

  const handleSend = useCallback(async () => {
    if (!draft || !editedDraft) return
    try {
      setIsSending(true)
      const changes = isEditing ? {
        to: editedDraft.to,
        subject: editedDraft.subject,
        body: editedDraft.body,
      } : undefined
      await onSend(draft.id, changes)
    } finally {
      setIsSending(false)
    }
  }, [draft, editedDraft, isEditing, onSend])

  const handleReject = useCallback(async () => {
    if (!draft) return
    try {
      setIsSending(true)
      await onReject(draft.id)
    } finally {
      setIsSending(false)
    }
  }, [draft, onReject])

  if (!draft || !editedDraft) {
    return null
  }

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        if (editedDraft && editedDraft.to && editedDraft.subject && !isSending) {
          handleSend()
        }
      } else if (e.key === 'Escape') {
        e.preventDefault()
        handleReject()
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [editedDraft, isSending, handleSend, handleReject])

  const riskColor = {
    low: 'text-green-400 bg-green-500/10 border-green-500/30',
    medium: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    high: 'text-red-400 bg-red-500/10 border-red-500/30',
  }[draft.risk_level || 'low']

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="flex-1 flex flex-col h-full bg-zinc-900/50 border border-zinc-800/50 rounded-xl overflow-hidden"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-zinc-800/50 flex items-center justify-between bg-zinc-900/30">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/30">
            <Mail size={18} className="text-blue-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-zinc-200">
              {isManualReply
                ? (draft.action_type === 'manual_compose' ? 'Compose Email' : 'Compose Reply')
                : 'Draft Email'}
            </h2>
            {!isManualReply && draft.agent_name && (
              <p className="text-xs text-zinc-500">Suggested by {draft.agent_name}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!isManualReply && draft.risk_level && (
            <span className={clsx(
              'px-2 py-1 rounded text-xs font-medium border',
              riskColor
            )}>
              {draft.risk_level} risk
            </span>
          )}
          <button
            onClick={onClose}
            className="p-2 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 rounded-lg transition-colors"
            aria-label="Close composer"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Agent Explanation Banner */}
      {!isManualReply && draft.explanation && (
        <div className="mx-6 mt-4 p-3 rounded-lg bg-blue-500/5 border border-blue-500/20 flex gap-3">
          <AlertCircle size={16} className="text-blue-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-zinc-300">{draft.explanation}</p>
        </div>
      )}

      {/* Email Form */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {/* To Field */}
        <div className="space-y-2">
          <label className="text-xs text-zinc-500 font-medium uppercase tracking-wider">
            To
          </label>
          <input
            type="email"
            value={editedDraft.to}
            onChange={(e) => {
              setEditedDraft({ ...editedDraft, to: e.target.value })
              if (!isEditing) setIsEditing(true)
            }}
            className={clsx(
              'w-full px-4 py-2.5 bg-zinc-900/50 border rounded-lg text-zinc-200',
              'placeholder-zinc-600 focus:outline-none transition-colors',
              isEditing ? 'border-blue-500/50 focus:border-blue-500' : 'border-zinc-800/50 focus:border-zinc-700'
            )}
            placeholder="recipient@example.com"
            disabled={isSending}
          />
        </div>

        {/* Subject Field */}
        <div className="space-y-2">
          <label className="text-xs text-zinc-500 font-medium uppercase tracking-wider">
            Subject
          </label>
          <input
            type="text"
            value={editedDraft.subject}
            onChange={(e) => {
              setEditedDraft({ ...editedDraft, subject: e.target.value })
              if (!isEditing) setIsEditing(true)
            }}
            className={clsx(
              'w-full px-4 py-2.5 bg-zinc-900/50 border rounded-lg text-zinc-200',
              'placeholder-zinc-600 focus:outline-none transition-colors',
              isEditing ? 'border-blue-500/50 focus:border-blue-500' : 'border-zinc-800/50 focus:border-zinc-700'
            )}
            placeholder="Email subject"
            disabled={isSending}
          />
        </div>

        {/* Body Field */}
        <div className="space-y-2 flex-1">
          <label className="text-xs text-zinc-500 font-medium uppercase tracking-wider">
            Message
          </label>
          <textarea
            value={editedDraft.body}
            onChange={(e) => {
              setEditedDraft({ ...editedDraft, body: e.target.value })
              if (!isEditing) setIsEditing(true)
            }}
            rows={12}
            className={clsx(
              'w-full px-4 py-3 bg-zinc-900/50 border rounded-lg text-zinc-200',
              'placeholder-zinc-600 focus:outline-none transition-colors resize-none',
              isEditing ? 'border-blue-500/50 focus:border-blue-500' : 'border-zinc-800/50 focus:border-zinc-700'
            )}
            placeholder="Compose your email..."
            disabled={isSending}
          />
        </div>

        {isEditing && (
          <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/5 border border-amber-500/20 rounded-lg p-3">
            <Edit2 size={14} />
            <span>You've modified this draft</span>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="px-6 py-4 border-t border-zinc-800/50 bg-zinc-900/30 flex justify-between items-center">
        <button
          onClick={handleReject}
          disabled={isSending}
          className={clsx(
            'px-4 py-2 rounded-lg border transition-colors font-medium text-sm',
            'border-zinc-700 text-zinc-400 hover:text-red-400 hover:border-red-500/50 hover:bg-red-500/5',
            isSending && 'opacity-50 cursor-not-allowed'
          )}
        >
          <X size={14} className="inline mr-2" />
          {isManualReply ? 'Cancel' : 'Reject'}
        </button>

        <div className="flex items-center gap-3">
          <span className="text-xs text-zinc-600">
            <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-zinc-400">Cmd+Enter</kbd> to send,{' '}
            <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-zinc-400">Esc</kbd> to {isManualReply ? 'cancel' : 'reject'}
          </span>
          <button
            onClick={handleSend}
            disabled={isSending || !editedDraft.to || !editedDraft.subject}
            className={clsx(
              'px-6 py-2.5 rounded-lg font-semibold text-sm transition-all flex items-center gap-2',
              'bg-blue-500 text-white hover:bg-blue-600 shadow-lg shadow-blue-500/20',
              (isSending || !editedDraft.to || !editedDraft.subject) && 'opacity-50 cursor-not-allowed'
            )}
          >
            {isSending ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Check size={14} />
                {isManualReply
                  ? (draft.action_type === 'manual_compose' ? 'Send Email' : 'Send Reply')
                  : (isEditing ? 'Send Modified Draft' : 'Send Draft')}
              </>
            )}
          </button>
        </div>
      </div>
    </motion.div>
  )
}
