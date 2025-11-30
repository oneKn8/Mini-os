import { InboxItem } from '../../api/inbox'
import { clsx } from 'clsx'

interface EmailItemProps {
  item: InboxItem
  isSelected: boolean
  onClick: () => void
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
  const messageCount = item.message_count || 1
  const folder = item.folder || 'inbox'
  const gmailCategory = item.gmail_category || 'primary'

  const chipLabel =
    folder && folder !== 'inbox'
      ? folder === 'spam'
        ? 'Spam'
        : folder === 'trash'
          ? 'Trash'
          : folder === 'sent'
            ? 'Sent'
            : folder === 'drafts'
              ? 'Draft'
              : folder.charAt(0).toUpperCase() + folder.slice(1)
      : gmailCategory && gmailCategory !== 'primary'
        ? gmailCategory.charAt(0).toUpperCase() + gmailCategory.slice(1)
        : null

  const chipClass =
    folder === 'spam'
      ? 'bg-red-500/15 text-red-300 border-red-500/30'
      : folder === 'trash'
        ? 'bg-zinc-800/60 text-zinc-300 border-zinc-700'
        : folder === 'sent'
          ? 'bg-zinc-700/60 text-zinc-200 border-zinc-600'
          : gmailCategory === 'promotions'
            ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
            : gmailCategory === 'social'
              ? 'bg-violet-500/15 text-violet-300 border-violet-500/30'
              : gmailCategory === 'updates'
                ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                : gmailCategory === 'forums'
                  ? 'bg-sky-500/15 text-sky-300 border-sky-500/30'
                  : 'bg-zinc-800/60 text-zinc-300 border-zinc-700'

  return (
    <div
      data-email-item={item.id}
      onClick={onClick}
      className={clsx(
        "group cursor-pointer px-4 py-2.5 border-b border-zinc-800/50 transition-all duration-150",
        isSelected
          ? "bg-blue-500/10 border-l-2 border-l-blue-500"
          : "hover:bg-zinc-800/30 border-l-2 border-l-transparent",
        isUnread && !isSelected && "bg-zinc-900/60"
      )}
    >
      {/* Single row: unread dot + sender + chips + count + time */}
      <div className="flex items-center gap-2 mb-0.5">
        {/* Unread indicator */}
        {isUnread && (
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500 flex-shrink-0" />
        )}

        {/* Sender - Gmail style bold for unread */}
        <span className={clsx(
          "text-sm truncate min-w-[120px] max-w-[200px]",
          isUnread ? "font-bold text-zinc-100" : "font-normal text-zinc-500"
        )}>
          {item.sender || 'Unknown'}
        </span>

        {/* Subject - Gmail style bold for unread */}
        <h3 className={clsx(
          "text-sm truncate flex-1 min-w-0",
          isUnread ? "font-bold text-zinc-100" : "font-normal text-zinc-400"
        )}>
          {item.title}
        </h3>

        {/* Message count for threads */}
        {messageCount > 1 && (
          <span className={clsx(
            "text-[11px] px-1.5 py-0.5 rounded-md flex-shrink-0",
            isUnread
              ? "bg-zinc-700/80 text-zinc-200 font-semibold border border-zinc-600"
              : "bg-zinc-800/60 text-zinc-400 border border-zinc-700"
          )}>
            ({messageCount})
          </span>
        )}

        {/* Category/folder chip - more subtle */}
        {chipLabel && (
          <span
            className={clsx(
              "inline-flex items-center px-1.5 py-0.5 rounded-md border text-[10px] font-medium flex-shrink-0",
              chipClass
            )}
          >
            {chipLabel}
          </span>
        )}

        {/* Time - more compact */}
        <span className={clsx(
          "text-xs flex-shrink-0 min-w-[45px] text-right",
          isUnread ? "text-zinc-400 font-medium" : "text-zinc-500"
        )}>
          {formatTime(item.received_at)}
        </span>
      </div>

      {/* Preview - more subtle, Gmail style */}
      <p className={clsx(
        "text-xs line-clamp-1 pl-5",
        isUnread ? "text-zinc-400" : "text-zinc-600"
      )}>
        {item.body_preview}
      </p>
    </div>
  )
}
