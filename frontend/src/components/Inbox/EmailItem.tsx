import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { InboxItem } from '../../api/inbox'
import { Briefcase, User, DollarSign, Mail } from 'lucide-react'
import { clsx } from 'clsx'
import { hoverScale } from '../../utils/gsap'

interface EmailItemProps {
  item: InboxItem
  isSelected: boolean
  onClick: () => void
}

const CategoryIcon = ({ category }: { category: string }) => {
  switch (category) {
    case "work": return <Briefcase size={14} className="text-accent-secondary" />
    case "personal": return <User size={14} className="text-accent-success" />
    case "finance": return <DollarSign size={14} className="text-accent-warning" />
    default: return <Mail size={14} className="text-text-tertiary" />
  }
}

const ImportanceDot = ({ level }: { level: string }) => {
  const color = {
    high: 'bg-accent-error',
    medium: 'bg-accent-warning',
    low: 'bg-accent-success'
  }[level] || 'bg-text-tertiary'
  return <div className={`w-2 h-2 rounded-full ${color} shadow-[0_0_8px_rgba(0,0,0,0.5)]`} />
}

export default function EmailItem({ item, isSelected, onClick }: EmailItemProps) {
  const itemRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (itemRef.current) {
      const cleanup = hoverScale(itemRef.current, 1.02, 0.2)
      return cleanup
    }
  }, [])

  return (
    <motion.div
      ref={itemRef}
      data-email-item
      layoutId={`email-${item.id}`}
      onClick={onClick}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      whileHover={{ scale: 1.02, x: 4 }}
      className={clsx(
        "group cursor-pointer relative p-4 rounded-xl border transition-all duration-300",
        isSelected 
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
          {new Date(item.received_at).toLocaleDateString()}
        </span>
      </div>
      <h3 className={clsx("text-sm mb-1 line-clamp-1", !item.read ? "font-bold text-text-primary" : "font-medium text-text-secondary")}>
        {item.title}
      </h3>
      <p className="text-xs text-text-tertiary line-clamp-2 mb-3">{item.body_preview}</p>
      
      <div className="flex gap-2">
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-black/20 border border-white/5 text-[10px] text-text-secondary capitalize">
          <CategoryIcon category={item.category} />
          {item.category}
        </span>
      </div>
    </motion.div>
  )
}

