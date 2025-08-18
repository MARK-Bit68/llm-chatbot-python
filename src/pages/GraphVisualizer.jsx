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
  Zap
} from 'lucide-react'
import GamingGraphVisualizer from '../components/GamingGraphVisualizer'
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
  const [viewMode, setViewMode] = useState('Gaming') // Gaming, 3D, 2D, Force
  const [useGamingMode, setUseGamingMode] = useState(true)
  
  // Edge filtering state for Gaming mode - START WITH NOTHING for guided experience
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
        setViewMode('2D')
      }
    } catch (error) {
      console.error('❌ Error checking ForceGraph3D:', error)
      setForceGraph3DError(true)
      setViewMode('2D')
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

  // 3D Graph visualization with ForceGraph3D
  const graphRef = useRef()
  const [graphConfig, setGraphConfig] = useState({
    showNavInfo: false, // Disable nav info to reduce GPU load
    enableNodeDrag: true,
    enableNavigationControls: true, // Enable built-in controls for dragging
    backgroundColor: '#0F172A',
    nodeRelSize: 8, // Increase node size for better visibility
    linkWidth: 4, // Increase link width for better visibility
    linkOpacity: 0.8, // Increase opacity for better visibility
    d3AlphaDecay: 0.02, // Slower simulation for better stability
    d3VelocityDecay: 0.1, // Less damping for more dynamic movement
    cooldownTicks: 100, // More ticks for better simulation
    // Performance optimizations
    enablePointerInteraction: true,
    enableNodeInteraction: true,
    enableLinkInteraction: true, // Enable link interaction
    // WebGL optimizations
    antialias: true, // Enable antialiasing for better quality
    pixelRatio: 1, // Use 1:1 pixel ratio
    // Force simulation settings
    d3Force: 'link',
    d3ForceLink: {
      distance: 100, // Increase distance between nodes
      iterations: 20 // More iterations for better layout
    },
    // Enable camera controls
    enableCameraInteraction: true,
    enableZoomInteraction: true,
    enablePanInteraction: true
  })

  // Prepare graph data for visualization with focus on dense parts
  const prepareGraphData = useCallback(() => {
    if (!graphData || !graphData.nodes) {
      return null
    }

    try {
      // Simple and robust node processing
      const enhancedNodes = graphData.nodes.slice(0, 50).map((node, index) => {
        const nodeId = node.id || node.code || `node-${index}`
        
        // Simple color mapping
        let color = '#6B7280' // default gray
        let size = 5 // default size
        
        if (node.type === 'Product') {
          color = '#10B981' // green
          size = 8
        } else if (node.type === 'Plant') {
          color = '#3B82F6' // blue
          size = 12
        } else if (node.type === 'StorageLocation') {
          color = '#F59E0B' // yellow
          size = 10
        } else if (node.type === 'Group') {
          color = '#8B5CF6' // purple
          size = 15
        } else if (node.type === 'SubGroup') {
          color = '#EF4444' // red
          size = 12
        }
        
        return {
          id: nodeId,
          name: node.name || node.code || nodeId,
          type: node.type || 'Unknown',
          val: size,
          color: color,
          // Simple positioning
          x: Math.cos(index * 0.5) * 100,
          y: Math.sin(index * 0.5) * 100,
          z: Math.sin(index * 0.3) * 50
        }
      })

      // Simple and robust edge processing
      const enhancedEdges = []
      const processedEdges = new Set()
      
      ;(graphData.links || []).slice(0, 1000).forEach((edge, index) => {
        const sourceId = edge.source || edge.source_id
        const targetId = edge.target || edge.target_id
        
        if (!sourceId || !targetId) return
        
        const edgeKey = `${sourceId}-${targetId}`
        if (processedEdges.has(edgeKey)) return
        processedEdges.add(edgeKey)
        
        // Find source and target nodes
        const sourceNode = enhancedNodes.find(node => 
          node.id === sourceId || 
          node.code === sourceId || 
          node.name === sourceId
        )
        const targetNode = enhancedNodes.find(node => 
          node.id === targetId || 
          node.code === targetId || 
          node.name === targetId
        )
        
        if (sourceNode && targetNode) {
          enhancedEdges.push({
            id: `edge-${index}`,
            source: sourceNode,
            target: targetNode,
            color: '#FFFFFF',
            width: 1,
            opacity: 0.6
          })
        }
      })

      const result = {
        nodes: enhancedNodes,
        links: enhancedEdges
      }


      return result
    } catch (error) {
      console.error('❌ Error preparing graph data:', error)
      // Return a simple fallback with just a few nodes
      return {
        nodes: [
          { id: 'node1', name: 'Product 1', type: 'Product', val: 8, color: '#10B981' },
          { id: 'node2', name: 'Plant 1', type: 'Plant', val: 12, color: '#3B82F6' },
          { id: 'node3', name: 'Storage 1', type: 'StorageLocation', val: 10, color: '#F59E0B' }
        ],
        links: [
          { id: 'edge1', source: 'node1', target: 'node2', color: '#FFFFFF', width: 1, opacity: 0.6 },
          { id: 'edge2', source: 'node2', target: 'node3', color: '#FFFFFF', width: 1, opacity: 0.6 }
        ]
      }
    }
  }, [graphData, viewMode])

  const graphData3D = prepareGraphData()
  const [webglError, setWebglError] = useState(false)
  const [graphReady, setGraphReady] = useState(false)

  // Graph interaction handlers
  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node)
  }, [])

  // Handle WebGL errors
  const handleWebGLError = useCallback((error) => {
    console.error('WebGL Error:', error)
    setWebglError(true)
  }, [])

  // Handle graph ready
  const handleGraphReady = useCallback(() => {
    setGraphReady(true)
  }, [])

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const handleNodeHover = useCallback((node, previousNode) => {
    if (node) {
      document.body.style.cursor = 'pointer'
    } else {
      document.body.style.cursor = 'default'
    }
  }, [])

  // Graph controls
  const resetCamera = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.cameraPosition({ x: 0, y: 0, z: 200 })
    }
  }, [])

  const zoomIn = useCallback(() => {
    if (graphRef.current) {
      const currentPos = graphRef.current.cameraPosition()
      graphRef.current.cameraPosition({
        x: currentPos.x * 0.8,
        y: currentPos.y * 0.8,
        z: currentPos.z * 0.8
      })
    }
  }, [])

  const zoomOut = useCallback(() => {
    if (graphRef.current) {
      const currentPos = graphRef.current.cameraPosition()
      graphRef.current.cameraPosition({
        x: currentPos.x * 1.2,
        y: currentPos.y * 1.2,
        z: currentPos.z * 1.2
      })
    }
  }, [])

  const fetchGraphData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch graph data from the backend with cache-busting
      const response = await fetch(`/api/graph/visualization?t=${Date.now()}`, {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache'
        }
      })
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
    <div className="flex-1 overflow-hidden" data-testid="graph-visualizer">
      {/* Collapsed Mini Header - Essential controls only */}
      <div className="bg-surface border-b border-white border-opacity-10 px-4 py-2">
        <div className="flex items-center justify-end space-x-2">
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

      {/* Graph Metadata - Prominently displayed */}
      <div className="px-6 py-4">
        <GraphMetadata />
      </div>

      <div className="flex h-full">
        {/* Controls Panel - Made narrower for larger visualization */}
        <div className="w-60 bg-surface border-r border-white border-opacity-10 p-4 space-y-6">
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
            <label className="block text-sm font-medium text-white mb-2">Visualization Engine</label>
            <div className="space-y-2">
              {/* Gaming Mode Toggle */}
              <button
                onClick={() => {
                  setUseGamingMode(true)
                  setViewMode('Gaming')
                }}
                className={`w-full px-3 py-3 text-sm rounded-lg transition-colors flex items-center space-x-2 ${
                  useGamingMode
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white border border-purple-500'
                    : 'bg-surface-2 text-dark-muted hover:text-white border border-gray-600'
                }`}
              >
                <Gamepad2 className="w-4 h-4" />
                <span className="font-medium">Gaming Engine</span>
                {useGamingMode && <Zap className="w-4 h-4 text-yellow-400" />}
              </button>
              
              {/* Legacy Modes */}
              <div className="grid grid-cols-3 gap-1">
                {['3D', '2D', 'Force'].map((mode) => (
                  <button
                    key={mode}
                    onClick={() => {
                      setUseGamingMode(false)
                      setViewMode(mode)
                    }}
                    className={`px-2 py-1 text-xs rounded transition-colors ${
                      !useGamingMode && viewMode === mode
                        ? 'bg-brand-500 text-white'
                        : 'bg-surface-2 text-dark-muted hover:text-white'
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
              
              {!useGamingMode && (
                <div className="text-xs text-yellow-500 flex items-center space-x-1">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                  <span>Legacy Mode</span>
                </div>
              )}
            </div>
          </div>

          {/* 3D Controls */}
          {viewMode === '3D' && (
            <div>
              <label className="block text-sm font-medium text-white mb-2">3D Controls</label>
              <div className="space-y-2">
                <button
                  onClick={resetCamera}
                  className="w-full px-3 py-2 text-sm bg-surface-2 hover:bg-surface-3 text-white rounded-lg transition-colors flex items-center justify-center space-x-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Reset Camera</span>
                </button>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={zoomIn}
                    className="px-3 py-2 text-sm bg-surface-2 hover:bg-surface-3 text-white rounded-lg transition-colors flex items-center justify-center space-x-2"
                  >
                    <ZoomIn className="w-4 h-4" />
                    <span>Zoom In</span>
                  </button>
                  <button
                    onClick={zoomOut}
                    className="px-3 py-2 text-sm bg-surface-2 hover:bg-surface-3 text-white rounded-lg transition-colors flex items-center justify-center space-x-2"
                  >
                    <ZoomOut className="w-4 h-4" />
                    <span>Zoom Out</span>
                  </button>
                </div>
              </div>
            </div>
          )}

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

          {/* Edge/Relationship Filters */}
          {useGamingMode && (
            <div className="border-t border-white border-opacity-10 pt-4">
              <label className="block text-sm font-medium text-white mb-2">Relationships</label>
              <div className="space-y-2">
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showBelongsTo}
                    onChange={(e) => {
                      setEdgeFilters(prev => ({ ...prev, showBelongsTo: e.target.checked }))
                    }}
                    className="w-4 h-4 text-green-500 bg-surface-2 border-white border-opacity-10 rounded focus:ring-green-500"
                  />
                  <span className="text-xs text-white">Product → Category</span>
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  <span className="text-xs text-gray-400">Portfolio Analysis</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showBrandedAs}
                    onChange={(e) => {
                      setEdgeFilters(prev => ({ ...prev, showBrandedAs: e.target.checked }))
                    }}
                    className="w-4 h-4 text-orange-500 bg-surface-2 border-white border-opacity-10 rounded focus:ring-orange-500"
                  />
                  <span className="text-xs text-white">Product → Brand</span>
                  <div className="w-2 h-2 bg-orange-500 rounded-full" />
                  <span className="text-xs text-gray-400">Brand Strategy</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showSoldIn}
                    onChange={(e) => {
                      setEdgeFilters(prev => ({ ...prev, showSoldIn: e.target.checked }))
                    }}
                    className="w-4 h-4 text-blue-500 bg-surface-2 border-white border-opacity-10 rounded focus:ring-blue-500"
                  />
                  <span className="text-xs text-white">Product → Market</span>
                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                  <span className="text-xs text-gray-400">Market Presence</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showPartOf}
                    onChange={(e) => {
                      setEdgeFilters(prev => ({ ...prev, showPartOf: e.target.checked }))
                    }}
                    className="w-4 h-4 text-cyan-500 bg-surface-2 border-white border-opacity-10 rounded focus:ring-cyan-500"
                  />
                  <span className="text-xs text-white">Country → Region</span>
                  <div className="w-2 h-2 bg-cyan-500 rounded-full" />
                  <span className="text-xs text-gray-400">Geographic Hierarchy</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showManufacturedAt}
                    onChange={(e) => {
                      setEdgeFilters(prev => ({ ...prev, showManufacturedAt: e.target.checked }))
                    }}
                    className="w-4 h-4 text-purple-500 bg-surface-2 border-white border-opacity-10 rounded focus:ring-purple-500"
                  />
                  <span className="text-xs text-white">Product → Plant</span>
                  <div className="w-2 h-2 bg-purple-500 rounded-full" />
                  <span className="text-xs text-gray-400">Supply Chain</span>
                </label>
              </div>
              
              {/* Focus Mode Toggle */}
              <div className="mt-3">
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.focusMode === 'selected'}
                    onChange={(e) => {
                      setEdgeFilters(prev => ({ ...prev, focusMode: e.target.checked ? 'selected' : 'none' }))
                    }}
                    className="w-4 h-4 text-purple-500 bg-surface-2 border-white border-opacity-10 rounded focus:ring-purple-500"
                  />
                  <span className="text-xs text-white">Focus on Selected Node</span>
                  <div className="w-2 h-2 bg-purple-500 rounded-full" />
                </label>
              </div>
            </div>
          )}

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
        <div className="flex-1 relative min-h-screen">
          <div className="absolute inset-0 bg-gradient-to-br from-dark-bg to-surface">
            {useGamingMode ? (
              // Gaming Mode Visualization
              <Suspense fallback={
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <h3 className="text-lg font-semibold text-white mb-2">Initializing Gaming Engine</h3>
                    <p className="text-dark-muted">Loading 3D gaming visualization...</p>
                  </div>
                </div>
              }>
                <GamingGraphVisualizer 
                  graphData={graphData}
                  onNodeSelect={setSelectedNode}
                  edgeFilters={edgeFilters}
                  selectedNode={selectedNode}
                  nodeFilters={filters}
                />
                
                {/* Guided Tutorial Overlay */}
                {showTutorial && (
                  <div className="absolute inset-0 bg-black/70 flex items-center justify-center z-50 pointer-events-auto">
                    <div className="bg-gradient-to-r from-purple-900 to-blue-900 rounded-xl p-6 max-w-md mx-4 border border-purple-500/30">
                      {tutorialStep === 0 && (
                        <div className="text-center">
                          <h3 className="text-xl font-bold text-white mb-4">🎯 Welcome to Graph Explorer!</h3>
                          <p className="text-purple-200 mb-4">
                            You're looking at 2000 products with no relationships visible yet. 
                            Let's light up the graph step by step!
                          </p>
                          <button
                            onClick={() => setTutorialStep(1)}
                            className="bg-purple-500 hover:bg-purple-600 text-white px-6 py-2 rounded-lg transition-colors"
                          >
                            Start Tutorial →
                          </button>
                          <button
                            onClick={() => {
                              localStorage.setItem('graphTutorialSkipped', 'true')
                              setShowTutorial(false)
                            }}
                            className="ml-2 text-purple-300 hover:text-white transition-colors"
                          >
                            Skip
                          </button>
                        </div>
                      )}
                      
                      {tutorialStep === 1 && (
                        <div className="text-center">
                          <h3 className="text-xl font-bold text-white mb-4">🟢 Step 1: Categories</h3>
                          <p className="text-purple-200 mb-4">
                            Click "Product → Category" in the left panel to see how products connect to their business categories.
                          </p>
                          <button
                            onClick={() => {
                              setEdgeFilters(prev => ({ ...prev, showBelongsTo: true }))
                              setTutorialStep(2)
                            }}
                            className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg transition-colors"
                          >
                            Show Categories ✨
                          </button>
                        </div>
                      )}
                      
                      {tutorialStep === 2 && (
                        <div className="text-center">
                          <h3 className="text-xl font-bold text-white mb-4">🟠 Step 2: Brands</h3>
                          <p className="text-purple-200 mb-4">
                            Now add brand relationships to see how products connect to their brands.
                          </p>
                          <button
                            onClick={() => {
                              setEdgeFilters(prev => ({ ...prev, showBrandedAs: true }))
                              setTutorialStep(3)
                            }}
                            className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-2 rounded-lg transition-colors"
                          >
                            Show Brands ✨
                          </button>
                        </div>
                      )}
                      
                      {tutorialStep === 3 && (
                        <div className="text-center">
                          <h3 className="text-xl font-bold text-white mb-4">🔷 Step 3: Geography</h3>
                          <p className="text-purple-200 mb-4">
                            Add regional hierarchy to understand the geographic structure.
                          </p>
                          <button
                            onClick={() => {
                              setEdgeFilters(prev => ({ ...prev, showPartOf: true }))
                              setTutorialStep(4)
                            }}
                            className="bg-cyan-500 hover:bg-cyan-600 text-white px-6 py-2 rounded-lg transition-colors"
                          >
                            Show Regions ✨
                          </button>
                        </div>
                      )}
                      
                      {tutorialStep === 4 && (
                        <div className="text-center">
                          <h3 className="text-xl font-bold text-white mb-4">🎉 Excellent!</h3>
                          <p className="text-purple-200 mb-4">
                            You now see the core relationships! Use the checkboxes in the left panel to explore different combinations.
                          </p>
                          <button
                            onClick={() => {
                              localStorage.setItem('graphTutorialCompleted', 'true')
                              setShowTutorial(false)
                            }}
                            className="bg-purple-500 hover:bg-purple-600 text-white px-6 py-2 rounded-lg transition-colors"
                          >
                            Start Exploring! 🚀
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Enhanced Hierarchical Visualization Guide */}
                <div className="absolute top-4 right-4 bg-surface/95 backdrop-blur-sm rounded-lg p-4 max-w-sm border border-white/10">
                  <h3 className="text-white font-semibold mb-3 flex items-center">
                    <Gamepad2 className="w-4 h-4 mr-2 text-purple-400" />
                    Graph Layout Guide
                  </h3>
                  
                  <div className="space-y-3 text-sm text-dark-muted">
                    <div>
                      <div className="text-white font-medium mb-2">🎯 Hierarchical Structure</div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                            <span>Products</span>
                          </div>
                          <span className="text-xs text-green-400">Center (Core)</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                            <span>Categories</span>
                          </div>
                          <span className="text-xs text-purple-400">Top Ring</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
                            <span>Brands</span>
                          </div>
                          <span className="text-xs text-orange-400">Right Cluster</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                            <span>Countries</span>
                          </div>
                          <span className="text-xs text-blue-400">Left Side</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-cyan-500 rounded-full mr-2"></div>
                            <span>Regions</span>
                          </div>
                          <span className="text-xs text-cyan-400">Above Countries</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-lime-500 rounded-full mr-2"></div>
                            <span>Plants</span>
                          </div>
                          <span className="text-xs text-lime-400">Right Bottom</span>
                        </div>
                      </div>
                    </div>
                    
                    <hr className="border-white/10" />
                    
                    <div>
                      <div className="text-white font-medium mb-2">🔗 Relationship Flow</div>
                      <div className="text-xs space-y-1">
                        <div>Product → Category (Classification)</div>
                        <div>Product → Brand (Branding)</div>
                        <div>Product → Country (Geography)</div>
                        <div>Country → Region (Hierarchy)</div>
                      </div>
                    </div>
                    
                    <hr className="border-white/10" />
                    
                    <div className="space-y-1">
                      <div className="text-white font-medium">⚡ Navigation</div>
                      <div>• <span className="text-yellow-400">Drag</span>: Rotate around center</div>
                      <div>• <span className="text-yellow-400">Scroll</span>: Zoom to explore layers</div>
                      <div>• <span className="text-yellow-400">Click</span>: Select & inspect</div>
                      <div>• <span className="text-green-400">Tip</span>: Start at center (Products)</div>
                    </div>
                    
                    <hr className="border-white/10" />
                    
                    <div className="text-xs text-dark-muted">
                      <strong>Performance:</strong> 1434/6034 edges visible<br/>
                      <strong>Layout:</strong> Intelligent hierarchy<br/>
                      <strong>Optimization:</strong> LOD + Distance culling
                    </div>
                  </div>
                </div>
              </Suspense>
            ) : graphData3D && graphData3D.nodes && graphData3D.nodes.length > 0 ? (
              // Legacy Mode Visualization
              <div className="w-full h-full relative">
                {/* Loading State */}
                {!graphReady && !webglError && (
                  <div className="absolute inset-0 flex items-center justify-center bg-dark-bg/50 z-10">
                    <div className="text-center">
                      <div className="w-16 h-16 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                      <h3 className="text-lg font-semibold text-white mb-2">Loading 3D Visualization</h3>
                      <p className="text-dark-muted">Initializing WebGL renderer...</p>
                    </div>
                  </div>
                )}

                {/* WebGL Error Fallback */}
                {webglError && (
                  <div className="absolute inset-0 flex items-center justify-center bg-dark-bg/50 z-10">
                    <div className="text-center">
                      <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Network className="w-8 h-8 text-red-500" />
                      </div>
                      <h3 className="text-lg font-semibold text-white mb-2">WebGL Not Supported</h3>
                      <p className="text-dark-muted mb-4">Your browser doesn't support WebGL 3D rendering</p>
                      <button
                        onClick={() => {
                          setWebglError(false)
                          setGraphReady(false)
                        }}
                        className="btn-primary px-4 py-2"
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Retry
                      </button>
                    </div>
                  </div>
                )}
                {(() => {
                  try {
                    
                    // Different visualization based on view mode
                    if (viewMode === '3D' && !forceGraph3DError) {
                      try {
                        return (
                          <ForceGraph3D
                            ref={graphRef}
                            graphData={graphData3D}
                            nodeLabel="name"
                            nodeColor="color"
                            nodeVal="val"
                            linkColor="color"
                            linkWidth="width"
                            linkOpacity={graphConfig.linkOpacity}
                            backgroundColor={graphConfig.backgroundColor}
                            showNavInfo={graphConfig.showNavInfo}
                            enableNodeDrag={graphConfig.enableNodeDrag}
                            enableNavigationControls={graphConfig.enableNavigationControls}
                            enablePointerInteraction={graphConfig.enablePointerInteraction}
                            enableNodeInteraction={graphConfig.enableNodeInteraction}
                            enableLinkInteraction={graphConfig.enableLinkInteraction}
                            antialias={graphConfig.antialias}
                            pixelRatio={graphConfig.pixelRatio}
                            d3AlphaDecay={graphConfig.d3AlphaDecay}
                            d3VelocityDecay={graphConfig.d3VelocityDecay}
                            cooldownTicks={graphConfig.cooldownTicks}
                            onNodeClick={handleNodeClick}
                            onBackgroundClick={handleBackgroundClick}
                            onNodeHover={handleNodeHover}
                            onEngineStop={handleGraphReady}
                            onWebGlContextLost={handleWebGLError}
                            width={windowDimensions.width - 320}
                            height={windowDimensions.height - 100}
                          />
                        )
                      } catch (error) {
                        console.error('❌ ForceGraph3D error:', error)
                        setForceGraph3DError(true)
                        setViewMode('2D')
                        // Fall through to 2D rendering
                      }
                    }
                    
                    // Use 2D as fallback for 3D or when 3D is selected
                    if (viewMode === '2D' || forceGraph3DError) {
                       return (
                         <ForceGraph2D
                           ref={graphRef}
                           graphData={graphData3D}
                           nodeLabel="name"
                           linkLabel="type"
                           nodeColor={node => node.color}
                           linkColor={link => link.color}
                           linkWidth={link => link.width}
                           linkOpacity={link => link.opacity}
                           nodeRelSize={6}
                           linkDirectionalParticles={2}
                           linkDirectionalParticleSpeed={0.005}
                           backgroundColor={graphConfig.backgroundColor}
                           onNodeClick={handleNodeClick}
                           onBackgroundClick={handleBackgroundClick}
                           onNodeHover={handleNodeHover}
                           width={windowDimensions.width - 320}
                           height={windowDimensions.height - 100}
                         />
                       )
                    } else if (viewMode === 'Force') {
                      return (
                        <ForceGraph2D
                          ref={graphRef}
                          graphData={graphData3D}
                          nodeLabel="name"
                          linkLabel="type"
                          nodeColor={node => node.color}
                          linkColor={link => link.color}
                          linkWidth={link => link.width}
                          linkOpacity={link => link.opacity}
                          nodeRelSize={8}
                          backgroundColor={graphConfig.backgroundColor}
                          d3Force="charge"
                          d3ForceLink={{
                            distance: 80,
                            iterations: 30
                          }}
                          d3ForceCharge={{
                            strength: -300,
                            distanceMin: 30,
                            distanceMax: 200
                          }}
                          onNodeClick={handleNodeClick}
                          onBackgroundClick={handleBackgroundClick}
                          onNodeHover={handleNodeHover}
                          width={windowDimensions.width - 320}
                          height={windowDimensions.height - 100}
                        />
                      )
                    }
                  } catch (error) {
                    console.error('❌ Graph rendering error:', error)
                    return (
                      <div className="flex items-center justify-center h-full">
                        <div className="text-center">
                          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Network className="w-8 h-8 text-red-500" />
                          </div>
                          <h3 className="text-lg font-semibold text-white mb-2">Visualization Error</h3>
                          <p className="text-dark-muted mb-4">Error: {error.message}</p>
                          <button
                            onClick={fetchGraphData}
                            className="btn-primary px-4 py-2"
                          >
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Retry
                          </button>
                        </div>
                      </div>
                    )
                  }
                })()}
                
                {/* 3D Controls Overlay */}
                <div className="absolute top-4 right-4 flex flex-col space-y-2">
                  <button
                    onClick={resetCamera}
                    className="p-2 bg-surface-2 hover:bg-surface-3 rounded-lg transition-colors"
                    title="Reset Camera"
                  >
                    <RotateCcw className="w-4 h-4 text-white" />
                  </button>
                  <button
                    onClick={zoomIn}
                    className="p-2 bg-surface-2 hover:bg-surface-3 rounded-lg transition-colors"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-4 h-4 text-white" />
                  </button>
                  <button
                    onClick={zoomOut}
                    className="p-2 bg-surface-2 hover:bg-surface-3 rounded-lg transition-colors"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-4 h-4 text-white" />
                  </button>
                </div>

                {/* Legend Overlay */}
                <div className="absolute top-4 left-4 bg-surface-2 rounded-lg p-3 text-white text-sm">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span>Products ({graphData.stats?.products || 0})</span>
                  </div>
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <span>Plants ({graphData.stats?.plants || 0})</span>
                  </div>
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <span>Storage ({graphData.stats?.storage || 0})</span>
                  </div>
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                    <span>Groups ({graphData.stats?.groups || 0})</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <span>Categories ({graphData.stats?.categories || 0})</span>
                  </div>
                </div>

                {/* Instructions Overlay */}
                <div className="absolute bottom-4 left-4 bg-surface-2 rounded-lg p-3 text-white text-xs opacity-80">
                  <div className="flex items-center space-x-2 mb-1">
                    <Layers className="w-3 h-3" />
                    <span className="font-medium">3D Controls</span>
                  </div>
                  <div>• Drag to rotate • Scroll to zoom • Click nodes for details</div>
                </div>
              </div>
            ) : (
              // No Data State
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="w-32 h-32 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                    {useGamingMode ? (
                      <Gamepad2 className="w-16 h-16 text-purple-500" />
                    ) : (
                      <Network className="w-16 h-16 text-brand-500" />
                    )}
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-4">
                    {useGamingMode ? 'Gaming Graph Explorer' : '3D Graph Visualization'}
                  </h3>
                  <p className="text-dark-muted mb-6 max-w-md">
                    {useGamingMode ? (
                      'Immersive gaming-style 3D exploration of your graph database with advanced navigation controls and real-time interaction.'
                    ) : (
                      'Interactive 3D visualization of your supply chain network with revenue and profit data exploration.'
                    )}
                  </p>
                  
                  {useGamingMode ? (
                    <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto">
                      <div className="bg-surface-2 rounded-lg p-4 border border-purple-500/20">
                        <Cpu className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                        <p className="text-sm text-white font-medium">Gaming Engine</p>
                        <p className="text-xs text-dark-muted">Advanced 3D rendering</p>
                      </div>
                      <div className="bg-surface-2 rounded-lg p-4 border border-blue-500/20">
                        <Zap className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                        <p className="text-sm text-white font-medium">Real-time HUD</p>
                        <p className="text-xs text-dark-muted">Gaming-style interface</p>
                      </div>
                    </div>
                  ) : (
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
                  )}
                  
                  {!useGamingMode && (
                    <div className="mt-6">
                      <button
                        onClick={() => {
                          setUseGamingMode(true)
                          setViewMode('Gaming')
                        }}
                        className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all"
                      >
                        <Gamepad2 className="w-4 h-4" />
                        <span>Try Gaming Engine</span>
                        <Zap className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default GraphVisualizer
