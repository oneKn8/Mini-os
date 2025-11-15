import { useMutation, useQueryClient } from '@tanstack/react-query'
import { approveAction, rejectAction } from '../api/actions'
import './ActionCard.css'

interface Props {
  action: any
}

function ActionCard({ action }: Props) {
  const queryClient = useQueryClient()

  const approveMutation = useMutation({
    mutationFn: () => approveAction(action.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-actions'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: () => rejectAction(action.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-actions'] })
    },
  })

  return (
    <div className="action-card">
      <div className="action-header">
        <span className="agent-badge">{action.agent_name}</span>
        <span className={`risk-badge ${action.risk_level}`}>
          {action.risk_level} risk
        </span>
      </div>

      <h3 className="action-type">{action.action_type.replace(/_/g, ' ')}</h3>
      <p className="explanation">{action.explanation}</p>

      <div className="payload-preview">
        <pre>{JSON.stringify(action.payload, null, 2)}</pre>
      </div>

      <div className="action-buttons">
        <button className="approve-btn" onClick={() => approveMutation.mutate()} disabled={approveMutation.isPending}>
          {approveMutation.isPending ? 'Approving...' : 'Approve'}
        </button>
        <button className="reject-btn" onClick={() => rejectMutation.mutate()} disabled={rejectMutation.isPending}>
          {rejectMutation.isPending ? 'Rejecting...' : 'Reject'}
        </button>
      </div>
    </div>
  )
}

export default ActionCard

