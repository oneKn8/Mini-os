import { useState, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mail, RefreshCw, Search, Inbox as InboxIcon, PenSquare } from 'lucide-react'
import { clsx } from 'clsx'
import { useInboxWithRealtime } from '../hooks/useInbox'
import { fetchInboxItems, InboxItem } from '../api/inbox'
import EmailList from '../components/Inbox/EmailList'
import EmailViewer from '../components/Inbox/EmailViewer'
import EmailComposer from '../components/Inbox/EmailComposer'
import { useScreenUpdates, useScreenController } from '../store/screenController'
import { useChatStore } from '../store/chatStore'

// Category filters with subtle colors
const CATEGORIES = [
  { id: 'primary', label: 'Primary', color: 'bg-blue-500/60' },
  { id: 'promotions', label: 'Promotions', color: 'bg-emerald-500/60' },
  { id: 'social', label: 'Social', color: 'bg-violet-500/60' },
  { id: 'updates', label: 'Updates', color: 'bg-amber-500/60' },
  { id: 'sent', label: 'Sent', color: 'bg-zinc-500/60' },
  { id: 'spam', label: 'Spam', color: 'bg-red-500/70' },
  { id: 'trash', label: 'Trash', color: 'bg-zinc-600' },
  { id: 'all', label: 'All mail', color: 'bg-zinc-700' },
]

