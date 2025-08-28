import React, { useState, useEffect, useRef, useCallback, Suspense } from 'react'
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
  Minimize2,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Layers,
  Gamepad2,
  Cpu,
  Zap,
  X,
  ChevronRight,
  ChevronLeft
} from 'lucide-react'
import GamingGraphVisualizer from '../components/GamingGraphVisualizer'
import EnhancedGraphVisualizer from '../components/EnhancedGraphVisualizer'
import GraphMetadata from '../components/GraphMetadata'

const GraphVisualizer = () => {
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedRelationships, setSelectedRelationships] = useState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [visualizationMode, setVisualizationMode] = useState('enhanced') // 'enhanced' or 'gaming'
  const [showFilters, setShowFilters] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  
  // Relationship mapping - map UI names to actual edge types
  const relationshipMapping = {
    'Product→Category': 'BELONGS_TO',
    'Product→Brand': 'BRANDED_AS', 
    'Product→Market': 'SOLD_IN',
    'Plant→Country': 'OPERATES_IN',
    'Product→Plant': 'MANUFACTURED_AT',
    'Category→Group': 'PART_OF'
  }
  
  // Available relationships for UI
  const availableRelationships = [
    'Product→Category',
    'Product→Brand', 
    'Product→Market',
    'Plant→Country',
    'Product→Plant',
    'Category→Group'
  ]

  const fetchGraphData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch('/api/graph/visualization')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Graph data received:', data)
      
      if (!data.nodes || !data.links) {
        throw new Error('Invalid graph data structure')
      }
      
      setGraphData(data)
    } catch (err) {
      console.error('Error fetching graph data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchGraphData()
  }, [fetchGraphData])

  const handleRelationshipToggle = useCallback((relationshipName) => {
    setSelectedRelationships(prev => {
      const actualType = relationshipMapping[relationshipName]
      if (!actualType) return prev
      
      if (prev.includes(actualType)) {
        return prev.filter(type => type !== actualType)
      } else {
        return [...prev, actualType]
      }
    })
  }, [])

  const handleNodeSelect = useCallback((node) => {
    setSelectedNode(node)
    console.log('Selected node:', node)
  }, [])

  const handleReset = useCallback(() => {
    setSelectedRelationships([])
    setSelectedNode(null)
    setSearchTerm('')
  }, [])

  const handleRefresh = useCallback(() => {
    fetchGraphData()
  }, [fetchGraphData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Graph Data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error Loading Graph</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full h-full bg-gray-900 flex flex-col">
      {/* Minimal Header Bar */}
      <div className="flex-shrink-0 bg-black/80 backdrop-blur-sm border-b border-white/10 px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Network className="w-5 h-5 text-blue-400" />
              <h1 className="text-white font-semibold text-sm">
                Supply Chain Graph Visualization
              </h1>
            </div>
            
            {/* Mode Selector */}
            <select
              value={visualizationMode}
              onChange={(e) => setVisualizationMode(e.target.value)}
              className="bg-black/40 border border-white/20 rounded px-2 py-1 text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="enhanced">Enhanced 3D</option>
              <option value="gaming">Gaming Style</option>
            </select>
            
            {/* Refresh Button */}
            <button
              onClick={handleRefresh}
              className="bg-black/40 border border-white/20 rounded p-1 text-white hover:bg-black/60 transition-colors"
              title="Refresh Data"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>
          
          {/* Sidebar Toggle */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="bg-black/40 border border-white/20 rounded p-1 text-white hover:bg-black/60 transition-colors"
            title={sidebarCollapsed ? "Show Filters" : "Hide Filters"}
          >
            {sidebarCollapsed ? <ChevronLeft className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 relative flex">
        {/* Minimal Sidebar */}
        <div className={`flex-shrink-0 transition-all duration-300 ${
          sidebarCollapsed ? 'w-0 overflow-hidden' : 'w-64'
        }`}>
          <div className="bg-black/90 backdrop-blur-sm border-r border-white/10 p-4 h-full overflow-y-auto">
            {/* Filters Header */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold text-sm flex items-center gap-2">
                <Filter className="w-4 h-4" />
                Filters
              </h3>
              <button
                onClick={handleReset}
                className="text-xs text-gray-400 hover:text-white"
              >
                Reset
              </button>
            </div>

            {/* Search */}
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-300 mb-2">
                Search Nodes
              </label>
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-3 h-3 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search..."
                  className="w-full pl-7 pr-3 py-1.5 bg-black/40 border border-white/10 rounded text-white text-xs placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Relationship Filters */}
            <div className="mb-4">
              <h4 className="text-xs font-medium text-gray-300 mb-2">Relationships</h4>
              <div className="space-y-1">
                {availableRelationships.map((relationship) => {
                  const actualType = relationshipMapping[relationship]
                  const isSelected = selectedRelationships.includes(actualType)
                  
                  return (
                    <label key={relationship} className="flex items-center gap-2 cursor-pointer text-xs">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleRelationshipToggle(relationship)}
                        className="rounded border-white/20 text-blue-600 focus:ring-blue-500 bg-black/40"
                      />
                      <span className="text-gray-300">{relationship}</span>
                    </label>
                  )
                })}
              </div>
            </div>

            {/* Stats */}
            {graphData && (
              <div className="pt-4 border-t border-white/10">
                <h4 className="text-xs font-medium text-gray-300 mb-2">Statistics</h4>
                <div className="space-y-1 text-xs text-gray-400">
                  <div className="flex justify-between">
                    <span>Nodes:</span>
                    <span className="text-blue-400 font-medium">{graphData.nodes?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Edges:</span>
                    <span className="text-green-400 font-medium">{graphData.links?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Selected:</span>
                    <span className="text-yellow-400 font-medium">{selectedRelationships.length === 0 ? 'All' : selectedRelationships.length}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Full-Screen Visualization */}
        <div className="flex-1 relative">
          {visualizationMode === 'enhanced' ? (
            <EnhancedGraphVisualizer
              data={graphData}
              selectedRelationships={selectedRelationships}
              onNodeSelect={handleNodeSelect}
              className="w-full h-full"
            />
          ) : (
            <GamingGraphVisualizer
              graphData={graphData}
              onNodeSelect={handleNodeSelect}
              edgeFilters={{
                showBelongsTo: selectedRelationships.includes('BELONGS_TO'),
                showBrandedAs: selectedRelationships.includes('BRANDED_AS'),
                showSoldIn: selectedRelationships.includes('SOLD_IN'),
                showOperatesIn: selectedRelationships.includes('OPERATES_IN'),
                showManufacturedAt: selectedRelationships.includes('MANUFACTURED_AT'),
                showPartOf: selectedRelationships.includes('PART_OF')
              }}
              selectedNode={selectedNode}
            />
          )}
        </div>
      </div>

      {/* Selected Node Info - Floating Panel */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 z-50 bg-black/80 backdrop-blur-sm border border-white/10 rounded-lg p-4 max-w-sm">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-white font-semibold text-sm">Selected Node</h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <GraphMetadata node={selectedNode} />
        </div>
      )}
    </div>
  )
}

export default GraphVisualizer
