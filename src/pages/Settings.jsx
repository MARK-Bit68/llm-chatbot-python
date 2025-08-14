import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Save, 
  Database, 
  Cpu, 
  Palette, 
  Bell, 
  Shield,
  Download,
  Upload,
  RefreshCw,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import toast from 'react-hot-toast'

const SettingCard = ({ title, description, icon: Icon, children }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="card"
  >
    <div className="flex items-start space-x-4">
      <div className="p-3 bg-brand-500/20 rounded-lg">
        <Icon className="w-6 h-6 text-brand-500" />
      </div>
      <div className="flex-1">
        <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
        <p className="text-dark-muted text-sm mb-4">{description}</p>
        {children}
      </div>
    </div>
  </motion.div>
)

const Settings = () => {
  const [settings, setSettings] = useState({
    // Database Settings
    neo4jUri: 'neo4j+s://e26a9915.databases.neo4j.io',
    neo4jUsername: 'neo4j',
    neo4jPassword: '••••••••••••••••••••',
    
    // AI Model Settings
    openaiModel: 'gpt-4.1-nano',
    temperature: 0.7,
    maxTokens: 2000,
    
    // UI Settings
    theme: 'dark',
    animations: true,
    compactMode: false,
    
    // Notifications
    emailNotifications: true,
    pushNotifications: false,
    weeklyReports: true,
    
    // Performance
    cacheEnabled: true,
    autoRefresh: true,
    refreshInterval: 30
  })

  const [testResults, setTestResults] = useState({
    database: null,
    openai: null
  })

  const handleSave = () => {
    // Simulate saving settings
    toast.success('Settings saved successfully!')
  }

  const testDatabaseConnection = async () => {
    setTestResults(prev => ({ ...prev, database: 'testing' }))
    
    // Simulate database test
    setTimeout(() => {
      setTestResults(prev => ({ ...prev, database: 'success' }))
      toast.success('Database connection successful!')
    }, 2000)
  }

  const testOpenAIConnection = async () => {
    setTestResults(prev => ({ ...prev, openai: 'testing' }))
    
    // Simulate OpenAI test
    setTimeout(() => {
      setTestResults(prev => ({ ...prev, openai: 'success' }))
      toast.success('OpenAI connection successful!')
    }, 1500)
  }

  const exportSettings = () => {
    const settingsBlob = new Blob([JSON.stringify(settings, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(settingsBlob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'fmcg-settings.json'
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Settings exported successfully!')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-white">Settings</h1>
          <p className="text-dark-muted mt-1">Configure your FMCG assistant</p>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={exportSettings} className="btn-secondary">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
          <button className="btn-secondary">
            <Upload className="w-4 h-4 mr-2" />
            Import
          </button>
          <button onClick={handleSave} className="btn-primary">
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </button>
        </div>
      </motion.div>

      {/* Database Settings */}
      <SettingCard
        title="Database Configuration"
        description="Configure your Neo4j connection settings"
        icon={Database}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-muted mb-2">Neo4j URI</label>
            <input
              type="text"
              value={settings.neo4jUri}
              onChange={(e) => setSettings(prev => ({ ...prev, neo4jUri: e.target.value }))}
              className="input-field w-full"
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-dark-muted mb-2">Username</label>
              <input
                type="text"
                value={settings.neo4jUsername}
                onChange={(e) => setSettings(prev => ({ ...prev, neo4jUsername: e.target.value }))}
                className="input-field w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-muted mb-2">Password</label>
              <input
                type="password"
                value={settings.neo4jPassword}
                onChange={(e) => setSettings(prev => ({ ...prev, neo4jPassword: e.target.value }))}
                className="input-field w-full"
              />
            </div>
          </div>
          
          <button
            onClick={testDatabaseConnection}
            disabled={testResults.database === 'testing'}
            className="btn-secondary"
          >
            {testResults.database === 'testing' ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : testResults.database === 'success' ? (
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
            ) : (
              <Database className="w-4 h-4 mr-2" />
            )}
            Test Connection
          </button>
        </div>
      </SettingCard>

      {/* AI Model Settings */}
      <SettingCard
        title="AI Model Configuration"
        description="Configure OpenAI and model parameters"
        icon={Cpu}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-muted mb-2">Model</label>
            <select
              value={settings.openaiModel}
              onChange={(e) => setSettings(prev => ({ ...prev, openaiModel: e.target.value }))}
              className="input-field w-full"
            >
              <option value="gpt-4.1-nano">GPT-4.1 Nano</option>
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-5-nano">GPT-5 Nano</option>
            </select>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-dark-muted mb-2">
                Temperature: {settings.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => setSettings(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                className="w-full accent-brand-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-muted mb-2">Max Tokens</label>
              <input
                type="number"
                min="100"
                max="4000"
                value={settings.maxTokens}
                onChange={(e) => setSettings(prev => ({ ...prev, maxTokens: parseInt(e.target.value) }))}
                className="input-field w-full"
              />
            </div>
          </div>
          
          <button
            onClick={testOpenAIConnection}
            disabled={testResults.openai === 'testing'}
            className="btn-secondary"
          >
            {testResults.openai === 'testing' ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : testResults.openai === 'success' ? (
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
            ) : (
              <Cpu className="w-4 h-4 mr-2" />
            )}
            Test AI Connection
          </button>
        </div>
      </SettingCard>

      {/* UI Settings */}
      <SettingCard
        title="User Interface"
        description="Customize the appearance and behavior"
        icon={Palette}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-white">Dark Theme</label>
              <p className="text-xs text-dark-muted">Use dark color scheme</p>
            </div>
            <button
              onClick={() => setSettings(prev => ({ 
                ...prev, 
                theme: prev.theme === 'dark' ? 'light' : 'dark' 
              }))}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.theme === 'dark' ? 'bg-brand-500' : 'bg-gray-400'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.theme === 'dark' ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-white">Animations</label>
              <p className="text-xs text-dark-muted">Enable smooth transitions</p>
            </div>
            <button
              onClick={() => setSettings(prev => ({ ...prev, animations: !prev.animations }))}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.animations ? 'bg-brand-500' : 'bg-gray-400'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.animations ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-white">Compact Mode</label>
              <p className="text-xs text-dark-muted">Reduce spacing and padding</p>
            </div>
            <button
              onClick={() => setSettings(prev => ({ ...prev, compactMode: !prev.compactMode }))}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.compactMode ? 'bg-brand-500' : 'bg-gray-400'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.compactMode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </SettingCard>

      {/* Notifications */}
      <SettingCard
        title="Notifications"
        description="Configure alerts and reports"
        icon={Bell}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-white">Email Notifications</label>
              <p className="text-xs text-dark-muted">Receive important updates via email</p>
            </div>
            <button
              onClick={() => setSettings(prev => ({ ...prev, emailNotifications: !prev.emailNotifications }))}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.emailNotifications ? 'bg-brand-500' : 'bg-gray-400'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.emailNotifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-white">Weekly Reports</label>
              <p className="text-xs text-dark-muted">Get weekly performance summaries</p>
            </div>
            <button
              onClick={() => setSettings(prev => ({ ...prev, weeklyReports: !prev.weeklyReports }))}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.weeklyReports ? 'bg-brand-500' : 'bg-gray-400'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.weeklyReports ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </SettingCard>

      {/* Performance */}
      <SettingCard
        title="Performance"
        description="Optimize system performance and caching"
        icon={Shield}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-white">Enable Caching</label>
              <p className="text-xs text-dark-muted">Cache responses for faster performance</p>
            </div>
            <button
              onClick={() => setSettings(prev => ({ ...prev, cacheEnabled: !prev.cacheEnabled }))}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.cacheEnabled ? 'bg-brand-500' : 'bg-gray-400'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.cacheEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-dark-muted mb-2">
              Auto Refresh Interval: {settings.refreshInterval}s
            </label>
            <input
              type="range"
              min="10"
              max="300"
              step="10"
              value={settings.refreshInterval}
              onChange={(e) => setSettings(prev => ({ ...prev, refreshInterval: parseInt(e.target.value) }))}
              className="w-full accent-brand-500"
            />
          </div>
        </div>
      </SettingCard>
    </div>
  )
}

export default Settings