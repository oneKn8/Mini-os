import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import { 
    Calendar, 
    Inbox, 
    Zap, 
    Settings, 
    Menu, 
    X,
    Activity,
    BarChart3,
    Cloud,
    ChevronLeft,
    ChevronRight,
    MessageSquare,
    Square
} from 'lucide-react'
import { clsx } from 'clsx'
import ChatWindow from './Chat/ChatWindow'
import { AgentCursor } from './AgentCursor'
import { ThoughtBubble } from './ThoughtBubble'
import { ConfettiCelebration } from './ConfettiCelebration'
import { ToastContainer } from './Toast'
import { useScreenController } from '../store/screenController'
import { useChatStore } from '../store/chatStore'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { path: '/inbox', label: 'Inbox', icon: Inbox },
  { path: '/calendar', label: 'Calendar', icon: Calendar },
  { path: '/weather', label: 'Weather', icon: Cloud },
  { path: '/actions', label: 'Actions', icon: Zap },
  { path: '/agents', label: 'Agents', icon: Activity },
  { path: '/settings', label: 'Settings', icon: Settings },
]

function Layout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebarCollapsed')
    return saved ? JSON.parse(saved) : true // Default to collapsed for Beast Mode look
  })
  const [isChatCollapsed, setIsChatCollapsed] = useState(() => {
    const saved = localStorage.getItem('chatCollapsed')
    return saved ? JSON.parse(saved) : false
  })
  const location = useLocation()

  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', JSON.stringify(isSidebarCollapsed))
  }, [isSidebarCollapsed])

  useEffect(() => {
    const syncChatCollapsed = () => {
      const saved = localStorage.getItem('chatCollapsed')
      setIsChatCollapsed(saved ? JSON.parse(saved) : false)
    }
    const handleCustom = (event: Event) => {
      const detail = (event as CustomEvent<boolean>).detail
      if (typeof detail === 'boolean') {
        setIsChatCollapsed(detail)
      } else {
        syncChatCollapsed()
      }
    }
    const handleExpand = () => setIsChatCollapsed(false)
    window.addEventListener('storage', syncChatCollapsed)
    window.addEventListener('chat-collapsed-change', handleCustom as EventListener)
    window.addEventListener('chatExpand', handleExpand)
    return () => {
      window.removeEventListener('storage', syncChatCollapsed)
      window.removeEventListener('chat-collapsed-change', handleCustom as EventListener)
      window.removeEventListener('chatExpand', handleExpand)
    }
  }, [])

  return (
    <div className="flex h-screen w-full bg-bg-primary text-text-primary overflow-hidden font-sans relative">
      
      {/* Desktop Floating Sidebar */}
      <motion.aside 
        className="hidden md:flex flex-col fixed left-4 top-4 bottom-4 z-50 rounded-2xl glass-panel border-border-light shadow-2xl overflow-hidden"
        initial={false}
        animate={{ width: isSidebarCollapsed ? 80 : 240 }}
        transition={{ duration: 0.4, type: "spring", bounce: 0.15 }}
      >
        <div className={clsx("flex items-center gap-3 py-6", isSidebarCollapsed ? "justify-center px-0" : "px-6")}>
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary text-white shadow-lg shrink-0">
            <Activity size={22} />
            <div className="absolute inset-0 rounded-xl bg-white/20 animate-pulse-glow"></div>
          </div>
          <AnimatePresence>
            {!isSidebarCollapsed && (
              <motion.div 
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                className="flex flex-col overflow-hidden whitespace-nowrap"
              >
                <span className="text-lg font-bold tracking-tight text-white">Ops Center</span>
                <span className="text-[10px] text-text-tertiary uppercase tracking-wider">System Online</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <nav className="flex-1 flex flex-col gap-2 px-3 py-4">
            {navItems.map((item) => {
                const isActive = location.pathname.startsWith(item.path)
                return (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => clsx(
                            "flex items-center relative group rounded-xl transition-all duration-300",
                            isSidebarCollapsed ? "justify-center h-12 w-12 mx-auto" : "px-4 py-3 gap-3",
                            isActive 
                                ? "text-white bg-white/10 shadow-[0_0_15px_rgba(255,255,255,0.1)] border border-white/10" 
                                : "text-text-secondary hover:text-white hover:bg-white/5"
                        )}
                        title={isSidebarCollapsed ? item.label : undefined}
                    >
                        <item.icon 
                          size={20} 
                          className={clsx(
                            "shrink-0 transition-colors",
                            isActive ? "text-accent-primary drop-shadow-[0_0_5px_rgba(76,110,245,0.8)]" : "group-hover:text-white"
                          )} 
                        />
                        
                        <AnimatePresence>
                          {!isSidebarCollapsed && (
                            <motion.span
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                              className="text-sm font-medium whitespace-nowrap"
                            >
                              {item.label}
                            </motion.span>
                          )}
                        </AnimatePresence>

                        {/* Active Indicator Dot (Collapsed) */}
                        {isSidebarCollapsed && isActive && (
                           <motion.div 
                             layoutId="activeDot"
                             className="absolute -right-1 top-1/2 -translate-y-1/2 w-1 h-1 bg-accent-primary rounded-full shadow-[0_0_8px_#4c6ef5]" 
                           />
                        )}
                    </NavLink>
                )
            })}
        </nav>

        {/* Collapse Toggle */}
        <button
          onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          className="mt-auto mx-3 mb-4 p-3 rounded-xl hover:bg-white/5 text-text-tertiary hover:text-white transition-colors flex justify-center"
        >
          {isSidebarCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </motion.aside>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-30 flex h-16 items-center justify-between border-b border-border-light bg-surface/80 backdrop-blur-md px-4">
        <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-primary text-white">
                <Activity size={20} />
            </div>
            <span className="font-bold text-lg text-white">Ops Center</span>
        </div>
        <button 
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-text-secondary hover:bg-white/10 rounded-md"
        >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>
      
      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {isMobileMenuOpen && (
            <motion.div 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="fixed inset-0 z-20 bg-surface pt-20 px-4 md:hidden"
            >
                 <nav className="space-y-2">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            onClick={() => setIsMobileMenuOpen(false)}
                            className={({ isActive }) => clsx(
                                "flex items-center gap-3 rounded-lg px-4 py-3 text-base font-medium transition-colors",
                                isActive 
                                    ? "bg-accent-primary/20 text-white border border-accent-primary/20" 
                                    : "text-text-secondary hover:bg-white/5"
                            )}
                        >
                            <item.icon size={20} />
                            {item.label}
                        </NavLink>
                    ))}
                 </nav>
            </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content + Chat Resizable Group */}
      <div className={clsx(
          "flex-1 h-full overflow-hidden pt-16 md:pt-0 relative transition-all duration-400 ease-spring z-10",
          "md:pl-[100px]", // Base padding for collapsed sidebar
          !isSidebarCollapsed && "md:pl-[260px]" // Padding when expanded
      )}>
          <ChatCollapseButton 
            isCollapsed={isChatCollapsed} 
            onExpand={() => {
              localStorage.setItem('chatCollapsed', JSON.stringify(false))
              setIsChatCollapsed(false)
              window.dispatchEvent(new CustomEvent('chat-collapsed-change', { detail: false }))
            }} 
          />
          {isChatCollapsed ? (
            <main className="app-main h-full w-full overflow-y-auto overflow-x-hidden md:p-6 px-4 scroll-smooth bg-bg-primary relative isolate z-50">
              <div className="mx-auto max-w-7xl min-h-full pb-20">
                  <AnimatePresence mode="wait">
                      <motion.div
                          key={location.pathname}
                          initial={{ opacity: 0, y: 20, scale: 0.98 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: -20, scale: 0.98 }}
                          transition={{ duration: 0.3, ease: "easeOut" }}
                          className="min-h-full"
                      >
                          <Outlet />
                      </motion.div>
                  </AnimatePresence>
              </div>
            </main>
          ) : (
            <PanelGroup direction="horizontal" className="h-full w-full">
              <Panel defaultSize={70} minSize={30}>
                  <main className="app-main h-full w-full overflow-y-auto overflow-x-hidden md:p-6 px-4 scroll-smooth bg-bg-primary relative isolate z-50">
                      <div className="mx-auto max-w-7xl min-h-full pb-20">
                          <AnimatePresence mode="wait">
                              <motion.div
                                  key={location.pathname}
                                  initial={{ opacity: 0, y: 20, scale: 0.98 }}
                                  animate={{ opacity: 1, y: 0, scale: 1 }}
                                  exit={{ opacity: 0, y: -20, scale: 0.98 }}
                                  transition={{ duration: 0.3, ease: "easeOut" }}
                                  className="min-h-full"
                              >
                                  <Outlet />
                              </motion.div>
                          </AnimatePresence>
                      </div>
                  </main>
              </Panel>
              
              <PanelResizeHandle className="w-1 hover:w-1.5 bg-transparent hover:bg-accent-primary/50 transition-all duration-300 flex items-center justify-center group z-50">
                  <div className="h-12 w-1 rounded-full bg-white/10 group-hover:bg-accent-primary"></div>
              </PanelResizeHandle>
              
              <Panel defaultSize={30} minSize={0} maxSize={50} className="bg-surface/90 backdrop-blur-xl border-l border-white/5 shadow-2xl z-40 relative">
                  <ChatWindow />
              </Panel>
            </PanelGroup>
          )}
          {isChatCollapsed && (
            <button
              onClick={() => {
                localStorage.setItem('chatCollapsed', JSON.stringify(false))
                setIsChatCollapsed(false)
                window.dispatchEvent(new CustomEvent('chat-collapsed-change', { detail: false }))
              }}
              className="fixed bottom-6 right-6 md:bottom-8 md:right-8 p-4 bg-accent-primary text-white rounded-full shadow-[0_0_20px_rgba(76,110,245,0.5)] hover:bg-accent-primary-hover transition-colors z-50 flex items-center gap-2"
              aria-label="Expand chat"
            >
              <MessageSquare size={22} />
              <span className="hidden sm:inline text-sm font-medium">Chat</span>
            </button>
          )}
      </div>
    </div>
  )
}

