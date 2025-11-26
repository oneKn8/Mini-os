import { useEffect, useState } from 'react'
import { 
  BarChart3, 
  Zap, 
  Globe, 
  Activity, 
  CheckCircle2,
  TrendingUp,
  Clock
} from 'lucide-react'
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie
} from 'recharts'
import { fetchDashboardStats, DashboardStats } from '../api/dashboard'
import GlassCard from '../components/UI/GlassCard'

const COLORS = ['#4c6ef5', '#7950f2', '#12b886', '#fab005', '#f03e3e']

export default function DashboardView() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
    const interval = setInterval(loadStats, 30000) // Poll every 30s
    return () => clearInterval(interval)
  }, [])

  const loadStats = async () => {
    try {
      const data = await fetchDashboardStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load dashboard stats:', error)
    } finally {
      setLoading(false)
    }
  }

  // Prepare chart data
  const importanceData = stats ? Object.entries(stats.items_by_importance).map(([name, value]) => ({ name, value })) : []
  const agentRunData = stats?.agent_stats.recent_runs.map(run => ({
    time: new Date(run.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    duration: run.duration_ms,
    status: run.status
  })).reverse() || []

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-16 w-16 animate-spin rounded-full border-4 border-accent-primary border-t-transparent"></div>
      </div>
    )
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const StatCard = ({ title, value, icon: Icon, trend, color }: any) => (
    <GlassCard className="p-6 flex flex-col justify-between h-32" hoverEffect>
      <div className="flex justify-between items-start">
        <div className={`p-2 rounded-lg bg-${color}/10 text-${color}`}>
          <Icon size={24} className={`text-${color}`} />
        </div>
        {trend && (
          <div className="flex items-center gap-1 text-xs font-medium text-accent-success bg-accent-success/10 px-2 py-1 rounded-full">
            <TrendingUp size={12} />
            {trend}
          </div>
        )}
      </div>
      <div>
        <div className="text-3xl font-bold text-white tracking-tight">{value}</div>
        <div className="text-xs text-text-tertiary uppercase tracking-wider font-medium mt-1">{title}</div>
      </div>
    </GlassCard>
  )

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold text-white tracking-tight mb-2 text-glow">Command Center</h1>
          <p className="text-text-secondary">System Status: <span className="text-accent-success font-medium">Operational</span></p>
        </div>
        <div className="flex items-center gap-2 text-sm text-text-tertiary bg-surface/50 px-3 py-1.5 rounded-full border border-white/5">
          <div className="w-2 h-2 rounded-full bg-accent-success animate-pulse"></div>
          Live Updates
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Items" 
          value={stats?.total_items || 0} 
          icon={BarChart3} 
          color="accent-primary"
          trend="+12%" 
        />
        <StatCard 
          title="Pending Actions" 
          value={stats?.pending_actions || 0} 
          icon={Zap} 
          color="accent-warning"
        />
        <StatCard 
          title="Agent Success" 
          value={`${stats?.agent_stats.success_rate || 0}%`} 
          icon={Activity} 
          color="accent-success"
          trend="+5%"
        />
        <StatCard 
          title="Connected Accounts" 
          value={stats?.connected_accounts || 0} 
          icon={Globe} 
          color="accent-info"
        />
      </div>

      {/* Main Charts Area - Bento Grid Style */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Agent Performance (Wide) */}
        <GlassCard className="lg:col-span-2 p-6 min-h-[400px] flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-white">Agent Runtime Performance</h3>
            <button className="text-xs text-accent-primary hover:text-white transition-colors">View Logs</button>
          </div>
          <div className="flex-1 w-full min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={agentRunData}>
                <defs>
                  <linearGradient id="colorDuration" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4c6ef5" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#4c6ef5" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="time" stroke="#606060" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#606060" fontSize={10} tickLine={false} axisLine={false} unit="ms" />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(10,10,10,0.9)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', backdropFilter: 'blur(10px)' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="duration" 
                  stroke="#4c6ef5" 
                  strokeWidth={3}
                  fillOpacity={1} 
                  fill="url(#colorDuration)" 
                  animationDuration={1500}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Items by Importance (Side) */}
        <GlassCard className="p-6 min-h-[400px] flex flex-col">
           <h3 className="text-lg font-bold text-white mb-2">Priority Distribution</h3>
           <div className="flex-1 relative">
             <ResponsiveContainer width="100%" height="100%">
               <PieChart>
                 <Pie
                   data={importanceData}
                   cx="50%"
                   cy="50%"
                   innerRadius={60}
                   outerRadius={100}
                   paddingAngle={5}
                   dataKey="value"
                   stroke="none"
                 >
                   {importanceData.map((entry, index) => (
                     <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                   ))}
                 </Pie>
                 <Tooltip 
                    contentStyle={{ backgroundColor: 'rgba(10,10,10,0.9)', borderRadius: '8px', border: 'none' }}
                 />
               </PieChart>
             </ResponsiveContainer>
             {/* Center Label */}
             <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
               <span className="text-3xl font-bold text-white">{stats?.total_items}</span>
               <span className="text-xs text-text-tertiary uppercase">Items</span>
             </div>
           </div>
           
           {/* Custom Legend */}
           <div className="grid grid-cols-2 gap-2 mt-4">
             {importanceData.map((entry, index) => (
               <div key={entry.name} className="flex items-center gap-2 text-xs text-text-secondary">
                 <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                 <span className="capitalize">{entry.name || 'Unassigned'}</span>
               </div>
             ))}
           </div>
        </GlassCard>

        {/* Recent Syncs (Bottom Wide) */}
        <GlassCard className="lg:col-span-3 p-6">
          <div className="flex items-center gap-2 mb-6">
             <Activity size={20} className="text-accent-secondary" />
             <h3 className="text-lg font-bold text-white">Recent Activity Stream</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats?.recent_sync_activity.slice(0, 4).map((activity) => (
              <div key={activity.id} className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                 <div className={`p-2 rounded-full ${
                   activity.status === 'success' ? 'bg-accent-success/20 text-accent-success' : 'bg-accent-error/20 text-accent-error'
                 }`}>
                   <CheckCircle2 size={16} />
                 </div>
                 <div>
                   <div className="text-sm font-medium text-white capitalize">{activity.context.replace('_', ' ')}</div>
                   <div className="text-xs text-text-tertiary flex items-center gap-1">
                     <Clock size={10} />
                     {new Date(activity.created_at).toLocaleTimeString()}
                   </div>
                 </div>
              </div>
            ))}
            {stats?.recent_sync_activity.length === 0 && (
              <div className="col-span-full text-center text-text-tertiary text-sm py-4">No recent activity</div>
            )}
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
