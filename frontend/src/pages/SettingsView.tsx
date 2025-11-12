import './SettingsView.css'

function SettingsView() {
  return (
    <div className="settings-view fade-in">
      <div className="settings-header">
        <h1 className="page-title gradient-text">Settings</h1>
      </div>

      <div className="settings-grid">
        <div className="settings-section glass">
          <div className="section-header">
            <h2>Link Connected Accounts</h2>
          </div>
          <div className="section-content">
            <div className="account-item">
              <div className="account-info">
                <div className="account-icon gmail">Email</div>
                <div>
                  <div className="account-name">Gmail</div>
                  <div className="account-status">Not connected</div>
                </div>
              </div>
              <button className="connect-button">Connect</button>
            </div>
            <div className="account-item">
              <div className="account-info">
                <div className="account-icon outlook">Mail</div>
                <div>
                  <div className="account-name">Outlook</div>
                  <div className="account-status">Not connected</div>
                </div>
              </div>
              <button className="connect-button">Connect</button>
            </div>
            <div className="account-item">
              <div className="account-info">
                <div className="account-icon calendar">Calendar</div>
                <div>
                  <div className="account-name">Google Calendar</div>
                  <div className="account-status">Not connected</div>
                </div>
              </div>
              <button className="connect-button">Connect</button>
            </div>
          </div>
        </div>

        <div className="settings-section glass">
          <div className="section-header">
            <h2>Settings Preferences</h2>
          </div>
          <div className="section-content">
            <div className="preference-item">
              <div className="preference-label">
                <span>Email Tone</span>
                <span className="preference-description">How formal should AI drafts be?</span>
              </div>
              <select className="preference-select">
                <option>Professional</option>
                <option>Friendly</option>
                <option>Casual</option>
              </select>
            </div>
            <div className="preference-item">
              <div className="preference-label">
                <span>Quiet Hours</span>
                <span className="preference-description">When should notifications pause?</span>
              </div>
              <div className="preference-value">10 PM - 8 AM</div>
            </div>
            <div className="preference-item">
              <div className="preference-label">
                <span>Timezone</span>
                <span className="preference-description">Your local timezone</span>
              </div>
              <div className="preference-value">UTC-8 (Pacific)</div>
            </div>
          </div>
        </div>

        <div className="settings-section glass">
          <div className="section-header">
            <h2>AI AI Configuration</h2>
          </div>
          <div className="section-content">
            <div className="preference-item">
              <div className="preference-label">
                <span>AI Provider</span>
                <span className="preference-description">Choose your LLM provider</span>
              </div>
              <select className="preference-select">
                <option>OpenAI (GPT-4o-mini)</option>
                <option>NVIDIA NIM (Llama 3 70B)</option>
              </select>
            </div>
            <div className="preference-item">
              <div className="preference-label">
                <span>Auto-sync Interval</span>
                <span className="preference-description">How often to check for new items</span>
              </div>
              <select className="preference-select">
                <option>Every 15 minutes</option>
                <option>Every 30 minutes</option>
                <option>Every hour</option>
                <option>Manual only</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsView
