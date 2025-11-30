import { useEffect, useMemo, useState } from 'react'
import { clsx } from 'clsx'
import { Reply, Archive, Trash2, MailCheck, MailX, ExternalLink } from 'lucide-react'
import { useInboxItem } from '../../api/inbox'

interface EmailViewerProps {
  itemId: string | null
  onClose: () => void
  onReply?: () => void
  onArchive?: () => void
  onDelete?: () => void
  onMarkRead?: () => void
  onMarkUnread?: () => void
}

// Clean up email body - properly extract text from HTML
function cleanEmailBody(text: string): string {
  if (!text) return ''

  let cleaned = text

  // Check if it's HTML content
  if (text.trim().startsWith('<')) {
    try {
      // Create a temporary DOM element to parse HTML
      const tempDiv = document.createElement('div')
      tempDiv.innerHTML = text

      // Remove script and style elements
      const scripts = tempDiv.getElementsByTagName('script')
      const styles = tempDiv.getElementsByTagName('style')
      Array.from(scripts).forEach(s => s.remove())
      Array.from(styles).forEach(s => s.remove())

      // Convert certain HTML elements to readable text
      // Add line breaks for block elements
      const blockElements = tempDiv.querySelectorAll('p, div, br, h1, h2, h3, h4, h5, h6, li')
      blockElements.forEach(el => {
        if (el.tagName === 'BR') {
          el.replaceWith('\n')
        } else {
          // Add newlines around block elements
          const textNode = document.createTextNode('\n')
          el.parentNode?.insertBefore(textNode, el.nextSibling)
        }
      })

      // Handle links - keep them as [text](url) or just text if url is too long
      const links = tempDiv.getElementsByTagName('a')
      Array.from(links).forEach(link => {
        const href = link.getAttribute('href') || ''
        const linkText = link.textContent || ''

        if (href && href.length < 50 && linkText && linkText !== href) {
          link.textContent = `${linkText} (${href})`
        } else if (linkText) {
          link.textContent = linkText
        }
      })

      // Get the clean text content
      cleaned = tempDiv.textContent || tempDiv.innerText || ''

      // Clean up excessive whitespace
      cleaned = cleaned
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .join('\n')

    } catch (e) {
      // If DOM parsing fails, fall back to basic cleaning
      console.error('Failed to parse email HTML:', e)
      cleaned = text.replace(/<[^>]+>/g, ' ')
    }
  }

  // Remove excessively long URLs (tracking links)
  cleaned = cleaned.replace(/https?:\/\/[^\s]{100,}/g, '[link]')

  // Remove excessive blank lines
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n')

  return cleaned.trim()
}

