import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import { 
    Calendar, 
    Inbox, 
    Trello, 
    Zap, 
    Settings, 
    Menu, 
    X,
    Activity,
    GripVertical
} from 'lucide-react'
import { clsx } from 'clsx'
import ChatWindow from './Chat/ChatWindow'

const navItems = [
  { path: '/today', label: 'Today', icon: Calendar },
  { path: '/inbox', label: 'Inbox', icon: Inbox },
  { path: '/planner', label: 'Planner', icon: Trello },
  { path: '/actions', label: 'Actions', icon: Zap },
  { path: '/settings', label: 'Settings', icon: Settings },
]

function Layout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="flex h-screen w-full bg-bg-secondary text-text-primary overflow-hidden font-sans">
      {/* Desktop Left Navigation Sidebar */}
      <aside className="hidden w-64 flex-col border-r border-border-light bg-surface px-4 py-6 md:flex shadow-sm z-20 shrink-0">
        <div className="flex items-center gap-3 px-2 mb-8">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-primary text-white shadow-md">
                <Activity size={20} />
            </div>
            <span className="text-lg font-bold tracking-tight text-text-primary">Ops Center</span>
        </div>

        <nav className="flex-1 space-y-1">
            {navItems.map((item) => {
                const isActive = location.pathname.startsWith(item.path)
                return (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => clsx(
                            "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                            isActive 
                                ? "bg-accent-primary/10 text-accent-primary" 
                                : "text-text-secondary hover:bg-surface-hover hover:text-text-primary"
                        )}
                    >
                        <item.icon size={18} className={clsx(isActive ? "text-accent-primary" : "text-text-tertiary group-hover:text-text-primary")} />
                        {item.label}
                    </NavLink>
                )
            })}
        </nav>

        <div className="mt-auto pt-6 border-t border-border-light">
             <div className="flex items-center gap-3 rounded-lg bg-bg-secondary px-3 py-3 border border-border-light">
                <div className="h-2 w-2 rounded-full bg-accent-success animate-pulse shadow-[0_0_8px_rgba(18,184,134,0.4)]"></div>
                <div className="flex flex-col">
                    <span className="text-xs font-semibold text-text-primary">System Online</span>
                    <span className="text-[10px] text-text-tertiary">All agents active</span>
                </div>
             </div>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-30 flex h-16 items-center justify-between border-b border-border-light bg-surface px-4">
        <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-primary text-white">
                <Activity size={20} />
            </div>
            <span className="font-bold text-lg">Ops Center</span>
        </div>
        <button 
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-text-secondary hover:bg-bg-secondary rounded-md"
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
                transition={{ duration: 0.2 }}
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
                                    ? "bg-accent-primary/10 text-accent-primary" 
                                    : "text-text-secondary hover:bg-bg-secondary"
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
      <div className="flex-1 h-full overflow-hidden pt-16 md:pt-0">
          <PanelGroup direction="horizontal">
            <Panel defaultSize={70} minSize={30}>
                <main className="h-full w-full overflow-y-auto overflow-x-hidden md:p-6 px-4 bg-bg-secondary">
                    <div className="mx-auto max-w-5xl min-h-full">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={location.pathname}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.2 }}
                                className="min-h-full"
                            >
                                <Outlet />
                            </motion.div>
                        </AnimatePresence>
                    </div>
                </main>
            </Panel>
            
            <PanelResizeHandle className="w-1 bg-border-light hover:bg-accent-primary/50 transition-colors flex items-center justify-center">
                <div className="h-8 w-1 rounded-full bg-border-medium"></div>
            </PanelResizeHandle>
            
            <Panel defaultSize={30} minSize={20} maxSize={50} className="bg-surface border-l border-border-light shadow-lg z-10">
                <div className="h-full flex flex-col">
                    <ChatWindow />
                </div>
            </Panel>
          </PanelGroup>
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
        window.addEventListener('chat-navigate', handleNavigation as EventListener)
        return () => {
            window.removeEventListener('chat-navigate', handleNavigation as EventListener)
        }
    }, [navigate])
}

// Wrapper component to use the hook
function LayoutWithNavigation() {
    useNavigationListener()
    return <Layout />
}

export default Layout

