import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchInboxItems, InboxItem } from '../api/inbox'
import InboxCard from '../components/InboxCard'
import './InboxView.css'

function InboxView() {
  const [filter, setFilter] = useState<string>('all')

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['inbox', filter],
    queryFn: () => fetchInboxItems(filter),
  })

  if (isLoading) {
    return <div className="loading">Loading inbox...</div>
  }

  return (
    <div className="inbox-view">
      <div className="inbox-header">
        <h1>Inbox</h1>
        <div className="filter-tabs">
          <button className={filter === 'all' ? 'active' : ''} onClick={() => setFilter('all')}>
            All
          </button>
          <button className={filter === 'critical' ? 'active' : ''} onClick={() => setFilter('critical')}>
            Critical
          </button>
          <button className={filter === 'high' ? 'active' : ''} onClick={() => setFilter('high')}>
            High
          </button>
          <button className={filter === 'deadline' ? 'active' : ''} onClick={() => setFilter('deadline')}>
            Deadlines
          </button>
        </div>
      </div>

      <div className="inbox-list">
        {items.length === 0 ? (
          <div className="empty-state">No items to show</div>
        ) : (
          items.map((item: InboxItem) => <InboxCard key={item.id} item={item} />)
        )}
      </div>
    </div>
  )
}

export default InboxView

