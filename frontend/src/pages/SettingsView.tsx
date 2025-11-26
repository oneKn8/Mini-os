import { Mail, Calendar, Moon, Globe, Cpu, RefreshCw } from 'lucide-react'

function SettingsView() {
  return (
    <div className="space-y-8 pb-20 fade-in">
      <h1 className="text-3xl font-bold text-text-primary">Settings</h1>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Connected Accounts */}
        <div className="space-y-6 rounded-2xl bg-surface p-6 border border-border-light shadow-sm">
          <h2 className="text-lg font-semibold text-text-primary border-b border-border-light pb-4">Connected Accounts</h2>
          
          <div className="space-y-4">
            {[
                { name: "Gmail", icon: Mail, connected: false },
                { name: "Outlook", icon: Mail, connected: false },
                { name: "Google Calendar", icon: Calendar, connected: false }
            ].map((account) => (
                <div key={account.name} className="flex items-center justify-between p-3 rounded-xl bg-bg-secondary/50 border border-border-light">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-surface text-text-secondary shadow-sm">
                            <account.icon size={20} />
                        </div>
                        <div>
                            <div className="font-medium text-text-primary">{account.name}</div>
                            <div className="text-xs text-text-tertiary">
                                {account.connected ? "Connected" : "Not connected"}
                            </div>
                        </div>
                    </div>
                    <button className="px-4 py-1.5 rounded-lg text-sm font-medium bg-surface border border-border-medium text-text-primary hover:bg-bg-secondary transition-colors">
                        {account.connected ? "Manage" : "Connect"}
                    </button>
                </div>
            ))}
          </div>
        </div>

        {/* Preferences */}
        <div className="space-y-6 rounded-2xl bg-surface p-6 border border-border-light shadow-sm">
          <h2 className="text-lg font-semibold text-text-primary border-b border-border-light pb-4">Preferences</h2>
          
          <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-accent-primary/10 text-accent-primary">
                        <Moon size={20} />
                    </div>
                    <div>
                        <div className="font-medium text-text-primary">Quiet Hours</div>
                        <div className="text-xs text-text-secondary">Pause notifications 10 PM - 8 AM</div>
                    </div>
                </div>
                <div className="h-6 w-11 rounded-full bg-accent-primary/20 p-1 cursor-pointer">
                    <div className="h-4 w-4 rounded-full bg-accent-primary translate-x-5"></div>
                </div>
            </div>

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-accent-secondary/10 text-accent-secondary">
                        <Globe size={20} />
                    </div>
                    <div>
                        <div className="font-medium text-text-primary">Timezone</div>
                        <div className="text-xs text-text-secondary">UTC-8 (Pacific Time)</div>
                    </div>
                </div>
                <button className="text-sm text-accent-primary font-medium">Edit</button>
            </div>
          </div>
        </div>

        {/* AI Configuration */}
        <div className="md:col-span-2 space-y-6 rounded-2xl bg-surface p-6 border border-border-light shadow-sm">
          <h2 className="text-lg font-semibold text-text-primary border-b border-border-light pb-4">AI Configuration</h2>
          
          <div className="grid gap-6 md:grid-cols-2">
             <div>
                <label className="block text-sm font-medium text-text-secondary mb-2 flex items-center gap-2">
                    <Cpu size={16} />
                    AI Provider
                </label>
                <select className="w-full rounded-xl border border-border-medium bg-bg-secondary px-4 py-2.5 text-sm text-text-primary focus:border-accent-primary focus:ring-1 focus:ring-accent-primary outline-none">
                    <option>OpenAI (GPT-4o-mini)</option>
                    <option>NVIDIA NIM (Llama 3 70B)</option>
                    <option>Anthropic (Claude 3 Haiku)</option>
                </select>
                <p className="mt-1.5 text-xs text-text-tertiary">Select the LLM that powers your agents.</p>
             </div>

             <div>
                <label className="block text-sm font-medium text-text-secondary mb-2 flex items-center gap-2">
                    <RefreshCw size={16} />
                    Auto-sync Interval
                </label>
                <select className="w-full rounded-xl border border-border-medium bg-bg-secondary px-4 py-2.5 text-sm text-text-primary focus:border-accent-primary focus:ring-1 focus:ring-accent-primary outline-none">
                    <option>Manual only</option>
                    <option>Every 15 minutes</option>
                    <option>Every 30 minutes</option>
                    <option>Every hour</option>
                </select>
                <p className="mt-1.5 text-xs text-text-tertiary">Frequency of background inbox checks.</p>
             </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsView
