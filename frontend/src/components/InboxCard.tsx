import { InboxItem } from '../api/inbox'
import { format } from 'date-fns'
import './InboxCard.css'

interface Props {
  item: InboxItem
}

function InboxCard({ item }: Props) {
  const importanceColor = {
    critical: '#ff4444',
    high: '#ff9944',
    medium: '#ffdd44',
    low: '#88dd44',
    ignore: '#666',
  }

  return (
    <div className="inbox-card">
      <div className="card-header">
        <span className="importance-badge" style={{ backgroundColor: importanceColor[item.importance] }}>
          {item.importance}
        </span>
        <span className="category-badge">{item.category}</span>
        {item.due_datetime && <span className="due-date">Due: {format(new Date(item.due_datetime), 'MMM dd')}</span>}
      </div>

      <h3 className="card-title">{item.title}</h3>
      <p className="card-preview">{item.body_preview}</p>

      <div className="card-footer">
        <span className="sender">{item.sender || 'Unknown'}</span>
        <span className="timestamp">{format(new Date(item.received_at), 'MMM dd, HH:mm')}</span>
      </div>

      {item.suggested_action && (
        <div className="suggested-action">
          <strong>Suggested:</strong> {item.suggested_action}
        </div>
      )}
    </div>
  )
}

export default InboxCard

