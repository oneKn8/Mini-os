import { useEffect, useState } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { Sun, Calendar, Clock, CheckCircle2, Sparkles, Zap, Coffee, Users, Target, Layers } from 'lucide-react'
import { clsx } from 'clsx'

interface TimeBlock {
  id: string
  time: string
  title: string
  type: "focus" | "meeting" | "break" | "task"
  duration: number
  completed?: boolean
}

interface DailyPlan {
  date: string
  summary: string
  priorities: string[]
  time_blocks: TimeBlock[]
  weather?: {
    temp: number
    condition: string
    icon: string
  }
}

export default function TodayView() {
  const [plan, setPlan] = useState<DailyPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [currentTime, setCurrentTime] = useState(new Date())
  
  const { scrollY } = useScroll()
  const headerY = useTransform(scrollY, [0, 200], [0, 50])
  const headerOpacity = useTransform(scrollY, [0, 200], [1, 0.8])

  useEffect(() => {
    fetchDailyPlan()
    const timer = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

  const fetchDailyPlan = async () => {
    try {
      const response = await fetch('/api/planner/today')
      if (response.ok) {
        const data = await response.json()
        setPlan(data)
      }
    } catch (error) {
      console.error('Failed to fetch daily plan:', error)
    } finally {
      setLoading(false)
    }
  }

  const getGreeting = () => {
    const hour = currentTime.getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 18) return 'Good afternoon'
    return 'Good evening'
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "focus": return <Target size={16} className="text-accent-primary" />
      case "meeting": return <Users size={16} className="text-accent-secondary" />
      case "break": return <Coffee size={16} className="text-accent-info" />
      case "task": return <CheckCircle2 size={16} className="text-accent-success" />
      default: return <Clock size={16} className="text-text-tertiary" />
    }
  }
  
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }
  
  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  }

  if (loading) {
    return (
      <div className="flex h-[60vh] w-full items-center justify-center">
        <div className="flex flex-col items-center gap-4">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-border-light border-t-accent-primary"></div>
            <p className="text-text-secondary animate-pulse">Planning your day...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 pb-20">
        {/* Hero Section */}
        <motion.div 
            style={{ y: headerY, opacity: headerOpacity }}
            className="relative overflow-hidden rounded-3xl bg-surface p-8 shadow-sm border border-border-light"
        >
             <div className="absolute top-0 right-0 -mt-10 -mr-10 h-64 w-64 rounded-full bg-accent-primary/5 blur-3xl"></div>
             <div className="absolute bottom-0 left-0 -mb-10 -ml-10 h-48 w-48 rounded-full bg-accent-secondary/5 blur-3xl"></div>
             
             <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                 <div>
                     <div className="flex items-center gap-2 text-accent-primary mb-2">
                         <Sparkles size={18} />
                         <span className="text-sm font-semibold uppercase tracking-wider">Daily Overview</span>
                     </div>
                     <h1 className="text-4xl font-bold tracking-tight text-text-primary mb-2">
                         {getGreeting()}, Sparkle
                     </h1>
                     <p className="text-text-secondary text-lg">
                         {currentTime.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                     </p>
                 </div>

                 {plan?.weather && (
                    <div className="flex items-center gap-4 rounded-2xl bg-bg-secondary/50 p-4 backdrop-blur-sm border border-border-light">
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface shadow-sm text-accent-warning">
                            <Sun size={24} />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-text-primary">{plan.weather.temp}°</div>
                            <div className="text-sm text-text-secondary capitalize">{plan.weather.condition}</div>
                        </div>
                    </div>
                 )}
             </div>

             {plan?.summary && (
                 <div className="mt-8 max-w-2xl">
                     <p className="text-text-secondary leading-relaxed border-l-2 border-accent-primary/30 pl-4">
                         {plan.summary}
                     </p>
                 </div>
             )}
        </motion.div>

        {/* Priorities */}
        {plan?.priorities && plan.priorities.length > 0 && (
            <motion.div 
                variants={container}
                initial="hidden"
                animate="show"
            >
                <div className="flex items-center gap-2 mb-4 px-1">
                    <Zap size={20} className="text-accent-warning" />
                    <h2 className="text-lg font-semibold text-text-primary">Top Priorities</h2>
                </div>
                
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    {plan.priorities.map((priority, idx) => (
                        <motion.div
                            key={idx}
                            variants={item}
                            whileHover={{ y: -4 }}
                            className="group relative overflow-hidden rounded-2xl bg-surface p-5 shadow-sm border border-border-light hover:shadow-md transition-all"
                        >
                            <div className="absolute top-0 right-0 h-20 w-20 translate-x-10 -translate-y-10 rounded-full bg-accent-primary/5 group-hover:bg-accent-primary/10 transition-colors"></div>
                            
                            <div className="relative z-10">
                                <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg bg-accent-primary/10 text-accent-primary font-bold text-sm">
                                    {idx + 1}
                                </div>
                                <p className="font-medium text-text-primary line-clamp-2">{priority}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </motion.div>
        )}

        {/* Schedule */}
        {plan?.time_blocks && plan.time_blocks.length > 0 ? (
             <motion.div 
                variants={container}
                initial="hidden"
                animate="show"
                className="space-y-4"
            >
                <div className="flex items-center gap-2 mb-4 px-1 pt-4">
                    <Calendar size={20} className="text-accent-primary" />
                    <h2 className="text-lg font-semibold text-text-primary">Today's Schedule</h2>
                </div>

                <div className="relative space-y-0">
                    {/* Timeline line */}
                    <div className="absolute left-8 top-4 bottom-4 w-px bg-border-medium/50 hidden md:block"></div>

                    {plan.time_blocks.map((block) => (
                        <motion.div
                            key={block.id}
                            variants={item}
                            className="group relative flex flex-col md:flex-row gap-4 rounded-xl hover:bg-surface p-3 transition-colors"
                        >
                            {/* Time Column */}
                            <div className="md:w-32 flex md:flex-col items-center md:items-end justify-start pt-1 md:pr-8 z-10">
                                <span className="text-sm font-semibold text-text-primary font-mono">{block.time}</span>
                                <span className="text-xs text-text-tertiary ml-2 md:ml-0">{block.duration}m</span>
                                
                                {/* Timeline dot */}
                                <div className={clsx(
                                    "hidden md:block absolute right-[-5px] w-2.5 h-2.5 rounded-full border-2 border-bg-secondary mt-1.5",
                                    block.completed ? "bg-accent-success" : "bg-accent-primary"
                                )}></div>
                            </div>

                            {/* Content Card */}
                            <div className={clsx(
                                "flex-1 rounded-xl border p-4 transition-all",
                                block.completed 
                                    ? "bg-surface/50 border-border-light opacity-60" 
                                    : "bg-surface border-border-light shadow-sm group-hover:border-accent-primary/30"
                            )}>
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex items-start gap-3">
                                        <div className={clsx(
                                            "p-2 rounded-lg shrink-0",
                                            "bg-bg-secondary"
                                        )}>
                                            {getTypeIcon(block.type)}
                                        </div>
                                        <div>
                                            <h3 className={clsx(
                                                "font-semibold text-text-primary",
                                                block.completed && "line-through"
                                            )}>{block.title}</h3>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className={clsx(
                                                    "text-xs px-2 py-0.5 rounded-full font-medium capitalize",
                                                    block.type === 'focus' && "bg-accent-primary/10 text-accent-primary",
                                                    block.type === 'meeting' && "bg-accent-secondary/10 text-accent-secondary",
                                                    block.type === 'break' && "bg-accent-info/10 text-accent-info",
                                                    block.type === 'task' && "bg-accent-success/10 text-accent-success"
                                                )}>
                                                    {block.type}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    {block.completed && (
                                        <div className="text-accent-success">
                                            <CheckCircle2 size={20} />
                                        </div>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </motion.div>
        ) : (
            !plan && (
                <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-border-dark/30 bg-surface/50 p-12 text-center">
                    <div className="mb-4 rounded-full bg-bg-secondary p-4">
                        <Layers size={32} className="text-text-tertiary" />
                    </div>
                    <h3 className="text-lg font-semibold text-text-primary">No plan for today yet</h3>
                    <p className="mt-2 text-text-secondary max-w-sm">
                        Ask the assistant to generate your daily schedule based on your tasks and meetings.
                    </p>
                </div>
            )
        )}
    </div>
  )
}
