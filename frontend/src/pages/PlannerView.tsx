import './PlannerView.css'

function PlannerView() {
  return (
    <div className="planner-view fade-in">
      <div className="planner-header">
        <h1 className="page-title gradient-text">Weekly Planner</h1>
        <div className="week-navigation">
          <button className="week-nav-button">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </button>
          <span className="week-label">This Week</span>
          <button className="week-nav-button">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>

      <div className="coming-soon glass">
        <div className="coming-soon-icon">Calendar</div>
        <h2>Weekly Planner Coming Soon</h2>
        <p>Drag-and-drop calendar view with weekly planning features</p>
        <ul className="feature-list">
          <li>Week-view calendar with time blocks</li>
          <li>Drag-and-drop scheduling</li>
          <li>Weekly goals and focus areas</li>
          <li>Time analytics and insights</li>
        </ul>
      </div>
    </div>
  )
}

export default PlannerView
