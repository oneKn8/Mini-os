import { useState, useEffect } from 'react'
import { Mail, Calendar, Moon, Globe, Cpu, LogOut, Shield, Sparkles, Mouse, MessageSquare, Eye, Zap, Trash2, X } from 'lucide-react'
import GlassCard from '../components/UI/GlassCard'
import { useChatStore } from '../store/chatStore'
import { useSettingsStore } from '../store/settingsStore'

const AVAILABLE_MODELS = [
    // OpenAI Models
    { id: 'gpt-5', name: 'GPT-5', provider: 'openai' },
    { id: 'gpt-5-mini', name: 'GPT-5 Mini', provider: 'openai' },
    { id: 'gpt-5-nano', name: 'GPT-5 Nano', provider: 'openai' },
    { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai' },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai' },
    // NVIDIA NIM Models
    { id: 'meta/llama-3.1-70b-instruct', name: 'Llama 3.1 70B (NVIDIA)', provider: 'nvidia' },
    { id: 'meta/llama-3.1-8b-instruct', name: 'Llama 3.1 8B (NVIDIA)', provider: 'nvidia' },
    { id: 'mistralai/mistral-large', name: 'Mistral Large (NVIDIA)', provider: 'nvidia' },
    { id: 'google/gemma-2-9b-it', name: 'Gemma 2 9B (NVIDIA)', provider: 'nvidia' },
]

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

// Toggle switch component (minimal design)
function Toggle({ 
  enabled, 
  onChange, 
  size = 'md' 
}: { 
  enabled: boolean
  onChange: (enabled: boolean) => void
  size?: 'sm' | 'md'
}) {
  const sizeClasses = size === 'sm' 
    ? 'w-9 h-5' 
    : 'w-11 h-6'
  const dotSizeClasses = size === 'sm'
    ? 'w-3 h-3 top-1 left-1'
    : 'w-4 h-4 top-1 left-1'
  const translateClass = size === 'sm' ? 'translate-x-4' : 'translate-x-5'

  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`${sizeClasses} rounded-full transition-colors relative border border-zinc-700/50 ${
        enabled ? 'bg-blue-500/30' : 'bg-zinc-800/50'
      }`}
    >
      <div 
        className={`absolute ${dotSizeClasses} rounded-full transition-transform ${
          enabled ? `${translateClass} bg-blue-400` : 'bg-zinc-500'
        }`} 
      />
    </button>
  )
}

