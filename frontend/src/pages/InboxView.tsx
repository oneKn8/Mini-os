import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
    Inbox as InboxIcon, 
    Check, 
    Trash2, 
    MoreHorizontal, 
    Mail, 
    Briefcase, 
    User, 
    DollarSign,
    Filter,
    RefreshCw,
    Search
} from 'lucide-react'
import { clsx } from 'clsx'

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
  const [filter, setFilter] = useState('all')
  const [selectedItem, setSelectedItem] = useState<InboxItem | null>(null)

  useEffect(() => {
    fetchInbox()
  }, [])

  const fetchInbox = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/inbox')
      if (response.ok) {
        const data = await response.json()
        setItems(data.items || [])
      }
    } catch (error) {
      console.error('Failed to fetch inbox:', error)
    } finally {
      setLoading(false)
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "work": return <Briefcase size={16} className="text-accent-secondary" />
      case "personal": return <User size={16} className="text-accent-success" />
      case "finance": return <DollarSign size={16} className="text-accent-warning" />
      default: return <Mail size={16} className="text-text-tertiary" />
    }
  }
  
  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'high': return 'bg-accent-error'
      case 'medium': return 'bg-accent-warning'
      case 'low': return 'bg-accent-success'
      default: return 'bg-text-tertiary'
    }
  }

  const filteredItems = items.filter((item) => {
    if (filter === 'all') return true
    if (filter === 'unread') return !item.read
    return item.category === filter
  })

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  }
  
  const item = {
    hidden: { opacity: 0, x: -10 },
    show: { opacity: 1, x: 0 }
  }

  return (
    <div className="h-full flex flex-col md:flex-row gap-6 pb-20">
       {/* List Column */}
       <div className={clsx(
           "flex-1 flex flex-col min-w-0 h-full",
           selectedItem ? "hidden md:flex" : "flex"
       )}>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-bold text-text-primary">Inbox</h1>
                <button 
                    onClick={fetchInbox}
                    className="p-2 rounded-lg hover:bg-surface text-text-secondary hover:text-accent-primary transition-colors"
                >
                    <RefreshCw size={20} className={clsx(loading && "animate-spin")} />
                </button>
            </div>

            {/* Search & Filters */}
            <div className="space-y-4 mb-6">
                <div className="relative">
                    <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                    <input 
                        type="text" 
                        placeholder="Search messages..."
                        className="w-full rounded-xl border border-border-light bg-surface pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary/20 focus:border-accent-primary transition-all"
                    />
                </div>

                <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
                    {['all', 'unread', "work", "personal", "finance"].map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={clsx(
                                "px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all",
                                filter === f 
                                    ? "bg-accent-primary text-white shadow-md" 
                                    : "bg-surface text-text-secondary hover:bg-bg-secondary border border-border-light"
                            )}
                        >
                            {f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Message List */}
            <div className="flex-1 overflow-y-auto min-h-0 pr-2 space-y-2">
                {loading && filteredItems.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12">
                        <div className="spinner-large text-accent-primary"></div>
                    </div>
                ) : (
                    <motion.div 
                        variants={container}
                        initial="hidden"
                        animate="show"
                        className="space-y-2"
                    >
                        {filteredItems.map((message) => (
                            <motion.div
                                key={message.id}
                                variants={item}
                                layoutId={`message-${message.id}`}
                                onClick={() => setSelectedItem(message)}
                                className={clsx(
                                    "group cursor-pointer rounded-xl p-4 border transition-all",
                                    selectedItem?.id === message.id 
                                        ? "bg-accent-primary/5 border-accent-primary" 
                                        : "bg-surface border-border-light hover:border-accent-primary/30 hover:shadow-sm",
                                    !message.read && "border-l-4 border-l-accent-primary"
                                )}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <div className="flex items-center gap-2">
                                        <div className={clsx("w-2 h-2 rounded-full", getImportanceColor(message.importance))}></div>
                                        <span className={clsx(
                                            "text-sm font-semibold",
                                            !message.read ? "text-text-primary" : "text-text-secondary"
                                        )}>{message.sender}</span>
                                    </div>
                                    <span className="text-xs text-text-tertiary">{message.timestamp}</span>
                                </div>
                                
                                <h3 className={clsx(
                                    "text-sm mb-1",
                                    !message.read ? "font-bold text-text-primary" : "font-medium text-text-secondary"
                                )}>{message.subject}</h3>
                                
                                <p className="text-xs text-text-tertiary line-clamp-2">{message.preview}</p>
                                
                                <div className="flex items-center gap-2 mt-3">
                                    <div className="flex items-center gap-1 text-xs text-text-tertiary px-2 py-1 rounded-md bg-bg-secondary">
                                        {getCategoryIcon(message.category)}
                                        <span className="capitalize">{message.category}</span>
                                    </div>
                                    {message.labels.map(label => (
                                        <span key={label} className="text-[10px] px-2 py-1 rounded-md bg-bg-secondary text-text-tertiary border border-border-light">
                                            {label}
                                        </span>
                                    ))}
                                </div>
                            </motion.div>
                        ))}
                    </motion.div>
                )}
                
                {!loading && filteredItems.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                        <div className="w-16 h-16 rounded-full bg-bg-secondary flex items-center justify-center mb-4">
                            <InboxIcon size={32} className="text-text-muted" />
                        </div>
                        <h3 className="text-lg font-semibold text-text-primary">Inbox Zero</h3>
                        <p className="text-text-secondary">You're all caught up!</p>
                    </div>
                )}
            </div>
       </div>

       {/* Detail View */}
       <AnimatePresence mode="wait">
           {selectedItem ? (
               <motion.div 
                   initial={{ opacity: 0, x: 20 }}
                   animate={{ opacity: 1, x: 0 }}
                   exit={{ opacity: 0, x: 20 }}
                   className="flex-1 bg-surface rounded-2xl border border-border-light shadow-sm flex flex-col h-full overflow-hidden"
               >
                   {/* Toolbar */}
                   <div className="flex items-center justify-between px-6 py-4 border-b border-border-light">
                       <div className="flex items-center gap-2">
                           <button className="p-2 hover:bg-bg-secondary rounded-lg text-text-secondary" title="Archive">
                               <Check size={18} />
                           </button>
                           <button className="p-2 hover:bg-bg-secondary rounded-lg text-text-secondary" title="Delete">
                               <Trash2 size={18} />
                           </button>
                           <button className="p-2 hover:bg-bg-secondary rounded-lg text-text-secondary">
                               <MoreHorizontal size={18} />
                           </button>
                       </div>
                       <button 
                           onClick={() => setSelectedItem(null)}
                           className="md:hidden text-sm font-medium text-accent-primary"
                       >
                           Back to list
                       </button>
                   </div>

                   {/* Content */}
                   <div className="flex-1 overflow-y-auto p-8">
                       <h2 className="text-2xl font-bold text-text-primary mb-4">{selectedItem.subject}</h2>
                       
                       <div className="flex items-start justify-between mb-8 pb-8 border-b border-border-light">
                           <div className="flex items-center gap-4">
                               <div className="w-10 h-10 rounded-full bg-accent-primary/10 flex items-center justify-center text-accent-primary font-bold text-lg">
                                   {selectedItem.sender[0]}
                               </div>
                               <div>
                                   <div className="font-semibold text-text-primary">{selectedItem.sender}</div>
                                   <div className="text-xs text-text-tertiary">To: Me</div>
                               </div>
                           </div>
                           <div className="text-sm text-text-tertiary">{selectedItem.timestamp}</div>
                       </div>

                       <div className="prose prose-sm max-w-none text-text-secondary leading-relaxed">
                           <p>{selectedItem.preview}</p>
                           <p className="mt-4">
                               Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                           </p>
                           <p className="mt-4">
                               Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
                           </p>
                       </div>
                   </div>
               </motion.div>
           ) : (
               <div className="hidden md:flex flex-1 items-center justify-center bg-bg-secondary/50 rounded-2xl border border-dashed border-border-dark/20">
                   <div className="text-center text-text-muted">
                       <Mail size={48} className="mx-auto mb-4 opacity-20" />
                       <p>Select a message to read</p>
                   </div>
               </div>
           )}
       </AnimatePresence>
    </div>
  )
}