// Light HTML sanitizer to render emails safely
function sanitizeEmailHtml(html: string): string {
  if (!html) return ''
  try {
    if (typeof DOMParser === 'undefined') {
      return html
    }

    const parser = new DOMParser()
    const doc = parser.parseFromString(html, 'text/html')
    if (!doc.body) return html

    // Remove dangerous nodes
    doc.querySelectorAll('script,style,noscript,link,meta,iframe').forEach(node => node.remove())

    const allowedTags = new Set([
      'body',
      'a','p','div','span','strong','em','b','i','u','br','ul','ol','li','blockquote','center',
      'h1','h2','h3','h4','h5','h6','table','thead','tbody','tfoot','tr','th','td','hr','img',
      'code','pre','section','article','header','footer','figure','figcaption','col','colgroup'
    ])
    const allowedAttrs: Record<string, string[]> = {
      a: ['href','title','target','rel','style'],
      img: ['src','srcset','alt','title','width','height','loading','referrerpolicy','style'],
      default: ['style','align','valign','width','height','bgcolor','border','cellpadding','cellspacing']
    }

    const cleanNode = (node: Element) => {
      const tag = node.tagName.toLowerCase()

      if (tag === 'body') {
        // Never strip the body element itself; just clean its children
        Array.from(node.children).forEach(child => cleanNode(child as Element))
        return
      }

      Array.from(node.children).forEach(child => cleanNode(child as Element))
      if (!allowedTags.has(tag)) {
        // unwrap unknown tags but keep their children
        const parent = node.parentNode
        if (parent) {
          while (node.firstChild) parent.insertBefore(node.firstChild, node)
          parent.removeChild(node)
        }
        return
      }

      // Strip unsafe attributes
      Array.from(node.attributes).forEach(attr => {
        const name = attr.name.toLowerCase()
        if (name.startsWith('on')) {
          node.removeAttribute(attr.name)
          return
        }
        const allowed = [...(allowedAttrs[tag] || []), ...(allowedAttrs.default || [])]
        if (!allowed.includes(name)) {
          node.removeAttribute(attr.name)
          return
        }
        if (name === 'style') {
          const value = attr.value || ''
          // Drop obviously dangerous patterns
          if (/expression\s*\(|javascript:|data:text\/html/i.test(value)) {
            node.removeAttribute(attr.name)
          }
        }
      })

      if (tag === 'a') {
        const href = node.getAttribute('href') || ''
        if (!href.match(/^(https?:|mailto:|tel:)/i)) {
          node.removeAttribute('href')
        } else {
          node.setAttribute('target', '_blank')
          node.setAttribute('rel', 'noopener noreferrer')
        }
      }

      if (tag === 'img') {
        const src = node.getAttribute('src') || ''
        if (!src.match(/^(https?:|data:image\/)/i)) {
          node.removeAttribute('src')
        }
        node.setAttribute('loading', 'lazy')
        node.setAttribute('referrerpolicy', 'no-referrer')
      }
    }

    if (doc.body) {
      cleanNode(doc.body)
      return doc.body.innerHTML || html
    }

    return html
  } catch (e) {
    console.error('Failed to sanitize email HTML:', e)
    return html
  }
}

export default function EmailViewer({
  itemId,
  onClose,
  onReply,
  onArchive,
  onDelete,
  onMarkRead,
  onMarkUnread
}: EmailViewerProps) {
  const { data: item, isLoading } = useInboxItem(itemId || '')
  const [viewMode, setViewMode] = useState<'html' | 'text'>('html')

  const rawBody = (item?.body_full || item?.body_preview || '').toString()
  const hasHtml = useMemo(() => /<[^>]+>/.test(rawBody.trim()), [rawBody])
  const sanitizedHtml = useMemo(() => (hasHtml ? sanitizeEmailHtml(rawBody) : ''), [rawBody, hasHtml])
  const plainBody = useMemo(() => cleanEmailBody(rawBody), [rawBody])

  useEffect(() => {
    setViewMode(hasHtml ? 'html' : 'text')
  }, [hasHtml, item?.id])

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

  const folder = (item as any).folder || 'inbox'
  const gmailCategory = (item as any).gmail_category || 'primary'
  const gmailLabels = ((item as any).gmail_labels || []) as string[]
  const gmail = (item as any).gmail as { message_id?: string; thread_id?: string } | undefined
  const calendar = (item as any).calendar as any

  const folderLabel =
    folder === 'spam'
      ? 'Spam'
      : folder === 'trash'
        ? 'Trash'
        : folder === 'sent'
          ? 'Sent'
          : folder === 'drafts'
            ? 'Drafts'
            : 'Inbox'

  const folderChipClass =
    folder === 'spam'
      ? 'bg-red-500/15 text-red-300 border-red-500/30'
      : folder === 'trash'
        ? 'bg-zinc-800/60 text-zinc-300 border-zinc-700'
        : folder === 'sent'
          ? 'bg-zinc-700/60 text-zinc-200 border-zinc-600'
          : 'bg-zinc-800/60 text-zinc-300 border-zinc-700'

  const categoryLabel =
    gmailCategory === 'primary'
      ? null
      : gmailCategory.charAt(0).toUpperCase() + gmailCategory.slice(1)

  const categoryChipClass =
    gmailCategory === 'promotions'
      ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
      : gmailCategory === 'social'
        ? 'bg-violet-500/15 text-violet-300 border-violet-500/30'
        : gmailCategory === 'updates'
          ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
          : gmailCategory === 'forums'
            ? 'bg-sky-500/15 text-sky-300 border-sky-500/30'
            : 'bg-zinc-800/60 text-zinc-300 border-zinc-700'

  const handleOpenInGmail = () => {
    const messageId = gmail?.message_id
    if (!messageId) return
    const url = `https://mail.google.com/mail/u/0/#all/${encodeURIComponent(messageId)}`
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="flex flex-col h-full bg-zinc-900/50 border border-zinc-800/50 rounded-xl overflow-hidden">
      {/* Sticky Header Container */}
      <div className="flex-shrink-0 sticky top-0 z-10 bg-zinc-900/50 backdrop-blur-sm">
        {/* Header with actions */}
        <div className="px-4 py-3 border-b border-zinc-800/50 bg-zinc-900/30 flex items-center justify-between">
          <button
            onClick={onClose}
            className="lg:hidden text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            ← Back
          </button>
          <div className="flex items-center gap-2 ml-auto">
            <div className="flex rounded-lg border border-zinc-800/70 overflow-hidden">
              <button
                onClick={() => setViewMode('html')}
                disabled={!hasHtml}
                className={clsx(
                  "px-3 py-1 text-xs font-medium transition-colors",
                  viewMode === 'html' && hasHtml
                    ? "bg-zinc-800 text-zinc-100"
                    : "text-zinc-400 hover:text-zinc-200",
                  !hasHtml && "opacity-40 cursor-not-allowed"
                )}
              >
                HTML
              </button>
              <button
                onClick={() => setViewMode('text')}
                className={clsx(
                  "px-3 py-1 text-xs font-medium transition-colors border-l border-zinc-800/70",
                  viewMode === 'text'
                    ? "bg-zinc-800 text-zinc-100"
                    : "text-zinc-400 hover:text-zinc-200"
                )}
              >
                Plain
              </button>
            </div>
            {item.read ? (
              <button
                onClick={() => onMarkUnread?.()}
                className="p-2 hover:bg-zinc-800/50 rounded-lg text-zinc-400 hover:text-zinc-200 transition-colors"
                title="Mark as unread"
              >
                <MailX size={16} />
              </button>
            ) : (
              <button
                onClick={() => onMarkRead?.()}
                className="p-2 hover:bg-zinc-800/50 rounded-lg text-zinc-400 hover:text-zinc-200 transition-colors"
                title="Mark as read"
              >
                <MailCheck size={16} />
              </button>
            )}
            {gmail?.message_id && (
              <button
                onClick={handleOpenInGmail}
                className="p-2 hover:bg-zinc-800/50 rounded-lg text-zinc-400 hover:text-zinc-200 transition-colors"
                title="Open in Gmail"
              >
                <ExternalLink size={16} />
              </button>
            )}
            <button
              onClick={onReply}
              className="p-2 hover:bg-zinc-800/50 rounded-lg text-zinc-400 hover:text-zinc-200 transition-colors"
              title="Reply"
            >
              <Reply size={16} />
            </button>
            <button
              onClick={onArchive}
              className="p-2 hover:bg-zinc-800/50 rounded-lg text-zinc-400 hover:text-zinc-200 transition-colors"
              title="Archive"
            >
              <Archive size={16} />
            </button>
            <button
              onClick={onDelete}
              className="p-2 hover:bg-red-500/10 hover:text-red-400 rounded-lg text-zinc-400 transition-colors"
              title="Delete"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>

        {/* Subject */}
        <div className="px-6 py-4 border-b border-zinc-800/50">
          <h1 className="text-xl font-semibold text-zinc-100">{item.title}</h1>
          <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
            <span
              className={clsx(
                "inline-flex items-center px-2 py-0.5 rounded-full border font-medium",
                folderChipClass
              )}
            >
              {folderLabel}
            </span>
            {categoryLabel && (
              <span
                className={clsx(
                  "inline-flex items-center px-2 py-0.5 rounded-full border font-medium",
                  categoryChipClass
                )}
              >
                {categoryLabel}
              </span>
            )}
            {gmailLabels.includes('STARRED') && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full border border-yellow-400/40 bg-yellow-500/10 text-yellow-200 font-medium">
                Starred
              </span>
            )}
          </div>
        </div>

        {/* Sender info */}
        <div className="px-6 py-4 border-b border-zinc-800/50 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-sm font-semibold">
            {item.sender?.[0]?.toUpperCase() || '?'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2">
              <span className="font-medium text-zinc-200">{item.sender}</span>
              <span className="text-xs text-zinc-600">
                {new Date(item.received_at).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: new Date(item.received_at).getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
                })}
              </span>
            </div>
            <div className="text-xs text-zinc-500">to me</div>
          </div>
        </div>
      </div>

      {/* Email body - scrollable */}
      <div className="flex-1 overflow-y-auto min-h-0 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
        <div className="px-6 py-6">
          {/* Calendar invite card (if present) */}
          {calendar && (calendar.summary || calendar.status || calendar.start || calendar.location) && (
            <div className="max-w-3xl mb-6 rounded-xl border border-emerald-900/40 bg-emerald-900/10 text-emerald-100 p-4">
              {calendar.status && (
                <div className={clsx(
                  "text-sm font-semibold mb-2 px-2 py-1 rounded-lg inline-flex",
                  calendar.status?.toLowerCase() === 'cancelled'
                    ? "bg-red-900/30 text-red-100 border border-red-800/60"
                    : "bg-emerald-800/40 border border-emerald-700/60"
                )}>
                  {calendar.status}
                </div>
              )}
              <h3 className="text-lg font-semibold text-emerald-50 mb-2">{calendar.summary || 'Calendar invite'}</h3>
              {calendar.start && (
                <div className="text-sm text-emerald-100/80">
                  <span className="font-semibold">When: </span>
                  {calendar.start}
                  {calendar.end ? ` — ${calendar.end}` : ''}
                </div>
              )}
              {calendar.location && (
                <div className="text-sm text-emerald-100/80">
                  <span className="font-semibold">Where: </span>
                  {calendar.location}
                </div>
              )}
              {calendar.url && (
                <div className="text-sm text-emerald-100/80">
                  <span className="font-semibold">Link: </span>
                  <a href={calendar.url} target="_blank" rel="noopener noreferrer" className="text-emerald-200 underline">
                    {calendar.url}
                  </a>
                </div>
              )}
              {Array.isArray(calendar.attendees) && calendar.attendees.length > 0 && (
                <div className="text-sm text-emerald-100/80 mt-2">
                  <span className="font-semibold">Guests: </span>
                  {calendar.attendees.join(', ')}
                </div>
              )}
              {calendar.description && (
                <div className="text-sm text-emerald-100/80 mt-2 whitespace-pre-line">
                  {calendar.description}
                </div>
              )}
            </div>
          )}

          <div className="text-sm text-zinc-300 leading-7 max-w-3xl">
            {viewMode === 'html' && hasHtml && sanitizedHtml ? (
              <div
                className="email-html space-y-4 [&_*]:max-w-full [&_a]:text-blue-600 [&_a]:underline [&_img]:rounded-lg [&_img]:border [&_img]:border-zinc-200 [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_td]:border [&_th]:border-zinc-200 [&_td]:border-zinc-200 [&_th]:px-3 [&_th]:py-2 [&_td]:px-3 [&_td]:py-2 [&_tr:nth-child(odd)]:bg-zinc-50 shadow-lg max-w-3xl mx-auto bg-white text-black rounded-xl p-8"
                dangerouslySetInnerHTML={{ __html: sanitizedHtml || rawBody }}
              />
            ) : (
              <div className="whitespace-pre-line">
                {plainBody}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
