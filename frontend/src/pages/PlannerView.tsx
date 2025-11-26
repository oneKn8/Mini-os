import { Calendar, ArrowLeft, ArrowRight, Clock, AlertCircle } from 'lucide-react'

function PlannerView() {
  return (
    <div className="space-y-8 fade-in pb-20">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-text-primary">Weekly Planner</h1>
        <div className="flex items-center gap-2 bg-surface p-1 rounded-lg border border-border-light shadow-sm">
          <button className="p-2 rounded-md hover:bg-bg-secondary text-text-secondary transition-colors">
            <ArrowLeft size={20} />
          </button>
          <span className="px-4 text-sm font-medium text-text-primary">This Week</span>
          <button className="p-2 rounded-md hover:bg-bg-secondary text-text-secondary transition-colors">
            <ArrowRight size={20} />
          </button>
        </div>
      </div>

      <div className="relative overflow-hidden rounded-3xl bg-surface border border-border-light shadow-sm p-12 text-center">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 h-64 w-64 rounded-full bg-accent-primary/5 blur-3xl"></div>
        <div className="absolute bottom-0 left-0 -mb-10 -ml-10 h-48 w-48 rounded-full bg-accent-secondary/5 blur-3xl"></div>
        
        <div className="relative z-10 flex flex-col items-center">
            <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-bg-secondary text-accent-primary shadow-inner">
                <Calendar size={40} />
            </div>
            
            <h2 className="text-2xl font-bold text-text-primary mb-3">Weekly Planning Coming Soon</h2>
            <p className="text-text-secondary max-w-md mb-8 text-lg">
                We're building a powerful drag-and-drop calendar to help you organize your week efficiently.
            </p>
            
            <div className="grid gap-4 text-left max-w-sm w-full">
                {[
                    "Week-view calendar with time blocks",
                    "Drag-and-drop scheduling",
                    "Weekly goals and focus areas",
                    "Time analytics and insights"
                ].map((feature, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-bg-secondary/50 border border-border-light">
                        <div className="h-2 w-2 rounded-full bg-accent-primary"></div>
                        <span className="text-text-secondary">{feature}</span>
                    </div>
                ))}
            </div>
        </div>
      </div>
    </div>
  )
}

export default PlannerView