export default function SettingsView() {
  const { selectedModel, setModel } = useChatStore()
  const settings = useSettingsStore()
  
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
        alert('Authorization started! A browser window should open shortly.')
        
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

  const actionTypeLabels: Record<string, string> = {
    create_email_draft: 'Email drafts',
    create_calendar_event: 'Calendar events',
    send_email: 'Sending emails',
  }

  return (
    <div className="space-y-6 pb-20 max-w-5xl mx-auto relative z-10">
      <h1 className="text-2xl font-medium text-white mb-6">Settings</h1>

      {error && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-red-400 text-sm flex items-center gap-2">
           <Shield size={14} />
           {error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        
        {/* Agent Visual Settings */}
        <GlassCard className="p-6 flex flex-col gap-5" variant="dark">
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 rounded-lg bg-violet-500/10 text-violet-400"><Eye size={18} /></div>
            <div>
              <h2 className="text-base font-medium text-white">Agent Visuals</h2>
              <p className="text-xs text-zinc-500">Control how the agent appears</p>
            </div>
          </div>

          <div className="space-y-4">
            {/* Agent Cursor */}
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-3">
                <Mouse size={16} className="text-zinc-500" />
                <div>
                  <div className="text-sm text-zinc-300">Agent Cursor</div>
                  <div className="text-xs text-zinc-600">Glowing cursor showing where agent looks</div>
                </div>
              </div>
              <Toggle 
                enabled={settings.agentCursor} 
                onChange={(v) => settings.updateSetting('agentCursor', v)} 
              />
            </div>

            {/* Thought Bubbles */}
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-3">
                <MessageSquare size={16} className="text-zinc-500" />
                <div>
                  <div className="text-sm text-zinc-300">Thought Bubbles</div>
                  <div className="text-xs text-zinc-600">Show agent's reasoning</div>
                </div>
              </div>
              <Toggle 
                enabled={settings.thoughtBubbles} 
                onChange={(v) => settings.updateSetting('thoughtBubbles', v)} 
              />
            </div>

            {/* Confetti */}
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-3">
                <Sparkles size={16} className="text-zinc-500" />
                <div>
                  <div className="text-sm text-zinc-300">Confetti Effects</div>
                  <div className="text-xs text-zinc-600">Celebrate completed actions</div>
                </div>
              </div>
              <Toggle 
                enabled={settings.confettiEnabled} 
                onChange={(v) => settings.updateSetting('confettiEnabled', v)} 
              />
            </div>

            {/* Reduced Motion */}
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-3">
                <Zap size={16} className="text-zinc-500" />
                <div>
                  <div className="text-sm text-zinc-300">Reduced Motion</div>
                  <div className="text-xs text-zinc-600">Minimize animations</div>
                </div>
              </div>
              <Toggle 
                enabled={settings.reducedMotion} 
                onChange={(v) => settings.updateSetting('reducedMotion', v)} 
              />
            </div>

            {/* Agent Speed */}
            <div className="pt-2">
              <label className="text-xs font-medium text-zinc-500 mb-2 block">Animation Speed</label>
              <div className="grid grid-cols-4 gap-2">
                {(['slow', 'normal', 'fast', 'instant'] as const).map((speed) => (
                  <button
                    key={speed}
                    onClick={() => settings.updateSetting('agentSpeed', speed)}
                    className={`py-1.5 rounded-lg text-xs transition-all border ${
                      settings.agentSpeed === speed
                        ? 'bg-zinc-800 border-zinc-600 text-white'
                        : 'bg-transparent border-zinc-800 text-zinc-500 hover:bg-zinc-800/50'
                    }`}
                  >
                    {speed.charAt(0).toUpperCase() + speed.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </GlassCard>

        {/* Agent Approval Settings */}
        <GlassCard className="p-6 flex flex-col gap-5" variant="dark">
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400"><Shield size={18} /></div>
            <div>
              <h2 className="text-base font-medium text-white">Agent Permissions</h2>
              <p className="text-xs text-zinc-500">Control agent autonomy</p>
            </div>
          </div>

          <div className="space-y-4">
            {/* Auto-approve all */}
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-3">
                <Zap size={16} className="text-zinc-500" />
                <div>
                  <div className="text-sm text-zinc-300">Auto-Approve All</div>
                  <div className="text-xs text-zinc-600">Skip all approval prompts</div>
                </div>
              </div>
              <Toggle 
                enabled={settings.autoApproveAll} 
                onChange={(v) => settings.updateSetting('autoApproveAll', v)} 
              />
            </div>

            {/* Auto-navigate */}
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-3">
                <Globe size={16} className="text-zinc-500" />
                <div>
                  <div className="text-sm text-zinc-300">Auto-Navigate</div>
                  <div className="text-xs text-zinc-600">Let agent navigate to relevant pages</div>
                </div>
              </div>
              <Toggle 
                enabled={settings.autoNavigate} 
                onChange={(v) => settings.updateSetting('autoNavigate', v)} 
              />
            </div>

            {/* Learn Preferences */}
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-3">
                <Cpu size={16} className="text-zinc-500" />
                <div>
                  <div className="text-sm text-zinc-300">Learn Preferences</div>
                  <div className="text-xs text-zinc-600">Improve over time</div>
                </div>
              </div>
              <Toggle 
                enabled={settings.learnPreferences} 
                onChange={(v) => settings.updateSetting('learnPreferences', v)} 
              />
            </div>

            {/* Learned Approvals */}
            {settings.learnedApprovals.length > 0 && (
              <div className="pt-2">
                <label className="text-xs font-medium text-zinc-500 mb-2 block">Auto-Approved Actions</label>
                <div className="space-y-2">
                  {settings.learnedApprovals.map((actionType) => (
                    <div 
                      key={actionType}
                      className="flex items-center justify-between px-3 py-2 rounded-lg bg-zinc-800/50 border border-zinc-800"
                    >
                      <span className="text-xs text-zinc-400">
                        {actionTypeLabels[actionType] || actionType.replace(/_/g, ' ')}
                      </span>
                      <button
                        onClick={() => settings.removeLearnedApproval(actionType)}
                        className="p-1 text-zinc-600 hover:text-red-400 transition-colors"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </GlassCard>
        
        {/* Connected Accounts */}
        <GlassCard className="p-6 flex flex-col gap-5" variant="dark">
           <div className="flex items-center gap-3 mb-1">
             <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400"><Globe size={18} /></div>
             <div>
               <h2 className="text-base font-medium text-white">Integrations</h2>
               <p className="text-xs text-zinc-500">Manage external data sources</p>
             </div>
           </div>

           <div className="space-y-3">
             {[
               { name: 'Gmail', key: 'gmail', icon: Mail },
               { name: 'Google Calendar', key: 'google_calendar', icon: Calendar }
             ].map((account) => {
               const connected = isConnected(account.key)
               const isLoading = loading[account.key as 'gmail' | 'calendar']
               const accountData = accounts.find(acc => acc.provider === account.key)

               return (
                 <div key={account.key} className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/30 border border-zinc-800/50">
                   <div className="flex items-center gap-3">
                     <div className={`p-1.5 rounded-lg ${connected ? 'bg-emerald-500/10 text-emerald-400' : 'bg-zinc-800 text-zinc-500'}`}>
                       <account.icon size={16} />
                     </div>
                     <div>
                       <div className="text-sm text-zinc-300">{account.name}</div>
                       <div className="text-xs text-zinc-600">
                         {connected ? (accountData?.provider_email || 'Connected') : 'Not connected'}
                       </div>
                     </div>
                   </div>
                   <button
                     onClick={() => connectAccount(account.key as 'gmail' | 'calendar')}
                     disabled={isLoading || connected}
                     className={`px-3 py-1.5 rounded-lg text-xs transition-all border ${
                       connected 
                         ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 cursor-default' 
                         : 'bg-zinc-800 border-zinc-700 text-zinc-300 hover:bg-zinc-700'
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
        <GlassCard className="p-6 flex flex-col gap-5" variant="dark">
           <div className="flex items-center gap-3 mb-1">
             <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400"><Cpu size={18} /></div>
             <div>
               <h2 className="text-base font-medium text-white">System</h2>
               <p className="text-xs text-zinc-500">Core preferences</p>
             </div>
           </div>

           <div className="space-y-4">
             {/* Quiet Hours Toggle */}
             <div className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                   <Moon size={16} className="text-zinc-500" />
                   <div>
                      <div className="text-sm text-zinc-300">Quiet Hours</div>
                      <div className="text-xs text-zinc-600">{preferences.quiet_hours_start} - {preferences.quiet_hours_end}</div>
                   </div>
                </div>
                <Toggle 
                  enabled={preferences.quiet_hours_enabled} 
                  onChange={(v) => updatePreferences({ quiet_hours_enabled: v })} 
                />
             </div>

             {/* AI Model Selection */}
             <div>
               <label className="text-xs font-medium text-zinc-500 mb-2 block">AI Model</label>
               <select 
                 value={selectedModel ? `${selectedModel.provider}:${selectedModel.name}` : 'openai:gpt-5'}
                 onChange={(e) => {
                   const [provider, name] = e.target.value.split(':')
                   setModel(provider, name)
                 }}
                 className="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-lg px-3 py-2 text-sm text-zinc-300 focus:border-zinc-600 outline-none"
               >
                 <optgroup label="OpenAI">
                   {AVAILABLE_MODELS.filter(m => m.provider === 'openai').map(model => (
                     <option key={model.id} value={`${model.provider}:${model.id}`}>
                       {model.name}
                     </option>
                   ))}
                 </optgroup>
                 <optgroup label="NVIDIA NIM">
                   {AVAILABLE_MODELS.filter(m => m.provider === 'nvidia').map(model => (
                     <option key={model.id} value={`${model.provider}:${model.id}`}>
                       {model.name}
                     </option>
                   ))}
                 </optgroup>
               </select>
             </div>

             {/* Temperature Unit */}
             <div>
               <label className="text-xs font-medium text-zinc-500 mb-2 block">Temperature Unit</label>
               <div className="grid grid-cols-2 gap-2">
                 {(['celsius', 'fahrenheit'] as const).map((unit) => (
                   <button
                     key={unit}
                     onClick={() => settings.updateSetting('tempUnit', unit)}
                     className={`py-1.5 rounded-lg text-xs transition-all border ${
                       settings.tempUnit === unit
                         ? 'bg-zinc-800 border-zinc-600 text-white'
                         : 'bg-transparent border-zinc-800 text-zinc-500 hover:bg-zinc-800/50'
                     }`}
                   >
                     {unit === 'celsius' ? '°C Celsius' : '°F Fahrenheit'}
                   </button>
                 ))}
               </div>
             </div>

             {/* Sync Interval */}
             <div>
               <label className="text-xs font-medium text-zinc-500 mb-2 block">Sync Frequency</label>
               <div className="grid grid-cols-3 gap-2">
                 {['manual', '15', '60'].map((interval) => (
                   <button
                     key={interval}
                     onClick={() => updatePreferences({ auto_sync_interval: interval })}
                     className={`py-1.5 rounded-lg text-xs transition-all border ${
                       preferences.auto_sync_interval === interval
                         ? 'bg-zinc-800 border-zinc-600 text-white'
                         : 'bg-transparent border-zinc-800 text-zinc-500 hover:bg-zinc-800/50'
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
        <GlassCard className="md:col-span-2 p-4 flex items-center justify-between" variant="dark">
           <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
                <LogOut size={18} />
              </div>
              <div>
                <h3 className="text-sm font-medium text-zinc-300">Sign Out</h3>
                <p className="text-xs text-zinc-600">End your current session</p>
              </div>
           </div>
           <div className="flex items-center gap-2">
             <button 
               onClick={() => settings.resetToDefaults()}
               className="px-3 py-1.5 rounded-lg border border-zinc-700/50 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 transition-colors text-xs flex items-center gap-1.5"
             >
               <Trash2 size={12} />
               Reset Settings
             </button>
             <button className="px-4 py-1.5 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors text-xs">
               Log Out
             </button>
           </div>
        </GlassCard>

      </div>
    </div>
  )
}
