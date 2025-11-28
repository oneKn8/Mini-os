import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mail, RefreshCw, Search, Inbox as InboxIcon } from 'lucide-react'
import { clsx } from 'clsx'
import { useInboxWithRealtime } from '../hooks/useInbox'
import EmailList from '../components/Inbox/EmailList'
import EmailViewer from '../components/Inbox/EmailViewer'
import { useScreenUpdates } from '../store/screenController'

// Category filters with subtle colors
const CATEGORIES = [
  { id: 'all', label: 'All', color: 'bg-zinc-600' },
  { id: 'work', label: 'Work', color: 'bg-blue-500/60' },
  { id: 'personal', label: 'Personal', color: 'bg-violet-500/60' },
  { id: 'finance', label: 'Finance', color: 'bg-emerald-500/60' },
]

export default function InboxView() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [filter, setFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Real-time inbox + agent previews
  const { items, isLoading, refresh, isRefreshing } = useInboxWithRealtime(filter === 'all' ? undefined : filter)
  const { previews, isAgentFocused } = useScreenUpdates('/inbox')

  // Filter and search
  const filteredItems = useMemo(() => {
    let result = items

    if (filter !== 'all') {
      result = result.filter(item => item.category === filter)
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(item =>
        item.title.toLowerCase().includes(query) ||
        item.sender?.toLowerCase().includes(query) ||
        item.body_preview.toLowerCase().includes(query)
      )
    }

    return result
  }, [items, filter, searchQuery])

  const selectedItem = items.find(i => i.id === selectedId)

  return (
    <div className="h-full flex flex-col gap-4 pb-16" data-inbox-page>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-medium text-zinc-200">Inbox</h1>
          <span className="px-2 py-0.5 rounded-full text-xs text-zinc-500 bg-zinc-800/50 border border-zinc-800/50">
            {items.length}
          </span>
        </div>
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

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
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

        {/* Category Pills */}
        <div className="flex gap-1">
          {CATEGORIES.map(cat => (
            <button
              key={cat.id}
              onClick={() => setFilter(cat.id)}
              className={clsx(
                "px-3 py-1.5 rounded-lg text-xs font-medium transition-all border",
                filter === cat.id
                  ? "bg-zinc-800 border-zinc-700 text-zinc-200"
                  : "bg-transparent border-zinc-800/50 text-zinc-500 hover:text-zinc-400 hover:bg-zinc-800/30"
              )}
            >
              <span className={clsx("inline-block w-1.5 h-1.5 rounded-full mr-1.5", cat.color)} />
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Email List */}
        <div
          data-email-list
          className={clsx(
            "flex flex-col gap-1 overflow-y-auto scrollbar-thin pr-1 transition-all duration-300",
            selectedId ? "hidden lg:flex lg:w-80 lg:flex-shrink-0" : "w-full"
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
              className="flex-1 min-w-0"
            >
              <EmailViewer
                itemId={selectedItem.id}
                onClose={() => setSelectedId(null)}
                onReply={() => console.log('Reply to', selectedItem.id)}
                onArchive={() => console.log('Archive', selectedItem.id)}
                onDelete={() => console.log('Delete', selectedItem.id)}
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
