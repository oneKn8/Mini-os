import { motion, AnimatePresence } from 'framer-motion'
import { Check, X, Info, AlertTriangle } from 'lucide-react'
import { create } from 'zustand'

// Toast types
type ToastType = 'success' | 'error' | 'info' | 'warning'

interface Toast {
  id: string
  message: string
  type: ToastType
  duration?: number
}

// Toast store
interface ToastStore {
  toasts: Toast[]
  addToast: (message: string, type?: ToastType, duration?: number) => void
  removeToast: (id: string) => void
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (message, type = 'info', duration = 3000) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`
    set((state) => ({
      toasts: [...state.toasts, { id, message, type, duration }]
    }))
    
    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id)
        }))
      }, duration)
    }
  },
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id)
    }))
  }
}))

// Helper function for easy access
export const toast = {
  success: (message: string, duration?: number) => 
    useToastStore.getState().addToast(message, 'success', duration),
  error: (message: string, duration?: number) => 
    useToastStore.getState().addToast(message, 'error', duration),
  info: (message: string, duration?: number) => 
    useToastStore.getState().addToast(message, 'info', duration),
  warning: (message: string, duration?: number) => 
    useToastStore.getState().addToast(message, 'warning', duration),
}

// Icon map
const icons = {
  success: Check,
  error: X,
  info: Info,
  warning: AlertTriangle,
}

// Color map (minimal, muted)
const colors = {
  success: 'text-emerald-400/80',
  error: 'text-red-400/80',
  info: 'text-zinc-400',
  warning: 'text-amber-400/80',
}

// Individual Toast component
function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
  const Icon = icons[toast.type]
  const colorClass = colors[toast.type]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.95 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className="flex items-center gap-2 px-3 py-2 bg-zinc-900/90 backdrop-blur-sm 
                 border border-zinc-800/50 rounded-lg shadow-lg max-w-xs"
    >
      <Icon size={14} className={colorClass} />
      <span className="text-sm text-zinc-300">{toast.message}</span>
      <button
        onClick={onRemove}
        className="ml-auto p-0.5 text-zinc-600 hover:text-zinc-400 transition-colors"
      >
        <X size={12} />
      </button>
    </motion.div>
  )
}

// Toast Container - renders all toasts
export function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence mode="popLayout">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onRemove={() => removeToast(t.id)} />
        ))}
      </AnimatePresence>
    </div>
  )
}

export default ToastContainer

