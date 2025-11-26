import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import TodayView from './pages/TodayView'
import InboxView from './pages/InboxView'
import PlannerView from './pages/PlannerView'
import ActionsView from './pages/ActionsView'
import SettingsView from './pages/SettingsView'
import ChatView from './pages/ChatView'

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
          <Route index element={<Navigate to="/today" replace />} />
          <Route path="today" element={<TodayView />} />
          <Route path="inbox" element={<InboxView />} />
          <Route path="planner" element={<PlannerView />} />
          <Route path="actions" element={<ActionsView />} />
          <Route path="settings" element={<SettingsView />} />
        </Route>
        <Route path="/chat" element={<ChatView />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
