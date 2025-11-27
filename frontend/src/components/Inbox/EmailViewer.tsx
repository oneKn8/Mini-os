import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Reply, Archive, Trash2, X } from 'lucide-react'
import { InboxItem } from '../../api/inbox'
import { useInboxItem } from '../../api/inbox'
import GlassCard from '../UI/GlassCard'
import { animateOnMount } from '../../utils/gsap'

interface EmailViewerProps {
  itemId: string | null
  onClose: () => void
  onReply?: () => void
  onArchive?: () => void
  onDelete?: () => void
}

export default function EmailViewer({ itemId, onClose, onReply, onArchive, onDelete }: EmailViewerProps) {
  const { data: item, isLoading } = useInboxItem(itemId || '')
  const viewerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (viewerRef.current && item) {
      animateOnMount(viewerRef.current, {
        opacity: 0,
        scale: 0.95,
        filter: 'blur(10px)',
        duration: 0.4,
      })
    }
  }, [item])

  if (!itemId || isLoading) {
    return (
      <div className="hidden lg:flex flex-[2] h-full items-center justify-center opacity-20">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-white/20 border-t-white rounded-full mx-auto mb-4"></div>
          <p className="text-xl font-light">Loading...</p>
        </div>
      </div>
    )
  }

  if (!item) {
    return null
  }

  return (
    <motion.div
      ref={viewerRef}
      key={item.id}
      initial={{ opacity: 0, scale: 0.95, filter: 'blur(10px)' }}
      animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
      exit={{ opacity: 0, scale: 0.95, filter: 'blur(10px)' }}
      className="flex-[2] h-full"
    >
      <GlassCard className="h-full flex flex-col" variant="dark">
        {/* Toolbar */}
        <div className="p-4 border-b border-white/5 flex justify-between items-center">
          <button onClick={onClose} className="lg:hidden text-sm text-text-secondary hover:text-white">
            ← Back
          </button>
          <div className="flex gap-2 ml-auto">
            <button 
              onClick={onReply}
              className="p-2 hover:bg-white/10 rounded-lg text-text-secondary transition-colors" 
              title="Reply"
            >
              <Reply size={18} />
            </button>
            <button 
              onClick={onArchive}
              className="p-2 hover:bg-white/10 rounded-lg text-text-secondary transition-colors" 
              title="Archive"
            >
              <Archive size={18} />
            </button>
            <button 
              onClick={onDelete}
              className="p-2 hover:bg-red-500/20 hover:text-red-400 rounded-lg text-text-secondary transition-colors" 
              title="Delete"
            >
              <Trash2 size={18} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-8 overflow-y-auto flex-1">
          <h2 className="text-2xl font-bold text-white mb-6">{item.title}</h2>
          
          <div className="flex items-center gap-4 mb-8 pb-8 border-b border-white/5">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center text-white text-lg font-bold shadow-lg">
              {item.sender?.[0] || '?'}
            </div>
            <div>
              <div className="font-semibold text-white text-lg">{item.sender}</div>
              <div className="text-xs text-text-tertiary">
                To: Me • {new Date(item.received_at).toLocaleString()}
              </div>
            </div>
          </div>

          <div className="prose prose-invert max-w-none text-text-secondary">
            <p>{item.body_preview}</p>
            {(item as any).body_full && (
              <div 
                className="mt-4"
                dangerouslySetInnerHTML={{ __html: (item as any).body_full }}
              />
            )}
          </div>
        </div>
      </GlassCard>
    </motion.div>
  )
}

