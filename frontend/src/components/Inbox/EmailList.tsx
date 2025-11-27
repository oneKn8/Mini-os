import { useEffect, useRef } from 'react'
import { InboxItem } from '../../api/inbox'
import { staggerAnimation } from '../../utils/gsap'
import EmailItem from './EmailItem'

interface EmailListProps {
  items: InboxItem[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function EmailList({ items, selectedId, onSelect }: EmailListProps) {
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (listRef.current && items.length > 0) {
      const itemElements = listRef.current.querySelectorAll('[data-email-item]')
      if (itemElements.length > 0) {
        staggerAnimation(Array.from(itemElements), {
          opacity: 0,
          y: 20,
          duration: 0.4,
        }, 0.05)
      }
    }
  }, [items.length])

  return (
    <div ref={listRef} className="flex-1 flex flex-col gap-3 overflow-y-auto pr-2 no-scrollbar">
      {items.map((item) => (
        <EmailItem
          key={item.id}
          item={item}
          isSelected={selectedId === item.id}
          onClick={() => onSelect(item.id)}
        />
      ))}
    </div>
  )
}

