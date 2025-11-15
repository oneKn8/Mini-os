import { useEffect, useState } from 'react'
import './TodayView.css'

interface TimeBlock {
  id: string
  time: string
  title: string
  type: "focus" | "meeting" | "break" | "task"
  duration: number
  completed?: boolean
}

interface DailyPlan {
  date: string
  summary: string
  priorities: string[]
  time_blocks: TimeBlock[]
  weather?: {
    temp: number
    condition: string
    icon: string
  }
}

function TodayView() {
  const [plan, setPlan] = useState<DailyPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    fetchDailyPlan()
    const timer = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

  const fetchDailyPlan = async () => {
    try {
      const response = await fetch('/api/planner/today')
      if (response.ok) {
        const data = await response.json()
        setPlan(data)
      }
    } catch (error) {
      console.error('Failed to fetch daily plan:', error)
    } finally {
      setLoading(false)
    }
  }

  const getGreeting = () => {
    const hour = currentTime.getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 18) return 'Good afternoon'
    return 'Good evening'
  }

  const formatDate = () => {
    return currentTime.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    })
  }

  const formatTime = () => {
    return currentTime.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    })
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "focus":
        return 'Focus'
      case "meeting":
        return 'Meeting'
      case "break":
        return 'Break'
      case "task":
        return 'Task'
      default:
        return '.'
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case "focus":
        return 'var(--color-accent-primary)'
      case "meeting":
        return 'var(--color-accent-secondary)'
      case "break":
        return 'var(--color-accent-info)'
      case "task":
        return 'var(--color-accent-success)'
      default:
        return 'var(--color-accent-primary)'
    }
  }

  if (loading) {
    return (
      <div className="today-view">
        <div className="loading-state">
          <div className="spinner-large"></div>
          <p>Loading your day...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="today-view fade-in">
      {/* Hero Header */}
      <div className="hero-header glass-strong">
        <div className="hero-content">
          <div className="greeting-section">
            <h1 className="greeting">{getGreeting()} Sparkle</h1>
            <p className="date-time">
              <span className="date">{formatDate()}</span>
              <span className="time-divider">.</span>
              <span className="time">{formatTime()}</span>
            </p>
          </div>
          
          {plan?.weather && (
            <div className="weather-widget">
              <div className="weather-icon">{plan.weather.icon}</div>
              <div className="weather-info">
                <div className="weather-temp">{plan.weather.temp}°</div>
                <div className="weather-condition">{plan.weather.condition}</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Daily Summary */}
      {plan?.summary && (
        <div className="summary-card glass slide-in">
          <div className="card-header">
            <h2>Today's Focus</h2>
            <div className="pulse-indicator"></div>
          </div>
          <p className="summary-text">{plan.summary}</p>
        </div>
      )}

      {/* Priorities */}
      {plan?.priorities && plan.priorities.length > 0 && (
        <div className="priorities-section slide-in">
          <h3 className="section-title">
            <span className="title-icon">Lightning</span>
            Top Priorities
          </h3>
          <div className="priorities-grid">
            {plan.priorities.map((priority, index) => (
              <div
                key={index}
                className="priority-card"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="priority-number" style={{ background: getTypeColor("focus") }}>
                  {index + 1}
                </div>
                <p className="priority-text">{priority}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Time Blocks */}
      {plan?.time_blocks && plan.time_blocks.length > 0 && (
        <div className="time-blocks-section slide-in">
          <h3 className="section-title">
            <span className="title-icon">Calendar</span>
            Your Schedule
          </h3>
          <div className="time-blocks-list">
            {plan.time_blocks.map((block, index) => (
              <div
                key={block.id}
                className={`time-block ${block.completed ? 'completed' : ''}`}
                style={{ animationDelay: `${index * 80}ms` }}
              >
                <div className="block-indicator" style={{ background: getTypeColor(block.type) }}></div>
                <div className="block-content">
                  <div className="block-header">
                    <div className="block-time">{block.time}</div>
                    <div className="block-type">
                      <span>{getTypeIcon(block.type)}</span>
                      <span className="type-label">{block.type}</span>
                    </div>
                  </div>
                  <h4 className="block-title">{block.title}</h4>
                  <div className="block-duration">{block.duration} min</div>
                </div>
                {block.completed && (
                  <div className="completed-badge">
                    <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!plan && (
        <div className="empty-state scale-in">
          <div className="empty-icon">Board</div>
          <h3>No plan for today yet</h3>
          <p>Run the planner agent to generate your daily schedule</p>
          <button className="cta-button">
            <span>Generate Plan</span>
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      )}
    </div>
  )
}

export default TodayView
