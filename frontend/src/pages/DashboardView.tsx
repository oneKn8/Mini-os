import { useRef } from 'react'
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
import { useDashboardWithRealtime } from '../hooks/useDashboard'
import { useScreenUpdates } from '../store/screenController'
import { clsx } from 'clsx'

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444']

export default function DashboardView() {
  const { stats, isLoading } = useDashboardWithRealtime()
  const headerRef = useRef<HTMLDivElement>(null)
  const { isAgentFocused } = useScreenUpdates('/dashboard')

  const agentStats = stats?.agent_stats || {
    total_runs: 0,
    success_rate: 0,
    avg_duration_ms: 0,
    runs_by_agent: {},
    recent_runs: [],
  }

  // Prepare chart data
  const importanceData = stats
    ? Object.entries(stats.items_by_importance).map(([name, value]) => ({ name, value }))
    : []

  const agentRunData = agentStats.recent_runs
    .map(run => ({
      time: new Date(run.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      duration: run.duration_ms,
      status: run.status
    }))
    .reverse()

  if (isLoading && !stats) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-600 border-t-zinc-300"></div>
      </div>
    )
  }

  return (
    <div data-dashboard-page className="space-y-5 pb-16">
      {/* Header */}
      <div ref={headerRef} className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-medium text-zinc-200 mb-0.5">Dashboard</h1>
          <p className="text-xs text-zinc-600">
            System Status: <span className="text-emerald-500">Operational</span>
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-zinc-600 bg-zinc-900/50 px-2.5 py-1 rounded-full border border-zinc-800/50">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          Live
        </div>
      </div>

      {/* Stats Grid */}
      <div data-dashboard-stats className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          title="Total Items"
          value={stats?.total_items || 0}
          icon={BarChart3}
          trend="+12%"
          color="blue"
        />
        <StatCard
          title="Pending Actions"
          value={stats?.pending_actions || 0}
          icon={Zap}
          color="amber"
        />
        <StatCard
          title="Agent Success"
          value={`${stats?.agent_stats.success_rate || 0}%`}
          icon={Activity}
          trend="+5%"
          color="emerald"
        />
        <StatCard
          title="Connected"
          value={stats?.connected_accounts || 0}
          icon={Globe}
          color="violet"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Agent Performance */}
        <div
          data-dashboard-performance
          className={clsx(
            "lg:col-span-2 rounded-xl border bg-zinc-900/30 p-5",
            isAgentFocused ? "border-blue-500/30" : "border-zinc-800/50"
          )}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-zinc-300">Agent Performance</h3>
            <span className="text-[10px] text-zinc-600">Last 24h</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={agentRunData}>
                <defs>
                  <linearGradient id="colorDuration" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                <XAxis dataKey="time" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} unit="ms" />
                <Tooltip content={<ChartTooltip />} />
                <Area
                  type="monotone"
                  dataKey="duration"
                  stroke="#3b82f6"
                  strokeWidth={1.5}
                  fillOpacity={1}
                  fill="url(#colorDuration)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Priority Distribution */}
        <div className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-5">
          <h3 className="text-sm font-medium text-zinc-300 mb-4">Priority Distribution</h3>
          <div className="h-40 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={importanceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {importanceData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* Center Label */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-medium text-zinc-200">{stats?.total_items}</span>
              <span className="text-[10px] text-zinc-600 uppercase">Items</span>
            </div>
          </div>
          {/* Legend */}
          <div className="grid grid-cols-2 gap-1.5 mt-3">
            {importanceData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5 text-[10px] text-zinc-500">
                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                <span className="capitalize truncate">{entry.name || 'Unassigned'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div data-dashboard-activity className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Activity size={14} className="text-zinc-500" />
          <h3 className="text-sm font-medium text-zinc-300">Recent Activity</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
          {stats?.recent_sync_activity.slice(0, 4).map((activity) => (
            <div
              key={activity.id}
              className="flex items-center gap-2.5 p-3 rounded-lg bg-zinc-800/30 border border-zinc-800/30 hover:bg-zinc-800/50 transition-colors"
            >
              <div className={clsx(
                "p-1.5 rounded-full",
                activity.status === 'success' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'
              )}>
                <CheckCircle2 size={12} />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-medium text-zinc-300 capitalize truncate">
                  {activity.context.replace('_', ' ')}
                </div>
                <div className="text-[10px] text-zinc-600 flex items-center gap-1">
                  <Clock size={8} />
                  {new Date(activity.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          {(!stats?.recent_sync_activity || stats.recent_sync_activity.length === 0) && (
            <div className="col-span-full text-center text-zinc-600 text-xs py-6">No recent activity</div>
          )}
        </div>
      </div>
    </div>
  )
}

// Stat Card Component
function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  color
}: {
  title: string
  value: number | string
  icon: React.ElementType
  trend?: string
  color: 'blue' | 'amber' | 'emerald' | 'violet'
}) {
  const colors = {
    blue: 'text-blue-400 bg-blue-500/10',
    amber: 'text-amber-400 bg-amber-500/10',
    emerald: 'text-emerald-400 bg-emerald-500/10',
    violet: 'text-violet-400 bg-violet-500/10',
  }

  return (
    <div className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-4 flex flex-col justify-between min-h-[100px] hover:bg-zinc-800/20 transition-colors">
      <div className="flex justify-between items-start">
        <div className={clsx("p-1.5 rounded-lg", colors[color])}>
          <Icon size={14} />
        </div>
        {trend && (
          <div className="flex items-center gap-0.5 text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
            <TrendingUp size={10} />
            {trend}
          </div>
        )}
      </div>
      <div>
        <div className="text-xl font-medium text-zinc-200">{value}</div>
        <div className="text-[10px] text-zinc-600 uppercase tracking-wide mt-0.5">{title}</div>
      </div>
    </div>
  )
}

// Chart Tooltip
function ChartTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs">
      {payload.map((item: any, index: number) => (
        <div key={index} className="text-zinc-300">
          {item.name}: <span className="text-zinc-100 font-medium">{item.value}</span>
        </div>
      ))}
    </div>
  )
}
