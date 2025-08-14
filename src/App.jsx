import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import AdvancedDashboard from './pages/AdvancedDashboard'
import Chat from './pages/Chat'
import AdvancedChat from './pages/AdvancedChat'
import Analytics from './pages/Analytics'
import SKUExplorer from './pages/SKUExplorer'
import Settings from './pages/Settings'

function App() {
  return (
    <div className="min-h-screen bg-dark-bg text-dark-text">
      <Layout>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Routes>
            <Route path="/" element={<AdvancedDashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/chat" element={<AdvancedChat />} />
            <Route path="/chat/basic" element={<Chat />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/skus" element={<SKUExplorer />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </motion.div>
      </Layout>
    </div>
  )
}

export default App