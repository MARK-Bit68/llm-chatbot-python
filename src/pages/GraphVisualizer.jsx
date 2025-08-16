import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion } from 'framer-motion'
import ForceGraph3D from 'react-force-graph-3d'
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
  Layers
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
  
  // Debug viewMode
  useEffect(() => {
    console.log('🎯 Current viewMode:', viewMode)
  }, [viewMode])
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
    nodeRelSize: 6, // Increase node size for better visibility
    linkWidth: 2, // Increase link width for better visibility
    linkOpacity: 0.6, // Increase opacity for better visibility
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

  // Prepare graph data for 3D visualization
  const prepareGraphData = useCallback(() => {
    if (!graphData || !graphData.nodes) return null

    console.log('🔧 Preparing graph data for 3D visualization:', {
      nodesCount: graphData.nodes.length,
      edgesCount: graphData.edges?.length || 0
    })

    // Add 3D positioning and enhanced properties to nodes
    const enhancedNodes = graphData.nodes.map((node, index) => {
      const nodeId = node.id || node.code || `node-${index}`
      return {
        ...node,
        id: nodeId,
        val: node.type === 'Product' ? 8 : 
             node.type === 'Plant' ? 12 : 
             node.type === 'StorageLocation' ? 10 : 
             node.type === 'Group' ? 15 : 6,
        color: node.type === 'Product' ? '#10B981' : 
               node.type === 'Plant' ? '#3B82F6' : 
               node.type === 'StorageLocation' ? '#F59E0B' : 
               node.type === 'Group' ? '#8B5CF6' : 
               node.type === 'Category' ? '#EF4444' : '#6B7280',
        // Add 3D positioning hints
        x: Math.cos(index * 0.1) * 100,
        y: Math.sin(index * 0.1) * 100,
        z: Math.sin(index * 0.05) * 50
      }
    })

    // Prepare edges with proper source/target mapping
    const enhancedEdges = (graphData.edges || []).map((edge, index) => {
      // Ensure source and target are valid node IDs
      const sourceId = edge.source || edge.source_id
      const targetId = edge.target || edge.target_id
      
      // Find the actual node objects for source and target
      const sourceNode = enhancedNodes.find(node => node.id === sourceId)
      const targetNode = enhancedNodes.find(node => node.id === targetId)
      
      if (sourceNode && targetNode) {
        return {
          ...edge,
          id: `edge-${index}`,
          source: sourceNode, // Use the actual node object
          target: targetNode, // Use the actual node object
          color: '#4B5563',
          width: 1
        }
      }
      return null
    }).filter(edge => edge !== null) // Filter out invalid edges

    const result = {
      nodes: enhancedNodes,
      links: enhancedEdges
    }

    console.log('✅ Prepared 3D graph data:', {
      nodesCount: result.nodes.length,
      linksCount: result.links.length,
      sampleNode: result.nodes[0],
      sampleLink: result.links[0]
    })

    return result
  }, [graphData])

  const graphData3D = prepareGraphData()
  const [webglError, setWebglError] = useState(false)
  const [graphReady, setGraphReady] = useState(false)

  // Graph interaction handlers
  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node)
    console.log('Node clicked:', node)
  }, [])

  // Handle WebGL errors
  const handleWebGLError = useCallback((error) => {
    console.error('WebGL Error:', error)
    setWebglError(true)
  }, [])

  // Handle graph ready
  const handleGraphReady = useCallback(() => {
    console.log('✅ ForceGraph3D is ready')
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

        {/* 3D Graph Visualization Area */}
        <div className="flex-1 relative">
          <div className="absolute inset-0 bg-gradient-to-br from-dark-bg to-surface">
            {graphData3D && graphData3D.nodes && graphData3D.nodes.length > 0 ? (
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
                                         console.log('🎯 Rendering ForceGraph3D with data:', {
                       nodes: graphData3D.nodes.length,
                       links: graphData3D.links.length,
                       sampleNode: graphData3D.nodes[0],
                       sampleLink: graphData3D.links[0],
                       nodeIds: graphData3D.nodes.map(n => n.id).slice(0, 5),
                       linkSources: graphData3D.links.map(l => l.source?.id || l.source).slice(0, 5),
                       linkTargets: graphData3D.links.map(l => l.target?.id || l.target).slice(0, 5)
                     })
                    
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
                         height={windowDimensions.height - 120}
                       />
                     )
                  } catch (error) {
                    console.error('❌ ForceGraph3D rendering error:', error)
                    return (
                      <div className="flex items-center justify-center h-full">
                        <div className="text-center">
                          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Network className="w-8 h-8 text-red-500" />
                          </div>
                          <h3 className="text-lg font-semibold text-white mb-2">3D Visualization Error</h3>
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
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default GraphVisualizer
