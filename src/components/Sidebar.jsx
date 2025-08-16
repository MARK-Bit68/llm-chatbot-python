import React from 'react'
import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  BarChart3, 
  MessageCircle, 
  TrendingUp, 
  Package, 
  Settings, 
  ChevronLeft,
  ChevronRight,
  Brain,
  Sparkles,
  Network,
  Upload
} from 'lucide-react'
import clsx from 'clsx'

const navigation = [
  { name: 'Advanced Dashboard', href: '/', icon: Brain, badge: 'AI' },
  { name: 'Advanced Chat', href: '/chat', icon: Sparkles, badge: 'ML' },
  { name: 'Graph Visualizer', href: '/graph', icon: Network, badge: '3D' },
  { name: 'Analytics', href: '/analytics', icon: TrendingUp },
  { name: 'Product Explorer', href: '/products', icon: Package },
  { name: 'Upload Excel', href: '/upload', icon: Upload, badge: 'NEW' },
  { name: 'Basic Dashboard', href: '/dashboard', icon: BarChart3 },
  { name: 'Basic Chat', href: '/chat/basic', icon: MessageCircle },
  { name: 'Settings', href: '/settings', icon: Settings },
]

const Sidebar = ({ isOpen, onToggle }) => {
  return (
    <div className="h-full bg-surface border-r border-white border-opacity-10 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-white border-opacity-10">
        <div className="flex items-center justify-between">
          {isOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center space-x-3"
            >
              <div className="w-8 h-8 bg-gradient-to-r from-brand-500 to-brand-600 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">FMCG Assistant</h1>
                <p className="text-xs text-dark-muted">Supply Chain Analytics</p>
              </div>
            </motion.div>
          )}
          
          {!isOpen && (
            <div className="w-8 h-8 bg-gradient-to-r from-brand-500 to-brand-600 rounded-lg flex items-center justify-center mx-auto">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
          )}
          
          <button
            onClick={onToggle}
            className="p-1 hover:bg-surface-2 rounded-md transition-colors"
          >
            {isOpen ? (
              <ChevronLeft className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                clsx(
                  'flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors relative',
                  isActive
                    ? 'bg-brand-500/20 text-brand-500 border border-brand-500/30'
                    : 'text-dark-muted hover:text-white hover:bg-surface-2'
                )
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {isOpen && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  transition={{ duration: 0.2 }}
                  className="flex items-center justify-between flex-1"
                >
                  <span>{item.name}</span>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 bg-brand-500 text-white text-xs rounded-full">
                      {item.badge}
                    </span>
                  )}
                </motion.div>
              )}
              {!isOpen && item.badge && (
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-brand-500 rounded-full"></div>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="p-4 border-t border-white border-opacity-10"
        >
          <div className="text-xs text-dark-muted space-y-1">
            <div className="flex items-center justify-between">
              <span>Version</span>
              <span>v1.0.0</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Model</span>
              <span>GPT-4</span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default Sidebar