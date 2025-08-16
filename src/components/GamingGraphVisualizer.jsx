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
          <div className=\"bg-black/80 text-white px-2 py-1 rounded text-xs whitespace-nowrap\">
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
    <div className=\"absolute inset-0 pointer-events-none\">
      {/* Top Left - Main Stats */}
      <div className=\"absolute top-4 left-4 pointer-events-auto\">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className=\"bg-black/80 text-green-400 font-mono text-xs p-3 rounded border border-green-500/30\"
        >
          <div className=\"flex items-center space-x-2 mb-2\">
            <Network className=\"w-4 h-4\" />
            <span className=\"text-green-300 font-bold\">GRAPH NAVIGATOR v2.0</span>
          </div>
          <div className=\"space-y-1 text-xs\">
            <div>NODES: <span className=\"text-white\">{stats?.totalNodes || 0}</span></div>
            <div>EDGES: <span className=\"text-white\">{stats?.totalEdges || 0}</span></div>
            <div>POS: <span className=\"text-white\">
              [{cameraPosition.x.toFixed(0)}, {cameraPosition.y.toFixed(0)}, {cameraPosition.z.toFixed(0)}]
            </span></div>
          </div>
        </motion.div>
      </div>
      
      {/* Top Right - Quick Actions */}
      <div className=\"absolute top-4 right-4 pointer-events-auto\">
        <div className=\"flex space-x-2\">
          <button
            onClick={onToggleMap}
            className={`p-2 rounded border transition-colors ${\n              showMinimap \n                ? 'bg-blue-500/20 border-blue-500 text-blue-400' \n                : 'bg-black/80 border-gray-500/30 text-gray-400 hover:text-white'\n            }`}
            title=\"Toggle Minimap\"
          >
            <Map className=\"w-4 h-4\" />
          </button>\n          \n          <button\n            onClick={onToggleFilters}\n            className=\"p-2 bg-black/80 border border-gray-500/30 text-gray-400 hover:text-white rounded transition-colors\"\n            title=\"Toggle Filters\"\n          >\n            <Filter className=\"w-4 h-4\" />\n          </button>\n          \n          <button\n            onClick={onReset}\n            className=\"p-2 bg-black/80 border border-gray-500/30 text-gray-400 hover:text-white rounded transition-colors\"\n            title=\"Reset View\"\n          >\n            <RotateCcw className=\"w-4 h-4\" />\n          </button>\n        </div>\n      </div>\n      \n      {/* Bottom Left - Controls Help */}\n      <div className=\"absolute bottom-4 left-4 pointer-events-auto\">\n        <motion.div \n          initial={{ opacity: 0, y: 20 }}\n          animate={{ opacity: 1, y: 0 }}\n          className=\"bg-black/80 text-amber-400 font-mono text-xs p-3 rounded border border-amber-500/30 max-w-xs\"\n        >\n          <div className=\"flex items-center space-x-2 mb-2\">\n            <Gamepad2 className=\"w-4 h-4\" />\n            <span className=\"text-amber-300 font-bold\">CONTROLS</span>\n          </div>\n          <div className=\"space-y-1 text-xs\">\n            <div><span className=\"text-white\">DRAG:</span> Rotate View</div>\n            <div><span className=\"text-white\">SCROLL:</span> Zoom In/Out</div>\n            <div><span className=\"text-white\">CLICK:</span> Select Node</div>\n            <div><span className=\"text-white\">SHIFT+DRAG:</span> Pan View</div>\n          </div>\n        </motion.div>\n      </div>\n      \n      {/* Selected Node Info */}\n      <AnimatePresence>\n        {selectedNode && (\n          <motion.div\n            initial={{ opacity: 0, x: 20 }}\n            animate={{ opacity: 1, x: 0 }}\n            exit={{ opacity: 0, x: 20 }}\n            className=\"absolute top-1/2 right-4 transform -translate-y-1/2 pointer-events-auto\"\n          >\n            <div className=\"bg-black/90 text-cyan-400 font-mono text-sm p-4 rounded border border-cyan-500/30 min-w-64\">\n              <div className=\"flex items-center space-x-2 mb-3\">\n                <Target className=\"w-5 h-5\" />\n                <span className=\"text-cyan-300 font-bold\">TARGET ACQUIRED</span>\n              </div>\n              \n              <div className=\"space-y-2 text-xs\">\n                <div>\n                  <span className=\"text-gray-400\">TYPE:</span>\n                  <span className=\"text-white ml-2 font-semibold\">{selectedNode.type}</span>\n                </div>\n                <div>\n                  <span className=\"text-gray-400\">NAME:</span>\n                  <span className=\"text-white ml-2\">{selectedNode.name}</span>\n                </div>\n                <div>\n                  <span className=\"text-gray-400\">ID:</span>\n                  <span className=\"text-white ml-2 font-mono\">{selectedNode.id}</span>\n                </div>\n                \n                {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (\n                  <div className=\"mt-3 pt-2 border-t border-cyan-500/20\">\n                    <div className=\"text-gray-400 mb-1\">PROPERTIES:</div>\n                    {Object.entries(selectedNode.properties).slice(0, 3).map(([key, value]) => (\n                      <div key={key} className=\"text-xs\">\n                        <span className=\"text-gray-500\">{key}:</span>\n                        <span className=\"text-white ml-1\">{String(value).substring(0, 20)}</span>\n                      </div>\n                    ))}\n                  </div>\n                )}\n              </div>\n            </div>\n          </motion.div>\n        )}\n      </AnimatePresence>\n      \n      {/* Minimap */}\n      <AnimatePresence>\n        {showMinimap && (\n          <motion.div\n            initial={{ opacity: 0, scale: 0.8 }}\n            animate={{ opacity: 1, scale: 1 }}\n            exit={{ opacity: 0, scale: 0.8 }}\n            className=\"absolute bottom-4 right-4 pointer-events-auto\"\n          >\n            <div className=\"bg-black/90 border border-blue-500/30 rounded p-2\">\n              <div className=\"flex items-center space-x-2 mb-2\">\n                <Compass className=\"w-4 h-4 text-blue-400\" />\n                <span className=\"text-blue-300 font-mono text-xs font-bold\">RADAR</span>\n              </div>\n              <div className=\"w-32 h-32 bg-blue-950/50 border border-blue-500/20 rounded relative overflow-hidden\">\n                {/* Minimap grid */}\n                <div className=\"absolute inset-0 opacity-20\">\n                  {[...Array(8)].map((_, i) => (\n                    <div key={i} className=\"absolute border-blue-500/20\" style={{\n                      left: `${i * 12.5}%`,\n                      top: 0,\n                      width: '1px',\n                      height: '100%',\n                      borderLeft: '1px solid'\n                    }} />\n                  ))}\n                  {[...Array(8)].map((_, i) => (\n                    <div key={i} className=\"absolute border-blue-500/20\" style={{\n                      top: `${i * 12.5}%`,\n                      left: 0,\n                      height: '1px',\n                      width: '100%',\n                      borderTop: '1px solid'\n                    }} />\n                  ))}\n                </div>\n                \n                {/* Camera indicator */}\n                <div className=\"absolute top-1/2 left-1/2 w-2 h-2 bg-yellow-400 rounded-full transform -translate-x-1/2 -translate-y-1/2\" />\n                \n                {/* Scanning effect */}\n                <div className=\"absolute inset-0 border border-green-500/50 rounded animate-pulse\" />\n              </div>\n            </div>\n          </motion.div>\n        )}\n      </AnimatePresence>\n    </div>\n  )\n}\n\n// Enhanced Camera Controls\nconst GameCameraControls = ({ onCameraChange, autoRotate = false }) => {\n  const { camera, gl } = useThree()\n  const controlsRef = useRef()\n  \n  useFrame(() => {\n    if (controlsRef.current && onCameraChange) {\n      onCameraChange(camera.position)\n    }\n  })\n  \n  return (\n    <OrbitControls\n      ref={controlsRef}\n      args={[camera, gl.domElement]}\n      enableDamping\n      dampingFactor={0.05}\n      enableZoom\n      enablePan\n      enableRotate\n      autoRotate={autoRotate}\n      autoRotateSpeed={0.5}\n      minDistance={50}\n      maxDistance={2000}\n      maxPolarAngle={Math.PI}\n      minPolarAngle={0}\n    />\n  )\n}\n\n// Main Gaming Graph Visualizer Component\nconst GamingGraphVisualizer = ({ graphData, onNodeSelect }) => {\n  const [selectedNode, setSelectedNode] = useState(null)\n  const [cameraPosition, setCameraPosition] = useState({ x: 0, y: 0, z: 300 })\n  const [showMinimap, setShowMinimap] = useState(true)\n  const [showFilters, setShowFilters] = useState(false)\n  const [filters, setFilters] = useState({\n    showProducts: true,\n    showPlants: true,\n    showStorage: true,\n    showGroups: true,\n    showEntities: true\n  })\n  const [autoRotate, setAutoRotate] = useState(false)\n  const [isFullscreen, setIsFullscreen] = useState(false)\n  \n  // Process graph data for 3D positioning\n  const processedData = useMemo(() => {\n    if (!graphData?.nodes) return { nodes: [], edges: [] }\n    \n    // Enhanced 3D positioning with clustering\n    const nodes = graphData.nodes.map((node, index) => {\n      // Cluster nodes by type\n      const typeOffset = {\n        'Product': { x: 0, y: 0, z: 0 },\n        'Plant': { x: 200, y: 0, z: 0 },\n        'StorageLocation': { x: -200, y: 0, z: 0 },\n        'Group': { x: 0, y: 200, z: 0 },\n        'Entity': { x: 0, y: -200, z: 0 }\n      }[node.type] || { x: 0, y: 0, z: 0 }\n      \n      // Add some randomness for natural distribution\n      const spread = 80\n      const angle = (index / graphData.nodes.length) * Math.PI * 2\n      const radius = Math.sqrt(index) * 15\n      \n      return {\n        ...node,\n        position: {\n          x: typeOffset.x + Math.cos(angle) * radius + (Math.random() - 0.5) * spread,\n          y: typeOffset.y + Math.sin(angle) * radius + (Math.random() - 0.5) * spread,\n          z: typeOffset.z + (Math.random() - 0.5) * spread\n        }\n      }\n    })\n    \n    const edges = (graphData.edges || []).map(edge => ({\n      ...edge,\n      source: nodes.find(n => n.id === edge.source),\n      target: nodes.find(n => n.id === edge.target)\n    })).filter(edge => edge.source && edge.target)\n    \n    return { nodes, edges }\n  }, [graphData])\n  \n  // Calculate node distance from camera\n  const calculateDistance = useCallback((nodePosition) => {\n    return Math.sqrt(\n      Math.pow(nodePosition.x - cameraPosition.x, 2) +\n      Math.pow(nodePosition.y - cameraPosition.y, 2) +\n      Math.pow(nodePosition.z - cameraPosition.z, 2)\n    )\n  }, [cameraPosition])\n  \n  const handleNodeSelect = useCallback((node) => {\n    setSelectedNode(node)\n    if (onNodeSelect) onNodeSelect(node)\n  }, [onNodeSelect])\n  \n  const handleReset = useCallback(() => {\n    setCameraPosition({ x: 0, y: 0, z: 300 })\n    setSelectedNode(null)\n  }, [])\n  \n  // Filter nodes based on current filters\n  const filteredNodes = useMemo(() => {\n    return processedData.nodes.filter(node => {\n      switch (node.type) {\n        case 'Product': return filters.showProducts\n        case 'Plant': return filters.showPlants\n        case 'StorageLocation': return filters.showStorage\n        case 'Group': return filters.showGroups\n        case 'Entity': return filters.showEntities\n        default: return true\n      }\n    })\n  }, [processedData.nodes, filters])\n  \n  const stats = useMemo(() => ({\n    totalNodes: filteredNodes.length,\n    totalEdges: processedData.edges.length,\n    products: filteredNodes.filter(n => n.type === 'Product').length,\n    plants: filteredNodes.filter(n => n.type === 'Plant').length,\n    storage: filteredNodes.filter(n => n.type === 'StorageLocation').length,\n    groups: filteredNodes.filter(n => n.type === 'Group').length\n  }), [filteredNodes, processedData.edges])\n  \n  return (\n    <div className=\"relative w-full h-full bg-gray-900 overflow-hidden\">\n      {/* 3D Canvas */}\n      <Canvas\n        className=\"absolute inset-0\"\n        camera={{ position: [0, 0, 300], fov: 75 }}\n        gl={{ antialias: true, alpha: false }}\n        onCreated={({ gl }) => {\n          gl.setClearColor('#0a0a0a')\n        }}\n      >\n        {/* Lighting */}\n        <ambientLight intensity={0.3} />\n        <pointLight position={[100, 100, 100]} intensity={0.8} />\n        <pointLight position={[-100, -100, -100]} intensity={0.4} color=\"#4FFFEF\" />\n        \n        {/* Environment */}\n        <Environment preset=\"night\" />\n        \n        {/* Camera Controls */}\n        <GameCameraControls \n          onCameraChange={setCameraPosition}\n          autoRotate={autoRotate}\n        />\n        \n        {/* Render Nodes */}\n        {filteredNodes.map(node => {\n          const distance = calculateDistance(node.position)\n          return (\n            <GraphNode\n              key={node.id}\n              node={node}\n              selected={selectedNode?.id === node.id}\n              distance={distance}\n              onSelect={handleNodeSelect}\n              cameraPosition={cameraPosition}\n            />\n          )\n        })}\n        \n        {/* Render Edges */}\n        {processedData.edges.map((edge, index) => {\n          if (!edge.source || !edge.target) return null\n          const distance = (calculateDistance(edge.source.position) + calculateDistance(edge.target.position)) / 2\n          return (\n            <GraphEdge\n              key={`edge-${index}`}\n              edge={edge}\n              visible={distance < 600}\n              distance={distance}\n            />\n          )\n        })}\n        \n        {/* Performance Stats */}\n        <Stats />\n      </Canvas>\n      \n      {/* Gaming HUD */}\n      <GamingHUD\n        selectedNode={selectedNode}\n        cameraPosition={cameraPosition}\n        stats={stats}\n        onToggleMap={() => setShowMinimap(!showMinimap)}\n        onToggleFilters={() => setShowFilters(!showFilters)}\n        onReset={handleReset}\n        filters={filters}\n        showMinimap={showMinimap}\n        isPlaying={autoRotate}\n      />\n      \n      {/* Filter Panel */}\n      <AnimatePresence>\n        {showFilters && (\n          <motion.div\n            initial={{ opacity: 0, x: 300 }}\n            animate={{ opacity: 1, x: 0 }}\n            exit={{ opacity: 0, x: 300 }}\n            className=\"absolute top-16 right-4 bg-black/90 border border-purple-500/30 rounded p-4 min-w-64\"\n          >\n            <div className=\"flex items-center space-x-2 mb-4\">\n              <Filter className=\"w-5 h-5 text-purple-400\" />\n              <span className=\"text-purple-300 font-mono font-bold\">FILTERS</span>\n            </div>\n            \n            <div className=\"space-y-3\">\n              {Object.entries(filters).map(([key, value]) => (\n                <label key={key} className=\"flex items-center space-x-3 cursor-pointer\">\n                  <input\n                    type=\"checkbox\"\n                    checked={value}\n                    onChange={(e) => setFilters(prev => ({ ...prev, [key]: e.target.checked }))}\n                    className=\"w-4 h-4 text-purple-500 bg-gray-900 border-purple-500/30 rounded focus:ring-purple-500\"\n                  />\n                  <span className=\"text-white text-sm\">\n                    {key.replace('show', '').replace(/([A-Z])/g, ' $1').trim()}\n                  </span>\n                  <span className=\"text-gray-400 text-xs\">\n                    ({stats[key.replace('show', '').toLowerCase() + 's'] || stats[key.replace('show', '').toLowerCase()] || 0})\n                  </span>\n                </label>\n              ))}\n            </div>\n            \n            <div className=\"mt-4 pt-3 border-t border-purple-500/20\">\n              <label className=\"flex items-center space-x-3 cursor-pointer\">\n                <input\n                  type=\"checkbox\"\n                  checked={autoRotate}\n                  onChange={(e) => setAutoRotate(e.target.checked)}\n                  className=\"w-4 h-4 text-purple-500 bg-gray-900 border-purple-500/30 rounded focus:ring-purple-500\"\n                />\n                <span className=\"text-white text-sm\">Auto Rotate</span>\n              </label>\n            </div>\n          </motion.div>\n        )}\n      </AnimatePresence>\n    </div>\n  )\n}\n\nexport default GamingGraphVisualizer