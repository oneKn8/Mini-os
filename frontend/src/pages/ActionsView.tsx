import { useQuery } from '@tanstack/react-query'
import { fetchPendingActions } from '../api/actions'
import ActionCard from '../components/ActionCard'
import './ActionsView.css'

function ActionsView() {
  const { data: actions = [], isLoading } = useQuery({
    queryKey: ['pending-actions'],
    queryFn: fetchPendingActions,
  })

  if (isLoading) {
    return <div className="loading">Loading actions...</div>
  }

  return (
    <div className="actions-view">
      <h1>Pending Actions</h1>
      <p className="subtitle">Review and approve agent-proposed actions</p>

      <div className="actions-list">
        {actions.length === 0 ? (
          <div className="empty-state">No pending actions</div>
        ) : (
          actions.map((action: any) => <ActionCard key={action.id} action={action} />)
        )}
      </div>
    </div>
  )
}

export default ActionsView

