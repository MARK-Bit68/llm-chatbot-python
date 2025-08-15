import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Network, 
  TrendingUp, 
  DollarSign, 
  BarChart3, 
  Filter,
  Search,
  RefreshCw,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2
} from 'lucide-react'

const GraphVisualizer = () => {
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({
    showProducts: true,
    showPlants: true,
    showStorage: true,
    showRevenue: true,
    showProfit: true,
    showGroups: true
  })
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedNode, setSelectedNode] = useState(null)
  const [viewMode, setViewMode] = useState('3D') // 3D, 2D, Force
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    fetchGraphData()
  }, [])

  const fetchGraphData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch graph data from the backend
      const response = await fetch('/api/graph/visualization')
      if (!response.ok) {
        throw new Error('Failed to fetch graph data')
      }
      
      const data = await response.json()
      setGraphData(data)
    } catch (err) {
      console.error('Error fetching graph data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const toggleFilter = (filterName) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: !prev[filterName]
    }))
  }

  const handleNodeClick = (node) => {
    setSelectedNode(node)
  }

  const clearSelection = () => {
    setSelectedNode(null)
  }

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  if (loading) {
    return (
      <div className="flex-1 overflow-auto">
        <div className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <RefreshCw className="w-8 h-8 text-brand-500 animate-spin mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Loading Graph Data</h3>
              <p className="text-dark-muted">Fetching supply chain network visualization...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex-1 overflow-auto">
        <div className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Network className="w-8 h-8 text-red-500" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Error Loading Graph</h3>
              <p className="text-dark-muted mb-4">{error}</p>
              <button
                onClick={fetchGraphData}
                className="btn-primary px-4 py-2"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-hidden">
      {/* Header */}
      <div className="bg-surface border-b border-white border-opacity-10 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-brand-500 to-brand-600 rounded-lg flex items-center justify-center">
                <Network className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Graph Visualizer</h1>
                <p className="text-sm text-dark-muted">Interactive 3D Supply Chain Network</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={toggleFullscreen}
              className="p-2 hover:bg-surface-2 rounded-lg transition-colors"
              title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
            >
              {isFullscreen ? (
                <Minimize2 className="w-5 h-5" />
              ) : (
                <Maximize2 className="w-5 h-5" />
              )}
            </button>
            <button
              onClick={fetchGraphData}
              className="p-2 hover:bg-surface-2 rounded-lg transition-colors"
              title="Refresh Data"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex h-full">
        {/* Controls Panel */}
        <div className="w-80 bg-surface border-r border-white border-opacity-10 p-4 space-y-6">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-white mb-2">Search Nodes</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-muted" />
              <input
                type="text"
                placeholder="Search products, plants, storage..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-surface-2 border border-white border-opacity-10 rounded-lg text-white placeholder-dark-muted focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          {/* View Mode */}
          <div>
            <label className="block text-sm font-medium text-white mb-2">View Mode</label>
            <div className="grid grid-cols-3 gap-2">
              {['3D', '2D', 'Force'].map((mode) => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className={`px-3 py-2 text-sm rounded-lg transition-colors ${
                    viewMode === mode
                      ? 'bg-brand-500 text-white'
                      : 'bg-surface-2 text-dark-muted hover:text-white'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          {/* Filters */}
          <div>
            <label className="block text-sm font-medium text-white mb-2">Filters</label>
            <div className="space-y-2">
              {Object.entries(filters).map(([key, value]) => (
                <label key={key} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={value}
                    onChange={() => toggleFilter(key)}
                    className="w-4 h-4 text-brand-500 bg-surface-2 border-white border-opacity-10 rounded focus:ring-brand-500"
                  />
                  <span className="text-sm text-white capitalize">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
                  </span>
                  {value ? <Eye className="w-4 h-4 text-green-500" /> : <EyeOff className="w-4 h-4 text-dark-muted" />}
                </label>
              ))}
            </div>
          </div>

          {/* Selected Node Details */}
          {selectedNode && (
            <div className="border-t border-white border-opacity-10 pt-4">
              <h3 className="text-sm font-medium text-white mb-2">Selected Node</h3>
              <div className="bg-surface-2 rounded-lg p-3 space-y-2">
                <div>
                  <span className="text-xs text-dark-muted">Type:</span>
                  <p className="text-sm text-white font-medium">{selectedNode.type}</p>
                </div>
                <div>
                  <span className="text-xs text-dark-muted">Name:</span>
                  <p className="text-sm text-white">{selectedNode.name}</p>
                </div>
                {selectedNode.revenue && (
                  <div>
                    <span className="text-xs text-dark-muted">Revenue:</span>
                    <p className="text-sm text-green-500 font-medium">${selectedNode.revenue.toLocaleString()}</p>
                  </div>
                )}
                {selectedNode.profit && (
                  <div>
                    <span className="text-xs text-dark-muted">Profit:</span>
                    <p className="text-sm text-blue-500 font-medium">${selectedNode.profit.toLocaleString()}</p>
                  </div>
                )}
                <button
                  onClick={clearSelection}
                  className="w-full mt-2 px-3 py-1 text-xs bg-surface-3 text-white rounded hover:bg-surface-4 transition-colors"
                >
                  Clear Selection
                </button>
              </div>
            </div>
          )}

          {/* Graph Stats */}
          {graphData && (
            <div className="border-t border-white border-opacity-10 pt-4">
              <h3 className="text-sm font-medium text-white mb-2">Graph Statistics</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-dark-muted">Total Nodes:</span>
                  <span className="text-white">{graphData.stats?.totalNodes || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-muted">Total Edges:</span>
                  <span className="text-white">{graphData.stats?.totalEdges || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-muted">Products:</span>
                  <span className="text-white">{graphData.stats?.products || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-muted">Plants:</span>
                  <span className="text-white">{graphData.stats?.plants || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-muted">Storage:</span>
                  <span className="text-white">{graphData.stats?.storage || 0}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Graph Visualization Area */}
        <div className="flex-1 relative">
          <div className="absolute inset-0 bg-gradient-to-br from-dark-bg to-surface">
            {/* Placeholder for 3D Graph Visualization */}
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="w-32 h-32 bg-gradient-to-r from-brand-500/20 to-brand-600/20 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Network className="w-16 h-16 text-brand-500" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">3D Graph Visualization</h3>
                <p className="text-dark-muted mb-6 max-w-md">
                  Interactive 3D visualization of your supply chain network with revenue and profit data exploration.
                </p>
                <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto">
                  <div className="bg-surface-2 rounded-lg p-4">
                    <TrendingUp className="w-8 h-8 text-green-500 mx-auto mb-2" />
                    <p className="text-sm text-white font-medium">Revenue Analysis</p>
                    <p className="text-xs text-dark-muted">Explore revenue patterns</p>
                  </div>
                  <div className="bg-surface-2 rounded-lg p-4">
                    <DollarSign className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                    <p className="text-sm text-white font-medium">Profit Insights</p>
                    <p className="text-xs text-dark-muted">Analyze profitability</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GraphVisualizer
