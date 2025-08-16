import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import * as THREE from 'three'
import { Canvas, useFrame, useThree, extend } from '@react-three/fiber'
import { 
  OrbitControls, 
  Text, 
  Sphere, 
  Line, 
  Html,
  PerspectiveCamera,
  Stats,
  Environment
} from '@react-three/drei'
import { 
  Network, 
  Gamepad2, 
  Compass, 
  Target, 
  Search, 
  Filter,
  Map,
  Layers,
  Eye,
  Navigation,
  Zap,
  Settings,
  Play,
  Pause,
  RotateCcw,
  Maximize2,
  TrendingUp,
  Users,
  Box
} from 'lucide-react'

// Gaming-style Graph Node Component
const GraphNode = ({ node, selected, distance, onSelect, cameraPosition }) => {
  const meshRef = useRef()
  const [hovered, setHovered] = useState(false)
  
  // Level of Detail based on distance
  const lod = useMemo(() => {
    if (distance > 1000) return 0 // Very far - don't render
    if (distance > 500) return 1  // Far - simple geometry
    if (distance > 200) return 2  // Medium - normal geometry
    return 3 // Close - full detail
  }, [distance])
  
  // Don't render if too far
  if (lod === 0) return null
  
  // Animate node on hover/selection
  useFrame((state) => {
    if (meshRef.current) {
      const scale = selected ? 1.5 : hovered ? 1.2 : 1
      meshRef.current.scale.lerp(
        new THREE.Vector3(scale, scale, scale), 
        0.1
      )
      
      // Subtle floating animation
      if (selected || hovered) {
        meshRef.current.position.y = node.position.y + Math.sin(state.clock.elapsedTime * 2) * 0.5
      } else {
        meshRef.current.position.y = node.position.y
      }
    }
  })
  
  // Node size based on LOD and type
  const nodeSize = useMemo(() => {
    const baseSize = node.type === 'Product' ? 3 : 
                    node.type === 'Plant' ? 5 : 
                    node.type === 'Group' ? 8 : 4
    return baseSize * (lod === 1 ? 0.5 : 1)
  }, [node.type, lod])
  
  // Node color with gaming-like glow effect
  const nodeColor = useMemo(() => {
    if (selected) return '#FFD700' // Gold when selected
    if (hovered) return '#87CEEB' // Sky blue when hovered
    
    switch (node.type) {
      case 'Product': return '#10B981' // Green
      case 'Plant': return '#3B82F6'   // Blue
      case 'StorageLocation': return '#F59E0B' // Orange
      case 'Group': return '#8B5CF6'   // Purple
      case 'Entity': return '#EF4444'  // Red
      default: return '#6B7280'        // Gray
    }
  }, [node.type, selected, hovered])
  
  return (
    <group position={[node.position.x, node.position.y, node.position.z]}>
      <mesh
        ref={meshRef}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        onClick={() => onSelect(node)}
      >
        {/* LOD-based geometry */}
        {lod >= 3 ? (
          <icosahedronGeometry args={[nodeSize, 2]} />
        ) : lod === 2 ? (
          <sphereGeometry args={[nodeSize, 16, 16]} />
        ) : (
          <sphereGeometry args={[nodeSize, 8, 8]} />
        )}
        
        <meshPhongMaterial 
          color={nodeColor}
          emissive={selected || hovered ? nodeColor : '#000000'}
          emissiveIntensity={selected ? 0.3 : hovered ? 0.1 : 0}
          shininess={100}
        />
      </mesh>
      
      {/* Node label for close nodes */}
      {(selected || hovered || distance < 100) && (
        <Html
          position={[0, nodeSize + 2, 0]}
          center
          style={{
            pointerEvents: 'none',
            userSelect: 'none'
          }}
        >
          <div className="bg-black/80 text-white px-2 py-1 rounded text-xs whitespace-nowrap">
            {node.name}
          </div>
        </Html>
      )}
      
      {/* Glow effect for important nodes */}
      {(selected || node.type === 'Group') && (
        <mesh position={[0, 0, 0]} scale={[1.5, 1.5, 1.5]}>
          <sphereGeometry args={[nodeSize * 1.2, 32, 32]} />
          <meshBasicMaterial 
            color={nodeColor}
            transparent
            opacity={0.1}
          />
        </mesh>
      )}
    </group>
  )
}

