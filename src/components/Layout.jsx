import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

const Layout = ({ children }) => {
  const location = useLocation()
  
  // Auto-collapse sidebar for Graph Visualizer to maximize visualization space
  const shouldCollapseSidebar = location.pathname === '/graph'
  const [sidebarOpen, setSidebarOpen] = useState(!shouldCollapseSidebar)
  
  // Update sidebar state when route changes
  useEffect(() => {
    if (shouldCollapseSidebar) {
      setSidebarOpen(false)
    }
  }, [shouldCollapseSidebar])

  return (
    <div className="flex h-screen bg-dark-bg">
      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ width: sidebarOpen ? 256 : 80 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="relative"
      >
        <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
        
        <main className="flex-1 overflow-auto">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout