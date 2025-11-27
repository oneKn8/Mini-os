import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import Layout from './components/Layout'
import ErrorBoundary from './components/ErrorBoundary'
import LoadingSpinner from './components/UI/LoadingSpinner'
import PageTransition from './components/Animations/PageTransition'

// Lazy load pages for code splitting
const DashboardView = lazy(() => import('./pages/DashboardView'))
const TodayView = lazy(() => import('./pages/TodayView'))
const InboxView = lazy(() => import('./pages/InboxView'))
const CalendarView = lazy(() => import('./pages/CalendarView'))
const WeatherView = lazy(() => import('./pages/WeatherView'))
const PlannerView = lazy(() => import('./pages/PlannerView'))
const ActionsView = lazy(() => import('./pages/ActionsView'))
const AgentsView = lazy(() => import('./pages/AgentsView'))
const SettingsView = lazy(() => import('./pages/SettingsView'))
const ChatView = lazy(() => import('./pages/ChatView'))

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route
              path="dashboard"
              element={
                <Suspense fallback={<LoadingSpinner size={60} className="mx-auto mt-20" />}>
                  <PageTransition>
                    <DashboardView />
                  </PageTransition>
                </Suspense>
              }
            />
            <Route
              path="today"
              element={
                <Suspense fallback={<LoadingSpinner size={60} className="mx-auto mt-20" />}>
                  <PageTransition>
                    <TodayView />
                  </PageTransition>
                </Suspense>
              }
            />
            <Route
              path="inbox"
              element={
                <Suspense fallback={<LoadingSpinner size={60} className="mx-auto mt-20" />}>
                  <PageTransition>
                    <InboxView />
                  </PageTransition>
                </Suspense>
              }
            />
            <Route
              path="calendar"
              element={
                <Suspense fallback={<LoadingSpinner size={60} className="mx-auto mt-20" />}>
                  <PageTransition>
                    <CalendarView />
                  </PageTransition>
                </Suspense>
              }
            />
            <Route
              path="weather"
              element={
                <Suspense fallback={<LoadingSpinner size={60} className="mx-auto mt-20" />}>
                  <PageTransition>
                    <WeatherView />
                  </PageTransition>
                </Suspense>
              }
            />
            <Route
              path="planner"
              element={
                <Suspense fallback={<LoadingSpinner size={60} className="mx-auto mt-20" />}>
                  <PageTransition>
                    <PlannerView />
                  </PageTransition>
                </Suspense>
              }
            />
            <Route
              path="actions"
              element={
                <Suspense fallback={<LoadingSpinner size={60} className="mx-auto mt-20" />}>
                  <PageTransition>
                    <ActionsView />
                  </PageTransition>
                </Suspense>
              }
            />
            <Route
              path="agents"
              element={
                <Suspense fallback={<LoadingSpinner size={60} className="mx-auto mt-20" />}>
                  <PageTransition>
                    <AgentsView />
                  </PageTransition>
                </Suspense>
              }
            />
            <Route
              path="settings"
              element={
                <Suspense fallback={<LoadingSpinner size={60} className="mx-auto mt-20" />}>
                  <PageTransition>
                    <SettingsView />
                  </PageTransition>
                </Suspense>
              }
            />
          </Route>
          <Route
            path="/chat"
            element={
              <Suspense fallback={<LoadingSpinner size={60} className="mx-auto mt-20" />}>
                <ChatView />
              </Suspense>
            }
          />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
