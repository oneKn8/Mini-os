import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Inbox as InboxIcon, RefreshCw } from 'lucide-react'
import { clsx } from 'clsx'
import { useInboxWithRealtime } from '../hooks/useInbox'
import EmailList from '../components/Inbox/EmailList'
import EmailViewer from '../components/Inbox/EmailViewer'
import EmailFilters from '../components/Inbox/EmailFilters'
import { animateOnMount } from '../utils/gsap'
import { useRef, useEffect } from 'react'

export default function InboxView() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [filter, setFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const headerRef = useRef<HTMLDivElement>(null)

  // Use real-time inbox hook
  const { items, isLoading, refresh, isRefreshing } = useInboxWithRealtime(filter === 'all' ? undefined : filter)

  // Animate header on mount
  useEffect(() => {
    if (headerRef.current) {
      animateOnMount(headerRef.current, {
        opacity: 0,
        y: -20,
        duration: 0.5,
      })
    }
  }, [])

  // Filter and search items
  const filteredItems = useMemo(() => {
    let result = items

    // Apply category filter (already handled by API, but keep for client-side filtering if needed)
    if (filter !== 'all') {
      result = result.filter(item => item.category === filter)
    }

    // Apply search query
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
    <div className="h-full flex flex-col gap-6 pb-20">
      {/* Header & Controls */}
      <div ref={headerRef} className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-text-primary text-glow">Inbox</h1>
          <span className="bg-surface px-2 py-0.5 rounded-full text-xs text-text-secondary border border-border-light">
            {items.length}
          </span>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => refresh()} 
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-surface hover:bg-surface-hover border border-border-light transition-colors disabled:opacity-50"
            title="Sync from Gmail/Outlook"
          >
            <RefreshCw size={18} className={clsx((isRefreshing || isLoading) && "animate-spin")} />
          </button>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <EmailFilters
        filter={filter}
        onFilterChange={setFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      {/* Main Content Area: Split View */}
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Message List */}
        <div className={clsx(
          "flex-1 flex flex-col gap-3 overflow-y-auto pr-2 no-scrollbar transition-all duration-300",
          selectedId ? "hidden lg:flex lg:w-1/3 lg:flex-none" : "w-full"
        )}>
          {isLoading && filteredItems.length === 0 ? (
            <div className="text-center py-20 text-text-tertiary animate-pulse">Loading inbox...</div>
          ) : filteredItems.length === 0 ? (
            <div className="text-center py-20 text-text-tertiary">
              <InboxIcon size={48} className="mx-auto mb-4 opacity-20" />
              <p>No messages found</p>
            </div>
          ) : (
            <EmailList
              items={filteredItems}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          )}
        </div>

        {/* Reading Pane */}
        <AnimatePresence mode="wait">
          {selectedItem ? (
            <EmailViewer
              key={selectedItem.id}
              itemId={selectedItem.id}
              onClose={() => setSelectedId(null)}
              onReply={() => {
                // TODO: Implement reply
                console.log('Reply to', selectedItem.id)
              }}
              onArchive={() => {
                // TODO: Implement archive
                console.log('Archive', selectedItem.id)
              }}
              onDelete={() => {
                // TODO: Implement delete
                console.log('Delete', selectedItem.id)
              }}
            />
          ) : (
            <div key="empty" className="hidden lg:flex flex-[2] h-full items-center justify-center opacity-20">
              <div className="text-center">
                <InboxIcon size={64} className="mx-auto mb-4" />
                <p className="text-xl font-light">Select a message</p>
              </div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
