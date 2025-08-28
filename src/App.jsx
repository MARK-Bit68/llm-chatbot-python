import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import AdvancedDashboard from './pages/AdvancedDashboard'
import Chat from './pages/Chat'
import AdvancedChat from './pages/AdvancedChat'
import Analytics from './pages/Analytics'
import ProductExplorer from './pages/ProductExplorer'
import GraphVisualizer from './pages/GraphVisualizer'
import ExcelUploadPage from './pages/ExcelUpload'
import Settings from './pages/Settings'

function App() {
  return (
    <div className="min-h-screen bg-dark-bg text-dark-text">
      <Routes>
        {/* Graph Visualizer route - no Layout wrapper for full-screen experience */}
        <Route path="/graph" element={<GraphVisualizer />} />
        
        {/* All other routes with Layout wrapper */}
        <Route path="*" element={
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
                <Route path="/products" element={<ProductExplorer />} />
                <Route path="/skus" element={<ProductExplorer />} />
                <Route path="/upload" element={<ExcelUploadPage />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </motion.div>
          </Layout>
        } />
      </Routes>
    </div>
  )
}

export default App