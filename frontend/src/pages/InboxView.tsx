import { useEffect, useState } from 'react'
import './InboxView.css'

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

function InboxView() {
  const [items, setItems] = useState<InboxItem[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [selectedItem, setSelectedItem] = useState<InboxItem | null>(null)

  useEffect(() => {
    fetchInbox()
  }, [])

  const fetchInbox = async () => {
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

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'high':
        return 'var(--gradient-warning)'
      case 'medium':
        return 'var(--gradient-primary)'
      case 'low':
        return 'var(--gradient-success)'
      default:
        return 'var(--gradient-primary)'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "work":
        return 'Work'
      case "personal":
        return 'Personal'
      case "finance":
        return 'Finance'
      case "social":
        return 'Social'
      default:
        return 'Email'
    }
  }

  const filteredItems = items.filter((item) => {
    if (filter === 'all') return true
    if (filter === 'unread') return !item.read
    return item.category === filter
  })

  if (loading) {
    return (
      <div className="inbox-view">
        <div className="loading-state">
          <div className="spinner-large"></div>
          <p>Loading inbox...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="inbox-view fade-in">
      <div className="inbox-header">
        <div className="header-top">
          <h1 className="page-title gradient-text">Inbox</h1>
          <button className="sync-button glass">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
                clipRule="evenodd"
              />
            </svg>
            <span>Sync</span>
          </button>
        </div>

        <div className="filters">
          {['all', 'unread', "work", "personal", "finance"].map((f) => (
            <button
              key={f}
              className={`filter-btn ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="inbox-content">
        <div className="inbox-list">
          {filteredItems.map((item, index) => (
            <div
              key={item.id}
              className={`inbox-item glass hover-lift ${item.read ? 'read' : 'unread'} ${
                selectedItem?.id === item.id ? 'selected' : ''
              }`}
              style={{ animationDelay: `${index * 50}ms` }}
              onClick={() => setSelectedItem(item)}
            >
              <div
                className="item-indicator"
                style={{ background: getImportanceColor(item.importance) }}
              ></div>

              <div className="item-content">
                <div className="item-header">
                  <div className="item-meta">
                    <span className="category-icon">{getCategoryIcon(item.category)}</span>
                    <span className="sender">{item.sender}</span>
                    {!item.read && <span className="unread-dot"></span>}
                  </div>
                  <span className="timestamp">{item.timestamp}</span>
                </div>

                <h3 className="item-subject">{item.subject}</h3>
                <p className="item-preview">{item.preview}</p>

                {item.labels.length > 0 && (
                  <div className="item-labels">
                    {item.labels.map((label, i) => (
                      <span key={i} className="label">
                        {label}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {filteredItems.length === 0 && (
            <div className="empty-state scale-in">
              <div className="empty-icon">Empty</div>
              <h3>No messages</h3>
              <p>Your inbox is empty</p>
            </div>
          )}
        </div>

        {selectedItem && (
          <div className="inbox-detail glass-strong">
            <div className="detail-header">
              <button
                className="close-button"
                onClick={() => setSelectedItem(null)}
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
              <h2>{selectedItem.subject}</h2>
            </div>
            <div className="detail-meta">
              <span className="detail-sender">{selectedItem.sender}</span>
              <span className="detail-timestamp">{selectedItem.timestamp}</span>
            </div>
            <div className="detail-body">
              <p>{selectedItem.preview}</p>
              {/* Full email content would go here */}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default InboxView
