import { motion } from 'framer-motion'
import { CheckCircle2, Loader2, Circle, AlertCircle } from 'lucide-react'
import { clsx } from 'clsx'
import { Thought } from '../../store/chatStore'

interface ProcessStepProps {
    thought: Thought
}

export default function ProcessStep({ thought }: ProcessStepProps) {
    const isRunning = thought.status === 'running'
    const isSuccess = thought.status === 'success'
    const isError = thought.status === 'error'

    return (
        <div className="flex items-start gap-3 py-2 group">
            <div className="mt-1 shrink-0">
                {isRunning && <Loader2 size={16} className="text-accent-primary animate-spin" />}
                {isSuccess && <CheckCircle2 size={16} className="text-accent-success" />}
                {isError && <AlertCircle size={16} className="text-accent-error" />}
                {!isRunning && !isSuccess && !isError && <Circle size={16} className="text-text-muted" />}
            </div>
            
            <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center gap-2">
                    <span className={clsx(
                        "text-sm font-medium capitalize",
                        isRunning ? "text-text-primary" : "text-text-secondary"
                    )}>
                        {thought.agent.replace(/_/g, ' ')}
                    </span>
                    {thought.duration_ms && (
                        <span className="text-xs text-text-tertiary font-mono">
                            {(thought.duration_ms / 1000).toFixed(2)}s
                        </span>
                    )}
                </div>

                {thought.log?.message && (
                    <p className="text-xs text-text-secondary">{thought.log.message}</p>
                )}

                {/* Summary Output */}
                {thought.summary && (
                    <motion.div 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="text-xs bg-bg-secondary/50 rounded p-2 border border-border-light mt-1 font-mono text-text-secondary overflow-x-auto"
                    >
                        {Object.entries(thought.summary).map(([key, value]) => (
                            <div key={key} className="flex gap-2">
                                <span className="text-text-tertiary">{key}:</span>
                                <span className="text-text-primary truncate">{String(value)}</span>
                            </div>
                        ))}
                    </motion.div>
                )}
            </div>
        </div>
    )
}