// Navigation Listener Hook
function useNavigationListener() {
    const navigate = useNavigate()
    useEffect(() => {
        const handleNavigation = (event: CustomEvent<string>) => {
            if (event.detail) {
                navigate(event.detail)
            }
        }
        
        // Handle both chat-navigate and agent-navigate events
        const handleAgentNavigation = (event: CustomEvent<{ page: string; focus?: string }>) => {
            if (event.detail?.page) {
                navigate(event.detail.page)
            }
        }
        
        window.addEventListener('chat-navigate', handleNavigation as EventListener)
        window.addEventListener('agent-navigate', handleAgentNavigation as EventListener)
        return () => {
            window.removeEventListener('chat-navigate', handleNavigation as EventListener)
            window.removeEventListener('agent-navigate', handleAgentNavigation as EventListener)
        }
    }, [navigate])
}

// Keyboard Shortcuts Hook
function useKeyboardShortcuts() {
    const { stopAgent, agentActive, canUndo, undo } = useScreenController()
    const { pendingApprovals, handleApproval } = useChatStore()
    
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Escape - Stop agent
            if (e.key === 'Escape' && agentActive) {
                e.preventDefault()
                stopAgent()
            }
            
            // Enter - Approve first pending action
            if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey && pendingApprovals.length > 0) {
                // Only if not typing in an input
                if (document.activeElement?.tagName !== 'INPUT' && 
                    document.activeElement?.tagName !== 'TEXTAREA') {
                    e.preventDefault()
                    handleApproval(pendingApprovals[0].id, true)
                }
            }
            
            // Ctrl+Z - Undo
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey && canUndo) {
                e.preventDefault()
                undo()
            }
        }
        
        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [agentActive, pendingApprovals, canUndo, stopAgent, handleApproval, undo])
}

