import { motion } from 'framer-motion'
import { CheckCircle2, Circle, Clock, Target } from 'lucide-react'
import { useState } from 'react'
import { clsx } from 'clsx'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface PlanChecklistProps {
    plan: {
        must_do_today?: string[]
        focus_areas?: string[]
        time_recommendations?: Array<{
            task: string
            suggested_time: string
            duration_minutes: number
        }>
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onPlanUpdate?: (updatedPlan: any) => void
}

export default function PlanChecklist({ plan, onPlanUpdate }: PlanChecklistProps) {
    const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set())
    const [mustDoItems, setMustDoItems] = useState<string[]>(plan.must_do_today || [])
    const [focusAreas, setFocusAreas] = useState<string[]>(plan.focus_areas || [])
    const [timeRecs, setTimeRecs] = useState(plan.time_recommendations || [])

    const toggleItem = (index: number) => {
        const newChecked = new Set(checkedItems)
        if (newChecked.has(index)) {
            newChecked.delete(index)
        } else {
            newChecked.add(index)
        }
        setCheckedItems(newChecked)
    }

    const toggleTimeRec = (index: number) => {
        const newRecs = [...timeRecs]
        newRecs[index] = {
            ...newRecs[index],
            // Toggle completion status if we track it
        }
        setTimeRecs(newRecs)
        if (onPlanUpdate) {
            onPlanUpdate({
                must_do_today: mustDoItems,
                focus_areas: focusAreas,
                time_recommendations: newRecs
            })
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-border-light bg-surface shadow-sm overflow-hidden my-3"
        >
            <div className="bg-bg-secondary/50 px-4 py-3 border-b border-border-light">
                <div className="flex items-center gap-2">
                    <Target size={18} className="text-accent-primary" />
                    <h3 className="text-sm font-semibold text-text-primary">Daily Plan</h3>
                </div>
            </div>

            <div className="p-4 space-y-4">
                {/* Must-Do Items */}
                {mustDoItems.length > 0 && (
                    <div>
                        <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
                            Must-Do Today
                        </h4>
                        <div className="space-y-2">
                            {mustDoItems.map((item, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, x: -5 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    className="flex items-start gap-3 p-2 rounded-lg hover:bg-bg-secondary transition-colors cursor-pointer"
                                    onClick={() => toggleItem(index)}
                                >
                                    {checkedItems.has(index) ? (
                                        <CheckCircle2 size={18} className="text-accent-success mt-0.5 shrink-0" />
                                    ) : (
                                        <Circle size={18} className="text-text-tertiary mt-0.5 shrink-0" />
                                    )}
                                    <span className={clsx(
                                        "text-sm flex-1",
                                        checkedItems.has(index) ? "text-text-tertiary line-through" : "text-text-primary"
                                    )}>
                                        {item}
                                    </span>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Focus Areas */}
                {focusAreas.length > 0 && (
                    <div>
                        <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
                            Focus Areas
                        </h4>
                        <div className="flex flex-wrap gap-2">
                            {focusAreas.map((area, index) => (
                                <motion.span
                                    key={index}
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: index * 0.05 }}
                                    className="px-3 py-1 rounded-full bg-accent-primary/10 text-accent-primary text-xs font-medium"
                                >
                                    {area}
                                </motion.span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Time Recommendations */}
                {timeRecs.length > 0 && (
                    <div>
                        <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
                            Suggested Time Blocks
                        </h4>
                        <div className="space-y-2">
                            {timeRecs.map((rec, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, x: -5 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    className="flex items-center gap-3 p-2 rounded-lg border border-border-light hover:bg-bg-secondary transition-colors"
                                >
                                    <Clock size={16} className="text-text-tertiary shrink-0" />
                                    <div className="flex-1">
                                        <div className="text-sm font-medium text-text-primary">{rec.task}</div>
                                        <div className="text-xs text-text-tertiary">
                                            {rec.suggested_time} • {rec.duration_minutes} min
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => toggleTimeRec(index)}
                                        className="p-1 rounded text-text-tertiary hover:text-accent-primary hover:bg-accent-primary/10 transition-colors"
                                        title="Toggle completion"
                                    >
                                        {checkedItems.has(mustDoItems.length + index) ? (
                                            <CheckCircle2 size={16} className="text-accent-success" />
                                        ) : (
                                            <Circle size={16} />
                                        )}
                                    </button>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    )
}