// Gaming-style Graph Edge Component
const GraphEdge = ({ edge, visible, distance }) => {
  const lineRef = useRef()
  
  // Level of Detail for edges
  const lod = useMemo(() => {
    if (distance > 800) return 0 // Don't render
    if (distance > 400) return 1 // Simple line
    return 2 // Full detail with particles
  }, [distance])
  
  if (!visible || lod === 0) return null
  
  // Edge color based on relationship type
  const edgeColor = useMemo(() => {
    switch (edge.type) {
      case 'COMPATIBLE_WITH': return '#10B981'
      case 'REPLACES': return '#EF4444'
      case 'REQUIRES': return '#F59E0B'
      case 'BUNDLED_WITH': return '#8B5CF6'
      default: return '#6B7280'
    }
  }, [edge.type])
  
  // Animate edge flow
  useFrame((state) => {
    if (lineRef.current && lod === 2) {
      // Animate line opacity for flow effect
      const opacity = 0.3 + Math.sin(state.clock.elapsedTime * 3) * 0.2
      lineRef.current.material.opacity = opacity
    }
  })
  
  const points = [
    new THREE.Vector3(edge.source.position.x, edge.source.position.y, edge.source.position.z),
    new THREE.Vector3(edge.target.position.x, edge.target.position.y, edge.target.position.z)
  ]
  
  return (
    <Line
      ref={lineRef}
      points={points}
      color={edgeColor}
      lineWidth={lod === 2 ? 2 : 1}
      transparent
      opacity={0.5}
    />
  )
}

