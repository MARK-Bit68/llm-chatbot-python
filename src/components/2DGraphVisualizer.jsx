import React, { useCallback, useMemo, useRef, useState } from 'react'
import { ForceGraph2D } from 'react-force-graph-2d'
import { Package, Box, Globe, Factory, Network } from 'lucide-react'

const NodeIcon = ({ type, size = 20 }) => {
  const iconProps = { size, className: "text-white" }
  
  switch (type) {
    case 'Product':
      return <Package {...iconProps} />
    case 'Category':
      return <Box {...iconProps} />
    case 'Country':
      return <Globe {...iconProps} />
    case 'Plant':
      return <Factory {...iconProps} />
    default:
      return <Network {...iconProps} />
  }
}

const getNodeColor = (type) => {
  switch (type) {
    case 'Product': return '#10B981' // Green
    case 'Category': return '#8B5CF6' // Purple
    case 'Country': return '#3B82F6' // Blue
    case 'Plant': return '#F59E0B' // Orange
    default: return '#6B7280' // Gray
  }
}

const getNodeSize = (type) => {
  switch (type) {
    case 'Product': return 8
    case 'Category': return 12
    case 'Country': return 10
    case 'Plant': return 11
    default: return 8
  }
}

const getEdgeColor = (type) => {
  switch (type) {
    case 'BELONGS_TO': return '#10B981' // Green
    case 'BRANDED_AS': return '#F59E0B' // Orange
    case 'SOLD_IN': return '#3B82F6' // Blue
    case 'OPERATES_IN': return '#8B5CF6' // Purple
    case 'MANUFACTURED_AT': return '#EF4444' // Red
    case 'PART_OF': return '#06B6D4' // Cyan
    default: return '#6B7280' // Gray
  }
}

const TwoDGraphVisualizer = ({ 
  data, 
  selectedRelationships = [], 
  onNodeSelect,
  className = "" 
}) => {
  const [selectedNode, setSelectedNode] = useState(null)
  const [hoveredNode, setHoveredNode] = useState(null)
  const graphRef = useRef()

  const processedData = useMemo(() => {
    if (!data) return { nodes: [], links: [] }

    // Process nodes
    const nodes = data.nodes.map(node => ({
      ...node,
      id: node.id,
      label: node.name || node.id,
      color: getNodeColor(node.type),
      size: getNodeSize(node.type),
      type: node.type
    }))

    // Process edges and filter by selected relationships
    const links = data.links
      .filter(edge => {
        // If no relationships are selected, show NO edges
        if (selectedRelationships.length === 0) return false
        // Otherwise, only show edges that match selected relationship types
        return selectedRelationships.includes(edge.type)
      })
      .map(edge => ({
        ...edge,
        source: edge.source,
        target: edge.target,
        color: getEdgeColor(edge.type),
        type: edge.type
      }))

    return { nodes, links }
  }, [data, selectedRelationships])

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node)
    if (onNodeSelect) {
      onNodeSelect(node)
    }
  }, [onNodeSelect])

  const handleNodeHover = useCallback((node) => {
    setHoveredNode(node)
  }, [])

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const handleZoomToFit = useCallback(() => {
    graphRef.current?.zoomToFit(400)
  }, [])

  const handleResetView = useCallback(() => {
    graphRef.current?.zoomToFit(400)
    setSelectedNode(null)
  }, [])

  if (!data) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-900 ${className}`}>
        <div className="text-white text-center">
          <Network className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p>No graph data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`relative w-full h-full bg-gray-900 ${className}`}>
      {/* Controls */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button
          onClick={handleZoomToFit}
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
        >
          Zoom to Fit
        </button>
        <button
          onClick={handleResetView}
          className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm"
        >
          Reset View
        </button>
      </div>

      {/* Node Info Panel */}
      {(selectedNode || hoveredNode) && (
        <div className="absolute top-4 right-4 z-10 bg-black/80 text-white p-4 rounded-lg max-w-xs">
          <h3 className="font-bold mb-2">
            {selectedNode ? 'Selected Node' : 'Hovered Node'}
          </h3>
          <div className="space-y-1 text-sm">
            <p><strong>Name:</strong> {(selectedNode || hoveredNode).label}</p>
            <p><strong>Type:</strong> {(selectedNode || hoveredNode).type}</p>
            <p><strong>ID:</strong> {(selectedNode || hoveredNode).id}</p>
          </div>
        </div>
      )}

      {/* Graph */}
      <ForceGraph2D
        ref={graphRef}
        graphData={processedData}
        nodeLabel="label"
        nodeColor="color"
        nodeVal="size"
        nodeRelSize={6}
        linkColor="color"
        linkWidth={1}
        linkOpacity={0.6}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
        onBackgroundClick={handleBackgroundClick}
        cooldownTicks={100}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const label = node.label
          const fontSize = 12/globalScale
          ctx.font = `${fontSize}px Sans-Serif`
          const textWidth = ctx.measureText(label).width
          const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2)

          ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
          ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions)

          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          ctx.fillStyle = node.color
          ctx.fillText(label, node.x, node.y)

          node.__bckgDimensions = bckgDimensions
        }}
        nodeCanvasObjectMode={() => 'after'}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        d3VelocityDecay={0.3}
        d3AlphaDecay={0.02}
        d3AlphaMin={0.001}
      />
    </div>
  )
}

export default TwoDGraphVisualizer