export default function InboxView() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [filter, setFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [replyTo, setReplyTo] = useState<string | null>(null)
  const [isComposing, setIsComposing] = useState(false)
  const [extraPages, setExtraPages] = useState<InboxItem[]>([])
  const [cursor, setCursor] = useState<string | null>(null)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [autoLoadTriggered, setAutoLoadTriggered] = useState(false)

  // Real-time inbox + agent previews
  const { items, isLoading, refresh, isRefreshing, nextCursor } = useInboxWithRealtime(filter === 'all' ? undefined : filter)
  const { previews, isAgentFocused } = useScreenUpdates('/inbox')
  const screenController = useScreenController()

  // Get pending email drafts from chat store
  const { pendingApprovals, handleApproval } = useChatStore()
  const emailDrafts = useMemo(() =>
    pendingApprovals.filter(p => p.action_type === 'create_email_draft'),
    [pendingApprovals]
  )
  const currentDraft = emailDrafts.length > 0 ? {
    id: emailDrafts[0].id,
    to: emailDrafts[0].payload?.to || '',
    subject: emailDrafts[0].payload?.subject || '',
    body: emailDrafts[0].payload?.body || '',
    action_type: emailDrafts[0].action_type,
    agent_name: emailDrafts[0].agent_name,
    explanation: emailDrafts[0].explanation,
    risk_level: emailDrafts[0].risk_level,
  } : null

  // Manual reply draft
  const replyItem = items.find(i => i.id === replyTo)
  const manualReplyDraft = replyItem ? {
    id: 'manual-reply',
    to: replyItem.sender || '',
    subject: replyItem.title.startsWith('Re: ') ? replyItem.title : `Re: ${replyItem.title}`,
    body: `\n\n---\nOn ${new Date(replyItem.received_at).toLocaleDateString()} ${replyItem.sender} wrote:\n${replyItem.body_preview}`,
    action_type: 'manual_reply',
    isManualReply: true,
    originalItemId: replyItem.id,
  } : null

  // New compose draft
  const newComposeDraft = isComposing ? {
    id: 'new-compose',
    to: '',
    subject: '',
    body: '',
    action_type: 'manual_compose',
    isManualReply: true,
  } : null

  // Agent preview draft (email_draft)
  const previewDraft = useMemo(() => {
    const preview = previews.find(p => p.type === 'email_draft')
    if (!preview) return null
    const data = preview.data || {}
    return {
      id: data.id || preview.id || 'preview-draft',
      to: data.to || '',
      subject: data.subject || '',
      body: data.body || '',
      action_type: data.mode === 'reply' ? 'manual_reply' : 'manual_compose',
      isManualReply: true,
      fromPreviewId: preview.id,
    }
  }, [previews])

  // Filter and search
  const filteredItems = useMemo(() => {
    const allItems = [...items, ...extraPages]

    // Group by thread_id (fallback to item.id) to mimic Gmail conversation view
    const threads = new Map<string, InboxItem & { message_count: number }>()

    allItems.forEach(item => {
      const key = item.thread_id || item.id
      const existing = threads.get(key)

      // Track latest message and count
      if (!existing) {
        threads.set(key, { ...item, message_count: 1 })
      } else {
        const existingDate = existing.received_at ? new Date(existing.received_at).getTime() : 0
        const newDate = item.received_at ? new Date(item.received_at).getTime() : 0
        const latest = newDate > existingDate ? item : existing
        threads.set(key, { ...latest, message_count: (existing.message_count || 1) + 1 })
      }
    })

    let result = Array.from(threads.values())

    // Sort by latest received_at
    result.sort((a, b) => {
      const aDate = a.received_at ? new Date(a.received_at).getTime() : 0
      const bDate = b.received_at ? new Date(b.received_at).getTime() : 0
      return bDate - aDate
    })

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(item =>
        item.title.toLowerCase().includes(query) ||
        item.sender?.toLowerCase().includes(query) ||
        item.body_preview.toLowerCase().includes(query)
      )
    }

    return result
  }, [items, extraPages, filter, searchQuery])

  const selectedItem = filteredItems.find(i => i.id === selectedId)

  // Handle draft approval
  const handleDraftSend = async (id: string, editedDraft?: Partial<typeof currentDraft>) => {
    await handleApproval(id, true, editedDraft)
  }

  const handleDraftReject = async (id: string) => {
    await handleApproval(id, false)
  }

  const handleCloseDraft = () => {
    if (currentDraft) {
      handleDraftReject(currentDraft.id)
    }
  }

  // Email actions
  const handleReply = (itemId: string) => {
    setReplyTo(itemId)
    setSelectedId(null)
  }

  const handleManualReplySend = async (_id: string, editedDraft?: any) => {
    if (!editedDraft || !replyItem) return
    try {
      // Send the email via API
      const response = await fetch('/api/inbox/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to: editedDraft.to,
          subject: editedDraft.subject,
          body: editedDraft.body,
          in_reply_to: replyItem.id,
        })
      })

      if (!response.ok) throw new Error('Failed to send email')

      // Mark original as read
      await fetch(`/api/inbox/${replyItem.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ read: true })
      })

      setReplyTo(null)
      refresh()
    } catch (error) {
      console.error('Failed to send reply:', error)
      alert('Failed to send email. Please try again.')
    }
  }

  const handleManualReplyCancel = async (_id: string) => {
    setReplyTo(null)
  }

  const handleCloseReply = () => {
    setReplyTo(null)
  }

  // Preview draft handlers
  const handlePreviewSend = async (_id: string, editedDraft?: any) => {
    await handleComposeSend(_id, editedDraft)
    if (previewDraft?.fromPreviewId) {
      screenController.removePreview(previewDraft.fromPreviewId)
    }
  }

  const handlePreviewReject = async (_id: string) => {
    if (previewDraft?.fromPreviewId) {
      screenController.removePreview(previewDraft.fromPreviewId)
    }
  }

  const handlePreviewClose = () => {
    if (previewDraft?.fromPreviewId) {
      screenController.removePreview(previewDraft.fromPreviewId)
    }
  }

  // Compose handlers
  const handleCompose = () => {
    setIsComposing(true)
    setSelectedId(null)
    setReplyTo(null)
  }

  // Reset pagination when filter changes
  useEffect(() => {
    setExtraPages([])
    setCursor(null)
    setAutoLoadTriggered(false)
  }, [filter])

  // Sync cursor from base query
  useEffect(() => {
    setCursor(nextCursor || null)
  }, [nextCursor])

  const handleLoadMore = async () => {
    if (!cursor || isLoadingMore) return
    try {
      setIsLoadingMore(true)
      const res = await fetchInboxItems({ filter: filter === 'all' ? undefined : filter, cursor })
      setExtraPages(prev => [...prev, ...(res.items || [])])
      setCursor(res.next_cursor)
    } catch (e) {
      console.error('Load more failed', e)
    } finally {
      setIsLoadingMore(false)
    }
  }

  // Auto-load next page if we have very few items and a cursor is available
  useEffect(() => {
    if (!autoLoadTriggered && cursor && filteredItems.length < 50 && !isLoadingMore && !isLoading) {
      setAutoLoadTriggered(true)
      handleLoadMore()
    }
  }, [cursor, filteredItems.length, isLoadingMore, isLoading, autoLoadTriggered])

  const handleComposeSend = async (_id: string, editedDraft?: any) => {
    if (!editedDraft) return
    try {
      const response = await fetch('/api/inbox/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to: editedDraft.to,
          subject: editedDraft.subject,
          body: editedDraft.body,
        })
      })

      if (!response.ok) throw new Error('Failed to send email')

      setIsComposing(false)
      refresh()
    } catch (error) {
      console.error('Failed to send email:', error)
      alert('Failed to send email. Please try again.')
    }
  }

  const handleComposeCancel = async (_id: string) => {
    setIsComposing(false)
  }

  const handleCloseCompose = () => {
    setIsComposing(false)
  }

  const handleArchive = async (itemId: string) => {
    try {
      await fetch(`/api/inbox/${itemId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ read: true, archived: true })
      })
      setSelectedId(null)
      refresh()
    } catch (error) {
      console.error('Failed to archive:', error)
    }
  }

  const handleDelete = async (itemId: string) => {
    if (!confirm('Delete this email?')) return
    try {
      await fetch(`/api/inbox/${itemId}`, { method: 'DELETE' })
      setSelectedId(null)
      refresh()
    } catch (error) {
      console.error('Failed to delete:', error)
    }
  }

  const handleMarkRead = async (itemId: string, read: boolean) => {
    try {
      await fetch(`/api/inbox/${itemId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ read })
      })
      refresh()
    } catch (error) {
      console.error('Failed to update read state:', error)
    }
  }

  return (
    <div className="h-full min-h-0 flex flex-col overflow-hidden" data-inbox-page>
      {/* Header stays in place; body does the scrolling */}
      <div className="flex-none z-50 bg-zinc-950/90 backdrop-blur-xl border-b border-zinc-800/70 shadow-[0_10px_30px_-18px_rgba(0,0,0,0.8)] pb-3">
        <div className="flex items-center justify-between py-3">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-medium text-zinc-200">Inbox</h1>
            {filteredItems.length > 0 && (
              <span className="px-2 py-0.5 rounded-full text-xs text-zinc-400 bg-zinc-800/50 border border-zinc-700/50">
                {filteredItems.length} {cursor && '+'}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCompose}
              className="px-3 py-2 rounded-lg border border-zinc-800/50 transition-all text-sm font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800/30 flex items-center gap-2"
            >
              <PenSquare size={14} />
              Compose
            </button>
            <button
              onClick={() => refresh()}
              disabled={isRefreshing}
              data-inbox-refresh
              className={clsx(
                "p-2 rounded-lg border border-zinc-800/50 transition-all",
                "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/30",
                isAgentFocused && "ring-1 ring-blue-500/30"
              )}
            >
              <RefreshCw size={16} className={clsx((isRefreshing || isLoading) && "animate-spin")} />
            </button>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="flex flex-col gap-2">
          {/* Search */}
          <div
            data-email-search
            className="relative flex-1"
          >
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
            <input
              type="text"
              placeholder="Search messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-zinc-900/50 border border-zinc-800/50 rounded-lg 
                        text-zinc-300 placeholder-zinc-600 focus:outline-none focus:border-zinc-700"
            />
          </div>

          {/* Tabs + folders */}
          <div className="flex items-center justify-between gap-2 pt-1">
            {/* Gmail-style tabs: All / Primary / Promotions / Social / Updates */}
            <div className="flex gap-1 flex-wrap">
              <button
                onClick={() => setFilter('all')}
                className={clsx(
                  "px-3 py-1.5 rounded-full text-xs font-medium transition-all border",
                  filter === 'all'
                    ? "bg-zinc-800 border-zinc-700 text-zinc-100"
                    : "bg-transparent border-transparent text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40"
                )}
              >
                All mail
              </button>
              {CATEGORIES.filter(c => ['primary','promotions','social','updates'].includes(c.id)).map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setFilter(cat.id)}
                  className={clsx(
                    "px-3 py-1.5 rounded-full text-xs font-medium transition-all border",
                    filter === cat.id
                      ? "bg-zinc-800 border-zinc-700 text-zinc-100"
                      : "bg-transparent border-transparent text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40"
                  )}
                >
                  <span className={clsx("inline-block w-1.5 h-1.5 rounded-full mr-1.5", cat.color)} />
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Folder shortcuts: Sent / Spam / Trash */}
            <div className="hidden sm:flex items-center gap-1 text-[11px]">
              {CATEGORIES.filter(c => ['sent','spam','trash'].includes(c.id)).map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setFilter(cat.id)}
                  className={clsx(
                    "px-2 py-1 rounded-md border text-[11px] font-medium transition-colors",
                    filter === cat.id
                      ? "bg-zinc-800 border-zinc-700 text-zinc-100"
                      : "bg-transparent border-zinc-800/60 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/60"
                  )}
                  title={cat.label}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 min-h-0 flex flex-col relative overflow-hidden pt-4">
        {/* Show Email Composer if there's a pending draft, reply, or new compose */}
        {previewDraft ? (
          <EmailComposer
            draft={previewDraft}
            onSend={handlePreviewSend}
            onReject={handlePreviewReject}
            onClose={handlePreviewClose}
            isManualReply
          />
        ) : currentDraft ? (
          <EmailComposer
            draft={currentDraft}
            onSend={handleDraftSend}
            onReject={handleDraftReject}
            onClose={handleCloseDraft}
          />
        ) : manualReplyDraft ? (
          <EmailComposer
            draft={manualReplyDraft}
            onSend={handleManualReplySend}
            onReject={handleManualReplyCancel}
            onClose={handleCloseReply}
            isManualReply
          />
        ) : newComposeDraft ? (
          <EmailComposer
            draft={newComposeDraft}
            onSend={handleComposeSend}
            onReject={handleComposeCancel}
            onClose={handleCloseCompose}
            isManualReply
          />
        ) : (
          <div className={clsx(
            "grid h-full min-h-0 gap-4 overflow-hidden",
            selectedItem ? "lg:grid-cols-[24rem_1fr]" : "lg:grid-cols-1"
          )}>
            {/* Email List */}
            <div
              data-component="email-list"
              data-email-list
              className={clsx(
                "flex flex-col bg-zinc-900/50 border border-zinc-800/50 rounded-xl overflow-hidden transition-all duration-300 h-full min-h-0",
                selectedItem ? "hidden lg:flex" : "flex"
              )}
            >
              {isLoading && filteredItems.length === 0 ? (
                <div className="flex-1 flex items-center justify-center">
                  <div className="flex items-center gap-2 text-zinc-600 text-sm">
                    <RefreshCw size={14} className="animate-spin" />
                    <span>Loading...</span>
                  </div>
                </div>
              ) : filteredItems.length === 0 ? (
                <EmptyState searchQuery={searchQuery} filter={filter} />
              ) : (
                <EmailList
                  items={filteredItems}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                />
              )}
              {cursor && (
                <div className="px-4 py-3 border-t border-zinc-800/50">
                  <button
                    onClick={handleLoadMore}
                    disabled={isLoadingMore}
                    className="w-full text-sm text-zinc-300 border border-zinc-800/60 rounded-lg py-2 hover:bg-zinc-800/40 disabled:opacity-50"
                  >
                    {isLoadingMore ? 'Loading…' : 'Load more'}
                  </button>
                </div>
              )}
            </div>

            {/* Email Viewer / Empty State */}
            <AnimatePresence mode="wait">
              {selectedItem ? (
                <motion.div
                  key={selectedItem.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="flex-1 min-w-0 min-h-0 h-full overflow-hidden"
                >
                  <EmailViewer
                    itemId={selectedItem.id}
                    onClose={() => setSelectedId(null)}
                    onReply={() => handleReply(selectedItem.id)}
                    onArchive={() => handleArchive(selectedItem.id)}
                    onDelete={() => handleDelete(selectedItem.id)}
                    onMarkRead={() => handleMarkRead(selectedItem.id, true)}
                    onMarkUnread={() => handleMarkRead(selectedItem.id, false)}
                  />
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="hidden lg:flex flex-1 items-center justify-center"
                >
                  <div
                    data-inbox-empty
                    className="text-center"
                  >
                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-zinc-800/30 border border-zinc-800/50
                                  flex items-center justify-center">
                      <Mail size={24} className="text-zinc-600" />
                    </div>
                    <p className="text-sm text-zinc-500">Select a message</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Agent Preview Overlay */}
            {previews.length > 0 && (
              <div className="absolute inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center">
                <div className="bg-zinc-900 border border-zinc-800/50 rounded-xl p-6 max-w-md">
                  <p className="text-sm text-zinc-400">Agent is composing an email...</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Empty state component
function EmptyState({ searchQuery, filter }: { searchQuery: string; filter: string }) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center py-12">
        <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-zinc-800/30 border border-zinc-800/50 
                      flex items-center justify-center">
          <InboxIcon size={20} className="text-zinc-600" />
        </div>
        <p className="text-sm text-zinc-500 mb-1">
          {searchQuery ? 'No matching messages' : filter !== 'all' ? `No ${filter} messages` : 'Inbox is empty'}
        </p>
        <p className="text-xs text-zinc-600">
          {searchQuery ? 'Try a different search term' : 'Messages will appear here'}
        </p>
      </div>
    </div>
  )
}