// Gaming HUD Component
const GamingHUD = ({ 
  selectedNode, 
  cameraPosition, 
  stats,
  onToggleMap,
  onToggleFilters,
  onReset,
  filters,
  showMinimap,
  isPlaying
}) => {
  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Top Left - Main Stats */}
      <div className="absolute top-4 left-4 pointer-events-auto">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-black/80 text-green-400 font-mono text-xs p-3 rounded border border-green-500/30"
        >
          <div className="flex items-center space-x-2 mb-2">
            <Network className="w-4 h-4" />
            <span className="text-green-300 font-bold">GRAPH NAVIGATOR v2.0</span>
          </div>
          <div className="space-y-1 text-xs">
            <div>NODES: <span className="text-white">{stats?.totalNodes || 0}</span></div>
            <div>EDGES: <span className="text-white">{stats?.totalEdges || 0}</span></div>
            <div>POS: <span className="text-white">
              [{cameraPosition.x.toFixed(0)}, {cameraPosition.y.toFixed(0)}, {cameraPosition.z.toFixed(0)}]
            </span></div>
          </div>
        </motion.div>
      </div>
      
      {/* Top Right - Quick Actions */}
      <div className="absolute top-4 right-4 pointer-events-auto">
        <div className="flex space-x-2">
          <button
            onClick={onToggleMap}
            className={`p-2 rounded border transition-colors ${
              showMinimap 
                ? 'bg-blue-500/20 border-blue-500 text-blue-400' 
                : 'bg-black/80 border-gray-500/30 text-gray-400 hover:text-white'
            }`}
            title="Toggle Minimap"
          >
            <Map className="w-4 h-4" />
          </button>
          
          <button
            onClick={onToggleFilters}
            className="p-2 bg-black/80 border border-gray-500/30 text-gray-400 hover:text-white rounded transition-colors"
            title="Toggle Filters"
          >
            <Filter className="w-4 h-4" />
          </button>
          
          <button
            onClick={onReset}
            className="p-2 bg-black/80 border border-gray-500/30 text-gray-400 hover:text-white rounded transition-colors"
            title="Reset View"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Bottom Left - Controls Help */}
      <div className="absolute bottom-4 left-4 pointer-events-auto">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-black/80 text-amber-400 font-mono text-xs p-3 rounded border border-amber-500/30 max-w-xs"
        >
          <div className="flex items-center space-x-2 mb-2">
            <Gamepad2 className="w-4 h-4" />
            <span className="text-amber-300 font-bold">CONTROLS</span>
          </div>
          <div className="space-y-1 text-xs">
            <div><span className="text-white">DRAG:</span> Rotate View</div>
            <div><span className="text-white">SCROLL:</span> Zoom In/Out</div>
            <div><span className="text-white">CLICK:</span> Select Node</div>
            <div><span className="text-white">SHIFT+DRAG:</span> Pan View</div>
          </div>
        </motion.div>
      </div>
      
      {/* Selected Node Info */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="absolute top-1/2 right-4 transform -translate-y-1/2 pointer-events-auto"
          >
            <div className="bg-black/90 text-cyan-400 font-mono text-sm p-4 rounded border border-cyan-500/30 min-w-64">
              <div className="flex items-center space-x-2 mb-3">
                <Target className="w-5 h-5" />
                <span className="text-cyan-300 font-bold">TARGET ACQUIRED</span>
              </div>
              
              <div className="space-y-2 text-xs">
                <div>
                  <span className="text-gray-400">TYPE:</span>
                  <span className="text-white ml-2 font-semibold">{selectedNode.type}</span>
                </div>
                <div>
                  <span className="text-gray-400">NAME:</span>
                  <span className="text-white ml-2">{selectedNode.name}</span>
                </div>
                <div>
                  <span className="text-gray-400">ID:</span>
                  <span className="text-white ml-2 font-mono">{selectedNode.id}</span>
                </div>
                
                {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                  <div className="mt-3 pt-2 border-t border-cyan-500/20">
                    <div className="text-gray-400 mb-1">PROPERTIES:</div>
                    {Object.entries(selectedNode.properties).slice(0, 3).map(([key, value]) => (
                      <div key={key} className="text-xs">
                        <span className="text-gray-500">{key}:</span>
                        <span className="text-white ml-1">{String(value).substring(0, 20)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Minimap */}
      <AnimatePresence>
        {showMinimap && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute bottom-4 right-4 pointer-events-auto"
          >
            <div className="bg-black/90 border border-blue-500/30 rounded p-2">
              <div className="flex items-center space-x-2 mb-2">
                <Compass className="w-4 h-4 text-blue-400" />
                <span className="text-blue-300 font-mono text-xs font-bold">RADAR</span>
              </div>
              <div className="w-32 h-32 bg-blue-950/50 border border-blue-500/20 rounded relative overflow-hidden">
                {/* Minimap grid */}
                <div className="absolute inset-0 opacity-20">
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className="absolute border-blue-500/20" style={{
                      left: `${i * 12.5}%`,
                      top: 0,
                      width: '1px',
                      height: '100%',
                      borderLeft: '1px solid'
                    }} />
                  ))}
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className="absolute border-blue-500/20" style={{
                      top: `${i * 12.5}%`,
                      left: 0,
                      height: '1px',
                      width: '100%',
                      borderTop: '1px solid'
                    }} />
                  ))}
                </div>
                
                {/* Camera indicator */}
                <div className="absolute top-1/2 left-1/2 w-2 h-2 bg-yellow-400 rounded-full transform -translate-x-1/2 -translate-y-1/2" />
                
                {/* Scanning effect */}
                <div className="absolute inset-0 border border-green-500/50 rounded animate-pulse" />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Enhanced Camera Controls
