import { AlertCircle, X } from 'lucide-react'
import { motion } from 'framer-motion'
import GlassCard from './GlassCard'
import { clsx } from 'clsx'

interface ErrorMessageProps {
  message: string
  onDismiss?: () => void
  retry?: () => void
  className?: string
}

export default function ErrorMessage({
  message,
  onDismiss,
  retry,
  className = '',
}: ErrorMessageProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={clsx('mb-4', className)}
    >
      <GlassCard className="p-4 border border-accent-error/20 bg-accent-error/10">
        <div className="flex items-start gap-3">
          <AlertCircle size={20} className="text-accent-error shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-accent-error font-medium">{message}</p>
            {retry && (
              <button
                onClick={retry}
                className="mt-2 text-xs text-accent-error hover:text-accent-error-hover underline"
              >
                Try again
              </button>
            )}
          </div>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="p-1 hover:bg-white/10 rounded transition-colors shrink-0"
            >
              <X size={16} className="text-text-tertiary" />
            </button>
          )}
        </div>
      </GlassCard>
    </motion.div>
  )
}

