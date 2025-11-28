import { motion, AnimatePresence } from 'framer-motion'
import { Clock, RotateCcw, X, Check, AlertCircle, Calendar, Mail, Send, MapPin, Zap } from 'lucide-react'
import { useScreenController } from '../store/screenController'

interface ActivityLogProps {
  isOpen: boolean
  onClose: () => void
}

export function ActivityLog({ isOpen, onClose }: ActivityLogProps) {
  const { activityLog, canUndo, undo, clearActivityLog } = useScreenController()

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'create_calendar_event':
        return <Calendar size={12} />
      case 'create_email_draft':
        return <Mail size={12} />
      case 'send_email':
        return <Send size={12} />
      case 'set_location':
        return <MapPin size={12} />
      default:
        return <Zap size={12} />
    }
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return date.toLocaleDateString()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40"
            onClick={onClose}
          />
          
          {/* Panel */}
          <motion.div
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 bottom-0 w-80 bg-zinc-950 border-l border-zinc-800/50 z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800/50">
              <div className="flex items-center gap-2">
                <Clock size={16} className="text-zinc-500" />
                <span className="text-sm font-medium text-zinc-300">Activity Log</span>
              </div>
              <button
                onClick={onClose}
                className="p-1 text-zinc-600 hover:text-zinc-400 transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {/* Undo button */}
            {canUndo && (
              <div className="px-4 py-2 border-b border-zinc-800/50">
                <button
                  onClick={undo}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 
                           bg-zinc-800/50 border border-zinc-700/50 rounded-lg 
                           text-zinc-300 hover:bg-zinc-700/50 transition-colors text-sm"
                >
                  <RotateCcw size={14} />
                  Undo Last Action
                </button>
              </div>
            )}

            {/* Activity list */}
            <div className="flex-1 overflow-y-auto">
              {activityLog.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-zinc-600">
                  <Clock size={24} className="mb-2 opacity-50" />
                  <span className="text-sm">No activity yet</span>
                </div>
              ) : (
                <div className="p-3 space-y-2">
                  {activityLog.map((action) => (
                    <div
                      key={action.id}
                      className="flex items-start gap-3 p-3 rounded-lg bg-zinc-900/50 border border-zinc-800/50"
                    >
                      <span className="text-lg">{getActionIcon(action.type)}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-zinc-300 truncate">{action.description}</p>
                        <p className="text-xs text-zinc-600 mt-0.5">{formatTime(action.timestamp)}</p>
                      </div>
                      {action.undoFn ? (
                        <Check size={14} className="text-emerald-500/60 mt-1" />
                      ) : (
                        <AlertCircle size={14} className="text-amber-500/60 mt-1" />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            {activityLog.length > 0 && (
              <div className="px-4 py-3 border-t border-zinc-800/50">
                <button
                  onClick={clearActivityLog}
                  className="w-full text-xs text-zinc-600 hover:text-zinc-400 transition-colors"
                >
                  Clear history
                </button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default ActivityLog

