import { Outlet, NavLink } from 'react-router-dom'
import './Layout.css'

function Layout() {
  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="logo">Personal Ops Center</div>
        <div className="nav-links">
          <NavLink to="/today" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Today
          </NavLink>
          <NavLink to="/inbox" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Inbox
          </NavLink>
          <NavLink to="/planner" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Planner
          </NavLink>
          <NavLink to="/actions" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Actions
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Settings
          </NavLink>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout

