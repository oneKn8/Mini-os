import { Outlet, NavLink } from 'react-router-dom'
import { useState } from 'react'
import './Layout.css'
import ChatAssistant from './ChatAssistant/ChatAssistant'

function Layout() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="layout">
      <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path
            d="M3 7h14M3 13h14"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      </button>

      <nav className={`sidebar ${menuOpen ? 'open' : ''}`}>
        <div className="logo">
          <div className="logo-icon">
            <svg width="24" height="24" viewBox="0 0 20 20" fill="white">
              <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="logo-text">Ops Center</div>
        </div>

        <div className="nav-links">
          <NavLink
            to="/today"
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            onClick={() => setMenuOpen(false)}
          >
            <svg className="nav-icon" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
            </svg>
            Today
          </NavLink>

          <NavLink
            to="/inbox"
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            onClick={() => setMenuOpen(false)}
          >
            <svg className="nav-icon" viewBox="0 0 20 20" fill="currentColor">
              <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
              <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
            </svg>
            Inbox
          </NavLink>

          <NavLink
            to="/planner"
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            onClick={() => setMenuOpen(false)}
          >
            <svg className="nav-icon" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                clipRule="evenodd"
              />
            </svg>
            Planner
          </NavLink>

          <NavLink
            to="/actions"
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            onClick={() => setMenuOpen(false)}
          >
            <svg className="nav-icon" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                clipRule="evenodd"
              />
            </svg>
            Actions
          </NavLink>

          <NavLink
            to="/settings"
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            onClick={() => setMenuOpen(false)}
          >
            <svg className="nav-icon" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                clipRule="evenodd"
              />
            </svg>
            Settings
          </NavLink>
        </div>

        <div className="status-indicator">
          <div className="status-card">
            <div className="status-dot"></div>
            <div className="status-text">AI Agents Active</div>
          </div>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>

      <ChatAssistant />
    </div>
  )
}

export default Layout
