import { InboxItem } from '../../api/inbox'
import { clsx } from 'clsx'

interface EmailItemProps {
  item: InboxItem
  isSelected: boolean
  onClick: () => void
}

// Importance indicator - subtle dots
const ImportanceDot = ({ level }: { level: string }) => {
  const colors: Record<string, string> = {
    critical: 'bg-red-400',
    high: 'bg-amber-400',
    medium: 'bg-blue-400',
    low: 'bg-zinc-500',
    ignore: 'bg-zinc-700',
  }
  return <div className={clsx("w-1.5 h-1.5 rounded-full flex-shrink-0", colors[level] || 'bg-zinc-600')} />
}

// Category colors
const categoryColors: Record<string, string> = {
  work: 'text-blue-400',
  personal: 'text-violet-400',
  finance: 'text-emerald-400',
}

// Format relative time
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
  if (diff < 604800000) return date.toLocaleDateString('en-US', { weekday: 'short' })
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function EmailItem({ item, isSelected, onClick }: EmailItemProps) {
  const isUnread = !item.read

  return (
    <div
      data-email-item={item.id}
      onClick={onClick}
      className={clsx(
        "group cursor-pointer p-3 rounded-lg border transition-all duration-200",
        isSelected
          ? "bg-zinc-800/50 border-zinc-700"
          : "bg-zinc-900/30 border-zinc-800/30 hover:bg-zinc-800/30 hover:border-zinc-800"
      )}
    >
      {/* Top row: sender + time */}
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-2 min-w-0">
          <ImportanceDot level={item.importance} />
          <span className={clsx(
            "text-sm truncate",
            isUnread ? "font-medium text-zinc-200" : "text-zinc-400"
          )}>
            {item.sender || 'Unknown'}
          </span>
          {isUnread && (
            <div className="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
          )}
        </div>
        <span className="text-[10px] text-zinc-600 flex-shrink-0">
          {formatTime(item.received_at)}
        </span>
      </div>

      {/* Subject */}
      <h3 className={clsx(
        "text-sm mb-1 truncate",
        isUnread ? "text-zinc-200" : "text-zinc-400"
      )}>
        {item.title}
      </h3>

      {/* Preview */}
      <p className="text-xs text-zinc-600 line-clamp-2 mb-2">
        {item.body_preview}
      </p>

      {/* Category tag */}
      <div className="flex items-center gap-2">
        <span className={clsx(
          "text-[10px] capitalize",
          categoryColors[item.category] || 'text-zinc-500'
        )}>
          {item.category}
        </span>
        {item.suggested_action && (
          <span className="text-[10px] text-amber-500/70 truncate">
            • {item.suggested_action}
          </span>
        )}
      </div>
    </div>
  )
}
