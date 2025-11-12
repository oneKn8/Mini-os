import { useQuery } from '@tanstack/react-query'
import { fetchTodayPlan } from '../api/planner'
import './TodayView.css'

function TodayView() {
  const { data: plan, isLoading } = useQuery({
    queryKey: ['today-plan'],
    queryFn: fetchTodayPlan,
  })

  if (isLoading) {
    return <div className="loading">Loading today's plan...</div>
  }

  return (
    <div className="today-view">
      <div className="today-header">
        <h1>Today</h1>
        <p className="date">{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</p>
      </div>

      <div className="today-grid">
        <section className="must-do-section">
          <h2>Must Do Today</h2>
          <div className="must-do-list">
            {plan?.must_do_today?.map((task: string, idx: number) => (
              <div key={idx} className="must-do-item">
                <input type="checkbox" />
                <span>{task}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="focus-section">
          <h2>Focus Areas</h2>
          <div className="focus-list">
            {plan?.focus_areas?.map((area: string, idx: number) => (
              <div key={idx} className="focus-item">
                {area}
              </div>
            ))}
          </div>
        </section>

        <section className="schedule-section">
          <h2>Suggested Schedule</h2>
          <div className="schedule-list">
            {plan?.time_recommendations?.map((rec: any, idx: number) => (
              <div key={idx} className="schedule-item">
                <span className="time">{rec.suggested_time}</span>
                <span className="task">{rec.task}</span>
                <span className="duration">{rec.duration_minutes}m</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

export default TodayView

