import { useState, useEffect } from 'react'
import { Mail, Calendar, Moon, Globe, Cpu, LogOut } from 'lucide-react'
import GlassCard from '../components/UI/GlassCard'

interface ConnectedAccount {
  id: string
  provider: string
  provider_email?: string
  status: string
  last_sync_at?: string
}

interface Preferences {
  quiet_hours_enabled: boolean
  quiet_hours_start: string
  quiet_hours_end: string
  timezone: string
  ai_provider: string
  auto_sync_interval: string
}

export default function SettingsView() {
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([])
  const [preferences, setPreferences] = useState<Preferences>({
    quiet_hours_enabled: true,
    quiet_hours_start: '22:00',
    quiet_hours_end: '08:00',
    timezone: 'UTC-8',
    ai_provider: 'openai',
    auto_sync_interval: 'manual'
  })
  const [loading, setLoading] = useState<Record<string, boolean>>({})
  const [error, setError] = useState<string>('')

  useEffect(() => {
    fetchAccounts()
    fetchPreferences()
  }, [])

  const fetchAccounts = async () => {
    try {
      const response = await fetch('/api/accounts/connected')
      if (response.ok) {
        const data = await response.json()
        setAccounts(data)
      }
    } catch (err) {
      console.error('Failed to fetch accounts:', err)
    }
  }

  const fetchPreferences = async () => {
    try {
      const response = await fetch('/api/preferences')
      if (response.ok) {
        const data = await response.json()
        setPreferences(data)
      }
    } catch (err) {
      console.error('Failed to fetch preferences:', err)
    }
  }

  const connectAccount = async (provider: 'gmail' | 'calendar') => {
    setLoading({ ...loading, [provider]: true })
    setError('')
    try {
      const endpoint = provider === 'gmail' ? '/api/accounts/connect/gmail' : '/api/accounts/connect/calendar'
      const response = await fetch(endpoint, { method: 'POST' })
      
      if (response.ok) {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const data = await response.json()
        alert(`✅ Authorization started! A browser window should open shortly.`)
        
        setTimeout(async () => {
          await fetchAccounts()
          setLoading({ ...loading, [provider]: false })
        }, 3000)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || `Failed to connect ${provider}`)
        setLoading({ ...loading, [provider]: false })
      }
    } catch (err) {
      setError(`Failed to connect ${provider}: ${err}`)
      setLoading({ ...loading, [provider]: false })
    }
  }

  const updatePreferences = async (updates: Partial<Preferences>) => {
    try {
      const response = await fetch('/api/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })
      if (response.ok) {
        await fetchPreferences()
      }
    } catch (err) {
      console.error('Failed to update preferences:', err)
    }
  }

  const isConnected = (provider: string) => {
    return accounts.some(acc => acc.provider === provider && acc.status === 'active')
  }

  return (
    <div className="space-y-8 pb-20 max-w-5xl mx-auto">
      <h1 className="text-4xl font-bold text-white text-glow mb-8">System Configuration</h1>

      {error && (
        <div className="rounded-xl bg-accent-error/10 border border-accent-error/20 p-4 text-accent-error text-sm flex items-center gap-2">
           <Shield size={16} />
           {error}
        </div>
      )}

      <div className="grid gap-8 md:grid-cols-2">
        
        {/* Connected Accounts */}
        <GlassCard className="p-8 flex flex-col gap-6" variant="dark">
           <div className="flex items-center gap-3 mb-2">
             <div className="p-2 rounded-lg bg-accent-primary/20 text-accent-primary"><Globe size={24} /></div>
             <div>
               <h2 className="text-xl font-bold text-white">Integrations</h2>
               <p className="text-sm text-text-tertiary">Manage external data sources</p>
             </div>
           </div>

           <div className="space-y-4">
             {[
               { name: 'Gmail', key: 'gmail', icon: Mail },
               { name: 'Google Calendar', key: 'google_calendar', icon: Calendar }
             ].map((account) => {
               const connected = isConnected(account.key)
               const isLoading = loading[account.key as 'gmail' | 'calendar']
               const accountData = accounts.find(acc => acc.provider === account.key)

               return (
                 <div key={account.key} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                   <div className="flex items-center gap-4">
                     <div className={`p-2 rounded-full ${connected ? 'bg-accent-success/20 text-accent-success' : 'bg-text-tertiary/20 text-text-tertiary'}`}>
                       <account.icon size={20} />
                     </div>
                     <div>
                       <div className="font-bold text-white">{account.name}</div>
                       <div className="text-xs text-text-tertiary">
                         {connected ? (accountData?.provider_email || 'Connected') : 'Not connected'}
                       </div>
                     </div>
                   </div>
                   <button
                     onClick={() => connectAccount(account.key as 'gmail' | 'calendar')}
                     disabled={isLoading || connected}
                     className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                       connected 
                         ? 'bg-green-500/20 text-green-400 cursor-default' 
                         : 'bg-accent-primary hover:bg-accent-primary-hover text-white shadow-lg shadow-accent-primary/20'
                     }`}
                   >
                     {isLoading ? 'Syncing...' : connected ? 'Active' : 'Connect'}
                   </button>
                 </div>
               )
             })}
           </div>
        </GlassCard>

        {/* System Preferences */}
        <GlassCard className="p-8 flex flex-col gap-6" variant="dark">
           <div className="flex items-center gap-3 mb-2">
             <div className="p-2 rounded-lg bg-accent-secondary/20 text-accent-secondary"><Cpu size={24} /></div>
             <div>
               <h2 className="text-xl font-bold text-white">System Preferences</h2>
               <p className="text-sm text-text-tertiary">Configure agent behavior</p>
             </div>
           </div>

           <div className="space-y-6">
             {/* Quiet Hours Toggle */}
             <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
                <div className="flex items-center gap-3">
                   <Moon size={20} className="text-purple-400" />
                   <div>
                      <div className="font-bold text-white">Quiet Hours</div>
                      <div className="text-xs text-text-tertiary">Pause notifications ({preferences.quiet_hours_start} - {preferences.quiet_hours_end})</div>
                   </div>
                </div>
                <button
                  onClick={() => updatePreferences({ quiet_hours_enabled: !preferences.quiet_hours_enabled })}
                  className={`w-12 h-6 rounded-full transition-colors relative ${preferences.quiet_hours_enabled ? 'bg-accent-primary' : 'bg-white/20'}`}
                >
                  <div className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${preferences.quiet_hours_enabled ? 'translate-x-6' : ''}`} />
                </button>
             </div>

             {/* AI Model Selection */}
             <div>
               <label className="text-sm font-bold text-text-secondary mb-2 block">AI Provider</label>
               <select 
                 value={preferences.ai_provider}
                 onChange={(e) => updatePreferences({ ai_provider: e.target.value })}
                 className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-accent-primary outline-none appearance-none"
               >
                 <option value="openai">OpenAI (GPT-4o)</option>
                 <option value="nvidia">NVIDIA NIM (Llama 3)</option>
                 <option value="anthropic">Anthropic (Claude 3.5)</option>
               </select>
             </div>

             {/* Sync Interval */}
             <div>
               <label className="text-sm font-bold text-text-secondary mb-2 block">Sync Frequency</label>
               <div className="grid grid-cols-3 gap-2">
                 {['manual', '15', '60'].map((interval) => (
                   <button
                     key={interval}
                     onClick={() => updatePreferences({ auto_sync_interval: interval })}
                     className={`py-2 rounded-lg text-sm font-medium transition-all border ${
                       preferences.auto_sync_interval === interval
                         ? 'bg-accent-primary/20 border-accent-primary text-white'
                         : 'bg-transparent border-white/10 text-text-tertiary hover:bg-white/5'
                     }`}
                   >
                     {interval === 'manual' ? 'Manual' : `${interval}m`}
                   </button>
                 ))}
               </div>
             </div>
           </div>
        </GlassCard>

        {/* Danger Zone */}
        <GlassCard className="md:col-span-2 p-8 flex items-center justify-between" variant="dark">
           <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-red-500/10 text-red-500">
                <LogOut size={24} />
              </div>
              <div>
                <h3 className="font-bold text-white">Sign Out</h3>
                <p className="text-sm text-text-tertiary">End your current session</p>
              </div>
           </div>
           <button className="px-6 py-2 rounded-xl border border-red-500/50 text-red-500 hover:bg-red-500/10 transition-colors font-bold">
             Log Out
           </button>
        </GlassCard>

      </div>
    </div>
  )
}
