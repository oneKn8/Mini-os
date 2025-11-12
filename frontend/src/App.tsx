import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import InboxView from './pages/InboxView'
import TodayView from './pages/TodayView'
import PlannerView from './pages/PlannerView'
import ActionsView from './pages/ActionsView'
import SettingsView from './pages/SettingsView'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/today" replace />} />
            <Route path="inbox" element={<InboxView />} />
            <Route path="today" element={<TodayView />} />
            <Route path="planner" element={<PlannerView />} />
            <Route path="actions" element={<ActionsView />} />
            <Route path="settings" element={<SettingsView />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App