const GameCameraControls = ({ onCameraChange, autoRotate = false }) => {
  const { camera, gl } = useThree()
  const controlsRef = useRef()
  
  useFrame(() => {
    if (controlsRef.current && onCameraChange) {
      onCameraChange(camera.position)
    }
  })
  
  return (
    <OrbitControls
      ref={controlsRef}
      args={[camera, gl.domElement]}
      enableDamping
      dampingFactor={0.05}
      enableZoom
      enablePan
      enableRotate
      autoRotate={autoRotate}
      autoRotateSpeed={0.5}
      minDistance={50}
      maxDistance={2000}
      maxPolarAngle={Math.PI}
      minPolarAngle={0}
    />
  )
}

// Main Gaming Graph Visualizer Component
const GamingGraphVisualizer = ({ graphData, onNodeSelect }) => {
  const [selectedNode, setSelectedNode] = useState(null)
  const [cameraPosition, setCameraPosition] = useState({ x: 0, y: 0, z: 300 })
  const [showMinimap, setShowMinimap] = useState(true)
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({
    showProducts: true,
    showPlants: true,
    showStorage: true,
    showGroups: true,
    showEntities: true
  })
  const [autoRotate, setAutoRotate] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  
  // Process graph data for 3D positioning
  const processedData = useMemo(() => {
    if (!graphData?.nodes) return { nodes: [], edges: [] }
    
    // Enhanced 3D positioning with clustering
    const nodes = graphData.nodes.map((node, index) => {
      // Cluster nodes by type
      const typeOffset = {
        'Product': { x: 0, y: 0, z: 0 },
        'Plant': { x: 200, y: 0, z: 0 },
        'StorageLocation': { x: -200, y: 0, z: 0 },
        'Group': { x: 0, y: 200, z: 0 },
        'Entity': { x: 0, y: -200, z: 0 }
      }[node.type] || { x: 0, y: 0, z: 0 }
      
      // Add some randomness for natural distribution
      const spread = 80
      const angle = (index / graphData.nodes.length) * Math.PI * 2
      const radius = Math.sqrt(index) * 15
      
      return {
        ...node,
        position: {
          x: typeOffset.x + Math.cos(angle) * radius + (Math.random() - 0.5) * spread,
          y: typeOffset.y + Math.sin(angle) * radius + (Math.random() - 0.5) * spread,
          z: typeOffset.z + (Math.random() - 0.5) * spread
        }
      }
    })
    
    const edges = (graphData.edges || []).map(edge => ({
      ...edge,
      source: nodes.find(n => n.id === edge.source),
      target: nodes.find(n => n.id === edge.target)
    })).filter(edge => edge.source && edge.target)
    
    return { nodes, edges }
  }, [graphData])
  
  // Calculate node distance from camera
  const calculateDistance = useCallback((nodePosition) => {
    return Math.sqrt(
      Math.pow(nodePosition.x - cameraPosition.x, 2) +
      Math.pow(nodePosition.y - cameraPosition.y, 2) +
      Math.pow(nodePosition.z - cameraPosition.z, 2)
    )
  }, [cameraPosition])
  
  const handleNodeSelect = useCallback((node) => {
    setSelectedNode(node)
    if (onNodeSelect) onNodeSelect(node)
  }, [onNodeSelect])
  
  const handleReset = useCallback(() => {
    setCameraPosition({ x: 0, y: 0, z: 300 })
    setSelectedNode(null)
  }, [])
  
  // Filter nodes based on current filters
  const filteredNodes = useMemo(() => {
    return processedData.nodes.filter(node => {
      switch (node.type) {
        case 'Product': return filters.showProducts
        case 'Plant': return filters.showPlants
        case 'StorageLocation': return filters.showStorage
        case 'Group': return filters.showGroups
        case 'Entity': return filters.showEntities
        default: return true
      }
    })
  }, [processedData.nodes, filters])
  
  const stats = useMemo(() => ({
    totalNodes: filteredNodes.length,
    totalEdges: processedData.edges.length,
    products: filteredNodes.filter(n => n.type === 'Product').length,
    plants: filteredNodes.filter(n => n.type === 'Plant').length,
    storage: filteredNodes.filter(n => n.type === 'StorageLocation').length,
    groups: filteredNodes.filter(n => n.type === 'Group').length
  }), [filteredNodes, processedData.edges])
  
  return (
    <div className="relative w-full h-full bg-gray-900 overflow-hidden">
      {/* 3D Canvas */}
      <Canvas
        className="absolute inset-0"
        camera={{ position: [0, 0, 300], fov: 75 }}
        gl={{ antialias: true, alpha: false }}
        onCreated={({ gl }) => {
          gl.setClearColor('#0a0a0a')
        }}
      >
        {/* Lighting */}
        <ambientLight intensity={0.3} />
        <pointLight position={[100, 100, 100]} intensity={0.8} />
        <pointLight position={[-100, -100, -100]} intensity={0.4} color="#4FFFEF" />
        
        {/* Environment */}
        <Environment preset="night" />
        
        {/* Camera Controls */}
        <GameCameraControls 
          onCameraChange={setCameraPosition}
          autoRotate={autoRotate}
        />
        
        {/* Render Nodes */}
        {filteredNodes.map(node => {
          const distance = calculateDistance(node.position)
          return (
            <GraphNode
              key={node.id}
              node={node}
              selected={selectedNode?.id === node.id}
              distance={distance}
              onSelect={handleNodeSelect}
              cameraPosition={cameraPosition}
            />
          )
        })}
        
        {/* Render Edges */}
        {processedData.edges.map((edge, index) => {
          if (!edge.source || !edge.target) return null
          const distance = (calculateDistance(edge.source.position) + calculateDistance(edge.target.position)) / 2
          return (
            <GraphEdge
              key={`edge-${index}`}
              edge={edge}
              visible={distance < 600}
              distance={distance}
            />
          )
        })}
        
        {/* Performance Stats */}
        <Stats />
      </Canvas>
      
      {/* Gaming HUD */}
      <GamingHUD
        selectedNode={selectedNode}
        cameraPosition={cameraPosition}
        stats={stats}
        onToggleMap={() => setShowMinimap(!showMinimap)}
        onToggleFilters={() => setShowFilters(!showFilters)}
        onReset={handleReset}
        filters={filters}
        showMinimap={showMinimap}
        isPlaying={autoRotate}
      />
      
      {/* Filter Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            className="absolute top-16 right-4 bg-black/90 border border-purple-500/30 rounded p-4 min-w-64"
          >
            <div className="flex items-center space-x-2 mb-4">
              <Filter className="w-5 h-5 text-purple-400" />
              <span className="text-purple-300 font-mono font-bold">FILTERS</span>
            </div>
            
            <div className="space-y-3">
              {Object.entries(filters).map(([key, value]) => (
                <label key={key} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={value}
                    onChange={(e) => setFilters(prev => ({ ...prev, [key]: e.target.checked }))}
                    className="w-4 h-4 text-purple-500 bg-gray-900 border-purple-500/30 rounded focus:ring-purple-500"
                  />
                  <span className="text-white text-sm">
                    {key.replace('show', '').replace(/([A-Z])/g, ' $1').trim()}
                  </span>
                  <span className="text-gray-400 text-xs">
                    ({stats[key.replace('show', '').toLowerCase() + 's'] || stats[key.replace('show', '').toLowerCase()] || 0})
                  </span>
                </label>
              ))}
            </div>
            
            <div className="mt-4 pt-3 border-t border-purple-500/20">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRotate}
                  onChange={(e) => setAutoRotate(e.target.checked)}
                  className="w-4 h-4 text-purple-500 bg-gray-900 border-purple-500/30 rounded focus:ring-purple-500"
                />
                <span className="text-white text-sm">Auto Rotate</span>
              </label>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default GamingGraphVisualizer