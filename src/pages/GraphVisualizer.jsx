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
  X
} from 'lucide-react'
import GamingGraphVisualizer from '../components/GamingGraphVisualizer'
import EnhancedGraphVisualizer from '../components/EnhancedGraphVisualizer'
import Layout from '../components/Layout'
import GraphMetadata from '../components/GraphMetadata'

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
  const [viewMode, setViewMode] = useState('Enhanced') // Enhanced, Gaming, 3D, 2D, Force
  const [useGamingMode, setUseGamingMode] = useState(false)
  
  // Edge filtering state - START WITH NOTHING for guided experience
  const [edgeFilters, setEdgeFilters] = useState({
    showBelongsTo: false,        // Product → Category (start hidden)
    showBrandedAs: false,        // Product → Brand (start hidden)
    showSoldIn: false,           // Product → Country (start hidden)
    showPartOf: false,           // Country → Region (start hidden)
    showManufacturedAt: false,   // Product → Plant (start hidden)
    focusMode: 'none'            // none, selected
  })
  
  // Tutorial state for guided experience - remember user preference
  const [tutorialStep, setTutorialStep] = useState(0)
  const [showTutorial, setShowTutorial] = useState(() => {
    const skipped = localStorage.getItem('graphTutorialSkipped')
    return !skipped
  })
  
  
  // Add error handling for 3D component
  const [forceGraph3DError, setForceGraph3DError] = useState(false)
  
  // Check if ForceGraph3D is available
  useEffect(() => {
    try {
      // Test if ForceGraph3D is available
      if (typeof ForceGraph3D === 'undefined') {
        console.warn('⚠️ ForceGraph3D not available, falling back to 2D')
        setForceGraph3DError(true)
        setViewMode('Enhanced')
      }
    } catch (error) {
      console.error('❌ Error checking ForceGraph3D:', error)
      setForceGraph3DError(true)
      setViewMode('Enhanced')
    }
  }, [])
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [windowDimensions, setWindowDimensions] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  })

  useEffect(() => {
    fetchGraphData()
  }, [])

  useEffect(() => {
    const handleResize = () => {
      setWindowDimensions({
        width: window.innerWidth,
        height: window.innerHeight
      })
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Fetch graph data from API
  const fetchGraphData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch('/api/graph/visualization')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('📊 Graph data loaded:', {
        nodes: data.nodes?.length || 0,
        edges: data.links?.length || 0,
        edgeTypes: [...new Set(data.links?.map(e => e.type) || [])]
      })
      
      setGraphData(data)
    } catch (error) {
      console.error('❌ Error fetching graph data:', error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  // Toggle filter
  const toggleFilter = (filterName) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: !prev[filterName]
    }))
  }

  // Handle node selection
  const handleNodeSelect = (node) => {
    setSelectedNode(node)
    console.log('🎯 Selected node:', node)
  }

  // Handle background click
  const handleBackgroundClick = () => {
    setSelectedNode(null)
  }

  // Handle node hover
  const handleNodeHover = (node) => {
    // Optional: Add hover effects
  }

  // Handle graph ready
  const handleGraphReady = () => {
    console.log('✅ Graph visualization ready')
  }

  // Handle WebGL error
  const handleWebGLError = () => {
    console.error('❌ WebGL context lost')
    setForceGraph3DError(true)
  }

  // Toggle fullscreen
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen bg-dark-bg">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <h3 className="text-lg font-semibold text-white mb-2">Loading Graph Data</h3>
            <p className="text-dark-muted">Fetching supply chain network visualization...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen bg-dark-bg">
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
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="min-h-screen bg-dark-bg">
        {/* Header Controls */}
        <div className="bg-surface border-b border-white border-opacity-10 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-white">Supply Chain Graph Visualization</h1>
              <div className="flex items-center gap-2">
                <span className="text-sm text-dark-muted">Mode:</span>
                <select
                  value={viewMode}
                  onChange={(e) => setViewMode(e.target.value)}
                  className="bg-surface-2 border border-white border-opacity-10 rounded px-2 py-1 text-white text-sm"
                >
                  <option value="Enhanced">Enhanced 3D</option>
                  <option value="Gaming">Gaming Mode</option>
                  <option value="3D">Legacy 3D</option>
                  <option value="2D">2D</option>
                  <option value="Force">Force Layout</option>
                </select>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleFullscreen}
                className="p-2 hover:bg-surface-2 rounded-lg transition-colors"
                title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
              >
                {isFullscreen ? (
                  <Minimize2 className="w-4 h-4 text-gray-400 hover:text-white" />
                ) : (
                  <Maximize2 className="w-4 h-4 text-gray-400 hover:text-white" />
                )}
              </button>
              <button
                onClick={fetchGraphData}
                className="p-2 hover:bg-surface-2 rounded-lg transition-colors"
                title="Refresh Data"
              >
                <RefreshCw className="w-4 h-4 text-gray-400 hover:text-white" />
              </button>
            </div>
          </div>
        </div>

        {/* Compact Controls Header */}
        <div className="bg-surface border-b border-white border-opacity-10 px-6 py-3">
          <div className="grid grid-cols-12 gap-4 items-center">
            
            {/* Node Filters - Column 1-3 */}
            <div className="col-span-3">
              <label className="text-xs font-medium text-white mb-1 block">Node Filters</label>
              <div className="flex flex-wrap gap-1">
                {Object.entries(filters).map(([key, value]) => (
                  <label key={key} className="flex items-center space-x-1 text-xs cursor-pointer">
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={() => toggleFilter(key)}
                      className="w-3 h-3 text-brand-500 bg-surface-2 border-white border-opacity-10 rounded focus:ring-brand-500"
                    />
                    <span className="text-white">
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Relationships - Column 4-8 */}
            <div className="col-span-5">
              <label className="text-xs font-medium text-white mb-1 block">Relationships</label>
              <div className="flex flex-wrap gap-2">
                <label className="flex items-center space-x-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showBelongsTo}
                    onChange={(e) => setEdgeFilters(prev => ({ ...prev, showBelongsTo: e.target.checked }))}
                    className="w-3 h-3 text-green-500 bg-surface-2 border-white border-opacity-10 rounded"
                  />
                  <span className="text-xs text-white">Product→Category</span>
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                </label>
                <label className="flex items-center space-x-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showBrandedAs}
                    onChange={(e) => setEdgeFilters(prev => ({ ...prev, showBrandedAs: e.target.checked }))}
                    className="w-3 h-3 text-orange-500 bg-surface-2 border-white border-opacity-10 rounded"
                  />
                  <span className="text-xs text-white">Product→Brand</span>
                  <div className="w-2 h-2 bg-orange-500 rounded-full" />
                </label>
                <label className="flex items-center space-x-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showSoldIn}
                    onChange={(e) => setEdgeFilters(prev => ({ ...prev, showSoldIn: e.target.checked }))}
                    className="w-3 h-3 text-blue-500 bg-surface-2 border-white border-opacity-10 rounded"
                  />
                  <span className="text-xs text-white">Product→Market</span>
                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                </label>
                <label className="flex items-center space-x-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showPartOf}
                    onChange={(e) => setEdgeFilters(prev => ({ ...prev, showPartOf: e.target.checked }))}
                    className="w-3 h-3 text-cyan-500 bg-surface-2 border-white border-opacity-10 rounded"
                  />
                  <span className="text-xs text-white">Country→Region</span>
                  <div className="w-2 h-2 bg-cyan-500 rounded-full" />
                </label>
                <label className="flex items-center space-x-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showManufacturedAt}
                    onChange={(e) => setEdgeFilters(prev => ({ ...prev, showManufacturedAt: e.target.checked }))}
                    className="w-3 h-3 text-purple-500 bg-surface-2 border-white border-opacity-10 rounded"
                  />
                  <span className="text-xs text-white">Product→Plant</span>
                  <div className="w-2 h-2 bg-purple-500 rounded-full" />
                </label>
              </div>
            </div>

            {/* Graph Statistics - Column 9-12 */}
            {graphData && (
              <div className="col-span-4">
                <label className="text-xs font-medium text-white mb-1 block">Graph Statistics</label>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="text-center">
                    <div className="text-white font-semibold">{graphData.stats?.totalNodes || 0}</div>
                    <div className="text-dark-muted">Nodes</div>
                  </div>
                  <div className="text-center">
                    <div className="text-white font-semibold">{graphData.stats?.totalEdges || 0}</div>
                    <div className="text-dark-muted">Edges</div>
                  </div>
                  <div className="text-center">
                    <div className="text-white font-semibold">{graphData.stats?.products || 0}</div>
                    <div className="text-dark-muted">Products</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Graph Visualization Area */}
        <div className="relative flex-1" style={{ height: 'calc(100vh - 200px)' }}>
          <Suspense fallback={
            <div className="flex items-center justify-center h-full bg-dark-bg">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-dark-muted">Loading visualization...</p>
              </div>
            </div>
          }>
            {viewMode === 'Enhanced' ? (
              <EnhancedGraphVisualizer
                graphData={graphData}
                onNodeSelect={handleNodeSelect}
                edgeFilters={edgeFilters}
                selectedNode={selectedNode}
                nodeFilters={filters}
              />
            ) : viewMode === 'Gaming' ? (
              <GamingGraphVisualizer
                graphData={graphData}
                onNodeSelect={handleNodeSelect}
                edgeFilters={edgeFilters}
                selectedNode={selectedNode}
                nodeFilters={filters}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-dark-bg">
                <div className="text-center">
                  <div className="w-16 h-16 bg-yellow-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Gamepad2 className="w-8 h-8 text-yellow-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Legacy Mode</h3>
                  <p className="text-dark-muted mb-4">Please use Enhanced 3D mode for the best experience</p>
                  <button
                    onClick={() => setViewMode('Enhanced')}
                    className="btn-primary px-4 py-2"
                  >
                    Switch to Enhanced Mode
                  </button>
                </div>
              </div>
            )}
          </Suspense>
        </div>

        {/* Selected Node Info Panel */}
        {selectedNode && (
          <div className="absolute top-20 right-4 bg-black/80 p-4 rounded-lg text-white max-w-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold">Selected Node</h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-1 text-sm">
              <div><strong>Type:</strong> {selectedNode.type}</div>
              <div><strong>Name:</strong> {selectedNode.name || selectedNode.id}</div>
              {selectedNode.category && <div><strong>Category:</strong> {selectedNode.category}</div>}
              {selectedNode.country && <div><strong>Country:</strong> {selectedNode.country}</div>}
              {selectedNode.region && <div><strong>Region:</strong> {selectedNode.region}</div>}
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}

export default GraphVisualizer
