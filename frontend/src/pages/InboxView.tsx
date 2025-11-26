import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Inbox as InboxIcon, 
  Search, 
  RefreshCw, 
  Mail, 
  DollarSign, 
  User, 
  Briefcase,
  Trash2,
  Archive,
  Reply
} from 'lucide-react'
import { clsx } from 'clsx'
import GlassCard from '../components/UI/GlassCard'

interface InboxItem {
  id: string
  subject: string
  sender: string
  preview: string
  timestamp: string
  category: string
  importance: 'high' | 'medium' | 'low'
  read: boolean
  labels: string[]
}

export default function InboxView() {
  const [items, setItems] = useState<InboxItem[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [filter, setFilter] = useState('all')
  const [syncMessage, setSyncMessage] = useState<string | null>(null)

  useEffect(() => {
    fetchInbox()
  }, [])

  const fetchInbox = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/inbox')
      if (response.ok) {
        const data = await response.json()
        const inboxItems = Array.isArray(data) ? data : (data.items || [])
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const mappedItems = inboxItems.map((item: any) => ({
          id: item.id,
          subject: item.title || '',
          sender: item.sender || '',
          preview: item.body_preview || '',
          timestamp: item.received_at || '',
          category: item.category || 'other',
          importance: item.importance || 'medium',
          read: false,
          labels: item.labels || []
        }))
        setItems(mappedItems)
      }
    } catch (error) {
      console.error('Failed to fetch inbox:', error)
    } finally {
      setLoading(false)
    }
  }

  const refreshInbox = async () => {
    setSyncing(true)
    setSyncMessage(null)
    try {
      // First, trigger sync from external providers
      const syncResponse = await fetch('/api/sync/refresh-inbox', { method: 'POST' })
      const syncData = await syncResponse.json()
      
      if (syncData.status === 'no_accounts') {
        setSyncMessage(syncData.message)
      } else if (syncData.synced_items > 0) {
        setSyncMessage(`Synced ${syncData.synced_items} new items`)
      } else {
        setSyncMessage('Already up to date')
      }
      
      // Then fetch the updated inbox
      await fetchInbox()
      
      // Clear message after 3 seconds
      setTimeout(() => setSyncMessage(null), 3000)
    } catch (error) {
      console.error('Failed to refresh inbox:', error)
      setSyncMessage('Sync failed. Please try again.')
      setTimeout(() => setSyncMessage(null), 3000)
    } finally {
      setSyncing(false)
    }
  }

  // Category Icons
  const CategoryIcon = ({ category }: { category: string }) => {
    switch (category) {
      case "work": return <Briefcase size={14} className="text-accent-secondary" />
      case "personal": return <User size={14} className="text-accent-success" />
      case "finance": return <DollarSign size={14} className="text-accent-warning" />
      default: return <Mail size={14} className="text-text-tertiary" />
    }
  }

  // Importance Indicator
  const ImportanceDot = ({ level }: { level: string }) => {
    const color = {
      high: 'bg-accent-error',
      medium: 'bg-accent-warning',
      low: 'bg-accent-success'
    }[level] || 'bg-text-tertiary'
    return <div className={`w-2 h-2 rounded-full ${color} shadow-[0_0_8px_rgba(0,0,0,0.5)]`} />
  }

  const filteredItems = items.filter(item => filter === 'all' || item.category === filter)
  const selectedItem = items.find(i => i.id === selectedId)

  return (
    <div className="h-full flex flex-col gap-6 pb-20">
      
      {/* Header & Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
           <h1 className="text-3xl font-bold text-text-primary text-glow">Inbox</h1>
           <span className="bg-surface px-2 py-0.5 rounded-full text-xs text-text-secondary border border-border-light">
             {items.length}
           </span>
           {syncMessage && (
             <span className="text-xs text-accent-primary animate-pulse">
               {syncMessage}
             </span>
           )}
        </div>
        <div className="flex gap-2">
           <button 
             onClick={refreshInbox} 
             disabled={syncing}
             className="p-2 rounded-lg bg-surface hover:bg-surface-hover border border-border-light transition-colors disabled:opacity-50"
             title="Sync from Gmail/Outlook"
           >
             <RefreshCw size={18} className={clsx((syncing || loading) && "animate-spin")} />
           </button>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <GlassCard className="p-2 flex gap-2 items-center" noBorder>
         <div className="relative flex-1">
           <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
           <input 
             type="text" 
             placeholder="Search messages..." 
             className="w-full bg-black/20 border border-white/5 rounded-xl pl-10 pr-4 py-2.5 text-sm text-text-primary focus:outline-none focus:border-accent-primary/50 transition-colors placeholder-text-muted"
           />
         </div>
         <div className="h-8 w-[1px] bg-white/10 mx-1" />
         {['all', 'work', 'personal', 'finance'].map(f => (
           <button 
             key={f}
             onClick={() => setFilter(f)}
             className={clsx(
               "px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all",
               filter === f ? "bg-accent-primary text-white shadow-lg shadow-accent-primary/20" : "text-text-secondary hover:bg-white/5"
             )}
           >
             {f}
           </button>
         ))}
      </GlassCard>

      {/* Main Content Area: Split View */}
      <div className="flex-1 flex gap-6 min-h-0">
        
        {/* Message List (Stack) */}
        <div className={clsx(
          "flex-1 flex flex-col gap-3 overflow-y-auto pr-2 no-scrollbar transition-all duration-300",
          selectedId ? "hidden lg:flex lg:w-1/3 lg:flex-none" : "w-full"
        )}>
          {loading && items.length === 0 ? (
            <div className="text-center py-20 text-text-tertiary animate-pulse">Loading inbox...</div>
          ) : (
            filteredItems.map((item) => (
              <motion.div
                key={item.id}
                layoutId={`card-${item.id}`}
                onClick={() => setSelectedId(item.id)}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                whileHover={{ scale: 1.02, x: 4 }}
                className={clsx(
                  "group cursor-pointer relative p-4 rounded-xl border transition-all duration-300",
                  selectedId === item.id 
                    ? "bg-accent-primary/10 border-accent-primary shadow-[0_0_15px_rgba(76,110,245,0.15)]" 
                    : "bg-surface/40 border-border-light hover:bg-surface/60 hover:border-border-medium"
                )}
              >
                 <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                       <ImportanceDot level={item.importance} />
                       <span className={clsx("text-sm font-semibold", !item.read ? "text-text-primary" : "text-text-secondary")}>
                         {item.sender}
                       </span>
                    </div>
                    <span className="text-[10px] text-text-tertiary">
                      {new Date(item.timestamp).toLocaleDateString()}
                    </span>
                 </div>
                 <h3 className={clsx("text-sm mb-1 line-clamp-1", !item.read ? "font-bold text-text-primary" : "font-medium text-text-secondary")}>
                   {item.subject}
                 </h3>
                 <p className="text-xs text-text-tertiary line-clamp-2 mb-3">{item.preview}</p>
                 
                 <div className="flex gap-2">
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-black/20 border border-white/5 text-[10px] text-text-secondary capitalize">
                      <CategoryIcon category={item.category} />
                      {item.category}
                    </span>
                 </div>
              </motion.div>
            ))
          )}
        </div>

        {/* Reading Pane (Glass Overlay) */}
        <AnimatePresence mode="wait">
           {selectedItem ? (
             <motion.div 
               key={selectedItem.id}
               initial={{ opacity: 0, scale: 0.95, filter: 'blur(10px)' }}
               animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
               exit={{ opacity: 0, scale: 0.95, filter: 'blur(10px)' }}
               className="flex-[2] h-full"
             >
               <GlassCard className="h-full flex flex-col" variant="dark">
                 {/* Toolbar */}
                 <div className="p-4 border-b border-white/5 flex justify-between items-center">
                    <button onClick={() => setSelectedId(null)} className="lg:hidden text-sm text-text-secondary hover:text-white">
                      ← Back
                    </button>
                    <div className="flex gap-2 ml-auto">
                       <button className="p-2 hover:bg-white/10 rounded-lg text-text-secondary transition-colors" title="Reply">
                         <Reply size={18} />
                       </button>
                       <button className="p-2 hover:bg-white/10 rounded-lg text-text-secondary transition-colors" title="Archive">
                         <Archive size={18} />
                       </button>
                       <button className="p-2 hover:bg-red-500/20 hover:text-red-400 rounded-lg text-text-secondary transition-colors" title="Delete">
                         <Trash2 size={18} />
                       </button>
                    </div>
                 </div>

                 {/* Content */}
                 <div className="p-8 overflow-y-auto flex-1">
                    <h2 className="text-2xl font-bold text-white mb-6">{selectedItem.subject}</h2>
                    
                    <div className="flex items-center gap-4 mb-8 pb-8 border-b border-white/5">
                       <div className="w-12 h-12 rounded-full bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center text-white text-lg font-bold shadow-lg">
                         {selectedItem.sender[0]}
                       </div>
                       <div>
                         <div className="font-semibold text-white text-lg">{selectedItem.sender}</div>
                         <div className="text-xs text-text-tertiary">To: Me • {new Date(selectedItem.timestamp).toLocaleString()}</div>
                       </div>
                    </div>

                    <div className="prose prose-invert max-w-none text-text-secondary">
                      <p>{selectedItem.preview}</p>
                      <p className="mt-4">
                         This is a placeholder for the full email body. In a real implementation, 
                         this would render the HTML content of the email securely.
                      </p>
                      <p>
                         Beast mode UI requires high contrast reading environments, so we ensure 
                         typography is legible against the dark glass background.
                      </p>
                    </div>
                 </div>
               </GlassCard>
             </motion.div>
           ) : (
             <div className="hidden lg:flex flex-[2] h-full items-center justify-center opacity-20">
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
