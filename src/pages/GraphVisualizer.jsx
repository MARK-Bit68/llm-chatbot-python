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
  const [selectedRelationships, setSelectedRelationships] = useState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [visualizationMode, setVisualizationMode] = useState('enhanced') // 'enhanced' or 'gaming'
  const [showFilters, setShowFilters] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  
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
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading Graph Data...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
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
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Network className="w-8 h-8 text-blue-600" />
                  <h1 className="text-2xl font-bold text-gray-900">
                    Supply Chain Graph Visualization
                  </h1>
                </div>
                
                {/* Mode Selector */}
                <div className="flex items-center gap-2 ml-8">
                  <span className="text-sm font-medium text-gray-700">Mode:</span>
                  <select
                    value={visualizationMode}
                    onChange={(e) => setVisualizationMode(e.target.value)}
                    className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="enhanced">Enhanced 3D</option>
                    <option value="gaming">Gaming Style</option>
                  </select>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <Filter className="w-4 h-4" />
                  {showFilters ? 'Hide' : 'Show'} Filters
                </button>
                
                <button
                  onClick={handleRefresh}
                  className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Filters Panel */}
            {showFilters && (
              <div className="lg:col-span-1">
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                      <Filter className="w-5 h-5" />
                      Filters
                    </h3>
                    <button
                      onClick={handleReset}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Reset
                    </button>
                  </div>

                  {/* Search */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Search Nodes
                    </label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search by name or type..."
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  {/* Relationship Filters */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Relationships</h4>
                    <div className="space-y-2">
                      {availableRelationships.map((relationship) => {
                        const actualType = relationshipMapping[relationship]
                        const isSelected = selectedRelationships.includes(actualType)
                        
                        return (
                          <label key={relationship} className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleRelationshipToggle(relationship)}
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-700">{relationship}</span>
                          </label>
                        )
                      })}
                    </div>
                  </div>

                  {/* Stats */}
                  {graphData && (
                    <div className="mt-6 pt-6 border-t border-gray-200">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Statistics</h4>
                      <div className="space-y-2 text-sm text-gray-600">
                        <div className="flex justify-between">
                          <span>Total Nodes:</span>
                          <span className="font-medium">{graphData.nodes?.length || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Total Edges:</span>
                          <span className="font-medium">{graphData.links?.length || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Selected Edges:</span>
                          <span className="font-medium">{selectedRelationships.length === 0 ? graphData.links?.length || 0 : 'Filtered'}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Visualization */}
            <div className={`${showFilters ? 'lg:col-span-3' : 'lg:col-span-4'}`}>
              <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
                {visualizationMode === 'enhanced' ? (
                  <EnhancedGraphVisualizer
                    data={graphData}
                    selectedRelationships={selectedRelationships}
                    onNodeSelect={handleNodeSelect}
                    className="w-full h-96"
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
          </div>

          {/* Selected Node Info */}
          {selectedNode && (
            <div className="mt-6">
              <GraphMetadata node={selectedNode} />
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}

export default GraphVisualizer
