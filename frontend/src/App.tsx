import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import TodayView from './pages/TodayView'
import InboxView from './pages/InboxView'
import PlannerView from './pages/PlannerView'
import ActionsView from './pages/ActionsView'
import SettingsView from './pages/SettingsView'
import ChatView from './pages/ChatView'
import DashboardView from './pages/DashboardView'
import CalendarView from './pages/CalendarView'
import WeatherView from './pages/WeatherView'
import AgentsView from './pages/AgentsView'

function App() {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardView />} />
          <Route path="today" element={<TodayView />} />
          <Route path="inbox" element={<InboxView />} />
          <Route path="calendar" element={<CalendarView />} />
          <Route path="weather" element={<WeatherView />} />
          <Route path="planner" element={<PlannerView />} />
          <Route path="actions" element={<ActionsView />} />
          <Route path="agents" element={<AgentsView />} />
          <Route path="settings" element={<SettingsView />} />
        </Route>
        <Route path="/chat" element={<ChatView />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
