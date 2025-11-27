import { Search } from 'lucide-react'
import GlassCard from '../UI/GlassCard'
import { clsx } from 'clsx'

interface EmailFiltersProps {
  filter: string
  onFilterChange: (filter: string) => void
  searchQuery: string
  onSearchChange: (query: string) => void
}

export default function EmailFilters({
  filter,
  onFilterChange,
  searchQuery,
  onSearchChange,
}: EmailFiltersProps) {
  return (
    <GlassCard className="p-2 flex gap-2 items-center" noBorder>
      <div className="relative flex-1">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
        <input 
          type="text" 
          placeholder="Search messages..." 
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full bg-black/20 border border-white/5 rounded-xl pl-10 pr-4 py-2.5 text-sm text-text-primary focus:outline-none focus:border-accent-primary/50 transition-colors placeholder-text-muted"
        />
      </div>
      <div className="h-8 w-[1px] bg-white/10 mx-1" />
      {['all', 'work', 'personal', 'finance'].map(f => (
        <button 
          key={f}
          onClick={() => onFilterChange(f)}
          className={clsx(
            "px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all",
            filter === f 
              ? "bg-accent-primary text-white shadow-lg shadow-accent-primary/20" 
              : "text-text-secondary hover:bg-white/5"
          )}
        >
          {f}
        </button>
      ))}
    </GlassCard>
  )
}

