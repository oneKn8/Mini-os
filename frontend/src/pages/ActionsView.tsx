import { useEffect, useState } from 'react'
import './ActionsView.css'

interface Action {
  id: string
  type: 'email_reply' | 'calendar_event' | 'task_create' | 'reminder'
  title: string
  description: string
  proposed_by: string
  confidence: number
  created_at: string
  status: 'pending' | 'approved' | 'rejected'
  preview?: {
    to?: string
    subject?: string
    body?: string
    time?: string
    location?: string
  }
}

function ActionsView() {
  const [actions, setActions] = useState<Action[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'pending' | 'all'>('pending')

  useEffect(() => {
    fetchActions()
  }, [])

  const fetchActions = async () => {
    try {
      const response = await fetch('/api/actions')
      if (response.ok) {
        const data = await response.json()
        setActions(data.actions || [])
      }
    } catch (error) {
      console.error('Failed to fetch actions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (actionId: string) => {
    try {
      await fetch(`/api/actions/${actionId}/approve`, { method: 'POST' })
      setActions(actions.map(a => a.id === actionId ? { ...a, status: 'approved' } : a))
    } catch (error) {
      console.error('Failed to approve action:', error)
    }
  }

  const handleReject = async (actionId: string) => {
    try {
      await fetch(`/api/actions/${actionId}/reject`, { method: 'POST' })
      setActions(actions.map(a => a.id === actionId ? { ...a, status: 'rejected' } : a))
    } catch (error) {
      console.error('Failed to reject action:', error)
    }
  }

  const getTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      email_reply: 'Email',
      calendar_event: 'Calendar',
      task_create: 'Task',
      reminder: 'Reminder',
    }
    return icons[type] || 'Action'
  }

  const getTypeGradient = (type: string) => {
    switch (type) {
      case 'email_reply':
        return 'var(--gradient-primary)'
      case 'calendar_event':
        return 'var(--gradient-warning)'
      case 'task_create':
        return 'var(--gradient-success)'
      case 'reminder':
        return 'var(--gradient-secondary)'
      default:
        return 'var(--gradient-primary)'
    }
  }

  const filteredActions = actions.filter(a => 
    filter === 'all' || a.status === 'pending'
  )

  if (loading) {
    return (
      <div className="actions-view">
        <div className="loading-state">
          <div className="spinner-large"></div>
          <p>Loading actions...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="actions-view fade-in">
      <div className="actions-header">
        <h1 className="page-title">Proposed Actions</h1>
        <div className="filters">
          <button
            className={`filter-btn ${filter === 'pending' ? 'active' : ''}`}
            onClick={() => setFilter('pending')}
          >
            Pending ({actions.filter(a => a.status === 'pending').length})
          </button>
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({actions.length})
          </button>
        </div>
      </div>

      <div className="actions-grid">
        {filteredActions.map((action, index) => (
          <div
            key={action.id}
            className={`action-card ${action.status}`}
            style={{ animationDelay: `${index * 80}ms` }}
          >
            <div className="action-header">
              <div className="action-type" style={{ background: getTypeGradient(action.type) }}>
                <span className="type-icon">{getTypeIcon(action.type).charAt(0)}</span>
              </div>
              <div className="confidence-badge">
                <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span>{Math.round(action.confidence * 100)}%</span>
              </div>
            </div>

            <h3 className="action-title">{action.title}</h3>
            <p className="action-description">{action.description}</p>

            {action.preview && (
              <div className="action-preview">
                {action.preview.to && (
                  <div className="preview-row">
                    <span className="preview-label">To:</span>
                    <span className="preview-value">{action.preview.to}</span>
                  </div>
                )}
                {action.preview.subject && (
                  <div className="preview-row">
                    <span className="preview-label">Subject:</span>
                    <span className="preview-value">{action.preview.subject}</span>
                  </div>
                )}
                {action.preview.body && (
                  <div className="preview-body">{action.preview.body}</div>
                )}
                {action.preview.time && (
                  <div className="preview-row">
                    <span className="preview-label">Time:</span>
                    <span className="preview-value">{action.preview.time}</span>
                  </div>
                )}
                {action.preview.location && (
                  <div className="preview-row">
                    <span className="preview-label">Location:</span>
                    <span className="preview-value">{action.preview.location}</span>
                  </div>
                )}
              </div>
            )}

            <div className="action-footer">
              <span className="proposed-by">by {action.proposed_by}</span>
              {action.status === 'pending' ? (
                <div className="action-buttons">
                  <button
                    className="reject-button"
                    onClick={() => handleReject(action.id)}
                  >
                    <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Reject
                  </button>
                  <button
                    className="approve-button"
                    onClick={() => handleApprove(action.id)}
                  >
                    <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Approve
                  </button>
                </div>
              ) : (
                <span className={`status-badge ${action.status}`}>
                  {action.status}
                </span>
              )}
            </div>
          </div>
        ))}

        {filteredActions.length === 0 && (
          <div className="empty-state scale-in">
            <div className="empty-icon">
              <svg width="80" height="80" viewBox="0 0 20 20" fill="currentColor">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </div>
            <h3>No pending actions</h3>
            <p>AI agents will propose actions here for your approval</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ActionsView