function LayoutWithNavigation() {
  useNavigationListener()
  useKeyboardShortcuts()
  const { agentActive, stopAgent } = useScreenController()
  
  return (
    <>
      <Layout />
      
      {/* Agent Visual Components */}
      <AgentCursor />
      <ThoughtBubble />
      <ConfettiCelebration />
      <ToastContainer />
      
      {/* Agent Stop Button - shows when agent is working */}
      <AnimatePresence>
        {agentActive && (
          <motion.button
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            onClick={stopAgent}
            className="fixed top-4 right-4 z-[9999] flex items-center gap-2 px-3 py-2 
                       bg-zinc-900/90 backdrop-blur-sm border border-zinc-800/50 
                       rounded-lg text-zinc-300 hover:text-white hover:border-zinc-700 
                       transition-colors shadow-lg"
          >
            <Square size={14} className="text-red-400" />
            <span className="text-xs font-medium">Stop Agent</span>
            <kbd className="ml-1 text-[10px] text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded">Esc</kbd>
          </motion.button>
        )}
      </AnimatePresence>
    </>
  )
}

export default LayoutWithNavigation
function ChatCollapseButton({ isCollapsed, onExpand }: { isCollapsed: boolean, onExpand: () => void }) {
  if (!isCollapsed) return null

  return (
    <motion.button
      initial={{ opacity: 0, scale: 0 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0 }}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={onExpand}
      className="fixed bottom-8 right-8 p-4 bg-accent-primary text-white rounded-full shadow-[0_0_20px_rgba(76,110,245,0.5)] hover:bg-accent-primary-hover transition-colors z-50 flex items-center gap-2"
      aria-label="Expand chat"
    >
      <MessageSquare size={24} />
    </motion.button>
  )
}
