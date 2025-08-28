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
  Environment,
  Float,
  Sparkles,
  Stars
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
  RotateCcw,
  Maximize2,
  TrendingUp,
  Users,
  Box,
  Activity,
  TrendingDown,
  BarChart3,
  Globe,
  Factory,
  Package,
  Building2,
  MapPin
} from 'lucide-react'

// Enhanced Node Component with rich interactions
const EnhancedNode = ({ node, selected, distance, onSelect, cameraPosition, isHovered }) => {
  const meshRef = useRef()
  const [hovered, setHovered] = useState(false)
  const [isMounted, setIsMounted] = useState(true)
  
  useEffect(() => {
    setIsMounted(true)
    return () => setIsMounted(false)
  }, [])
  
  // Level of Detail based on distance and node importance
  const lod = useMemo(() => {
    if (distance > 1500) return 0 // Don't render
    if (distance > 800) return 1  // Simple sphere
    if (distance > 400) return 2  // Basic geometry
    return 3 // Full detail with labels
  }, [distance])
  
  if (lod === 0) return null
  
  // Node size and color based on type and importance
  const nodeConfig = useMemo(() => {
    const baseSize = 3
    const baseColor = '#6B7280'
    
    switch (node.type) {
      case 'Product':
        return {
          size: baseSize * 1.2,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#10B981',
          icon: Package,
          glow: true
        }
      case 'Category':
        return {
          size: baseSize * 2.5,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#8B5CF6',
          icon: Box,
          glow: true
        }
      case 'Country':
        return {
          size: baseSize * 2,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#3B82F6',
          icon: Globe,
          glow: true
        }
      case 'Plant':
        return {
          size: baseSize * 2.2,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#84CC16',
          icon: Factory,
          glow: true
        }
      case 'Brand':
        return {
          size: baseSize * 1.8,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#F59E0B',
          icon: Building2,
          glow: true
        }
      default:
        return {
          size: baseSize,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : baseColor,
          icon: MapPin,
          glow: false
        }
    }
  }, [node.type, selected, hovered])
  
  // Animate node
  useFrame((state) => {
    if (!isMounted || !meshRef.current) return
    
    const scale = selected ? 1.8 : hovered ? 1.4 : 1
    meshRef.current.scale.lerp(new THREE.Vector3(scale, scale, scale), 0.1)
    
    // Floating animation
    if (selected || hovered) {
      meshRef.current.position.y = node.position.y + Math.sin(state.clock.elapsedTime * 2) * 0.8
    } else {
      meshRef.current.position.y = node.position.y
    }
    
    // Rotation for selected nodes
    if (selected) {
      meshRef.current.rotation.y += 0.02
    }
  })
  
  return (
    <group>
      {/* Main node sphere */}
      <Sphere
        ref={meshRef}
        args={[nodeConfig.size, 16, 16]}
        position={[node.position.x, node.position.y, node.position.z]}
        onClick={() => onSelect(node)}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={nodeConfig.color}
          emissive={nodeConfig.glow ? nodeConfig.color : '#000000'}
          emissiveIntensity={nodeConfig.glow ? 0.3 : 0}
          metalness={0.8}
          roughness={0.2}
        />
      </Sphere>
      
      {/* Glow effect for important nodes */}
      {nodeConfig.glow && (selected || hovered) && (
        <Sphere
          args={[nodeConfig.size * 1.5, 16, 16]}
          position={[node.position.x, node.position.y, node.position.z]}
        >
          <meshStandardMaterial
            color={nodeConfig.color}
            transparent
            opacity={0.3}
            emissive={nodeConfig.color}
            emissiveIntensity={0.5}
          />
        </Sphere>
      )}
      
      {/* Node label for close-up view */}
      {lod === 3 && (selected || hovered) && (
        <Html
          position={[node.position.x, node.position.y + nodeConfig.size + 2, node.position.z]}
          center
          distanceFactor={50}
        >
          <div className="bg-black/80 text-white px-2 py-1 rounded text-xs whitespace-nowrap">
            {node.name || node.id}
          </div>
        </Html>
      )}
      
      {/* Sparkles for selected nodes */}
      {selected && (
        <Sparkles
          position={[node.position.x, node.position.y, node.position.z]}
          count={20}
          scale={nodeConfig.size * 2}
          size={2}
          speed={0.5}
          color={nodeConfig.color}
        />
      )}
    </group>
  )
}

// Enhanced Edge Component with flow animations
const EnhancedEdge = ({ edge, visible, distance, sourceNode, targetNode }) => {
  const lineRef = useRef()
  const [isMounted, setIsMounted] = useState(true)
  
  useEffect(() => {
    setIsMounted(true)
    return () => setIsMounted(false)
  }, [])
  
  const lod = useMemo(() => {
    if (distance > 2000) return 0
    if (distance > 1000) return 1
    if (distance > 500) return 2
    return 3
  }, [distance])
  
  if (!visible || lod === 0 || !edge.source || !edge.target) return null
  
  // Edge color and style based on type
  const edgeConfig = useMemo(() => {
    switch (edge.type) {
      case 'BELONGS_TO':
        return { color: '#00FF88', width: 2, dashArray: [0, 0] }
      case 'BRANDED_AS':
        return { color: '#FF8800', width: 2, dashArray: [5, 5] }
      case 'SOLD_IN':
        return { color: '#0088FF', width: 2, dashArray: [10, 5] }
      case 'OPERATES_IN':
        return { color: '#0088FF', width: 2, dashArray: [10, 5] }
      case 'MANUFACTURED_AT':
        return { color: '#BB00FF', width: 2, dashArray: [15, 5] }
      case 'PART_OF':
        return { color: '#00FFFF', width: 2, dashArray: [20, 5] }
      default:
        return { color: '#888888', width: 1, dashArray: [0, 0] }
    }
  }, [edge.type])
  
  // Animate edge flow
  useFrame((state) => {
    if (!isMounted || !lineRef.current || !lineRef.current.material) return
    
    const time = state.clock.elapsedTime
    const flowOpacity = 0.6 + Math.sin(time * 2) * 0.2
    lineRef.current.material.opacity = flowOpacity
  })
  
  // Create curved path for edges
  const curvePoints = useMemo(() => {
    if (!edge.source.position || !edge.target.position) return []
    
    const start = new THREE.Vector3(edge.source.position.x, edge.source.position.y, edge.source.position.z)
    const end = new THREE.Vector3(edge.target.position.x, edge.target.position.y, edge.target.position.z)
    
    // Create a curved path
    const midPoint = start.clone().lerp(end, 0.5)
    midPoint.y += Math.random() * 20 - 10 // Random height variation
    
    return [start, midPoint, end]
  }, [edge.source.position, edge.target.position])
  
  if (curvePoints.length < 3) return null
  
  return (
    <group>
      {/* Main edge line */}
      <Line
        ref={lineRef}
        points={curvePoints}
        color={edgeConfig.color}
        lineWidth={edgeConfig.width}
        dashed={edgeConfig.dashArray[0] > 0}
        dashScale={edgeConfig.dashArray[0]}
        dashSize={edgeConfig.dashArray[0]}
        dashOffset={edgeConfig.dashArray[1]}
        transparent
        opacity={0.6}
      />
      
      {/* Flow particles for high LOD */}
      {lod === 3 && (
        <Float speed={1} rotationIntensity={0.5} floatIntensity={0.5}>
          <Sphere args={[0.3, 8, 8]} position={curvePoints[1]}>
            <meshStandardMaterial
              color={edgeConfig.color}
              emissive={edgeConfig.color}
              emissiveIntensity={0.5}
            />
          </Sphere>
        </Float>
      )}
    </group>
  )
}

// Enhanced Camera Controls
const EnhancedCameraControls = ({ onCameraChange, autoRotate = false }) => {
  const { camera, gl } = useThree()
  
  useEffect(() => {
    if (onCameraChange) {
      onCameraChange({
        x: camera.position.x,
        y: camera.position.y,
        z: camera.position.z
      })
    }
  }, [camera.position, onCameraChange])
  
  return (
    <OrbitControls
      args={[camera, gl.domElement]}
      enableDamping
      dampingFactor={0.05}
      enableZoom
      enablePan
      enableRotate
      autoRotate={autoRotate}
      autoRotateSpeed={0.5}
      minDistance={50}
      maxDistance={3000}
      maxPolarAngle={Math.PI}
      minPolarAngle={0}
    />
  )
}

// Main Enhanced Graph Visualizer Component
const EnhancedGraphVisualizer = ({ 
  graphData, 
  onNodeSelect, 
  edgeFilters, 
  selectedNode, 
  nodeFilters 
}) => {
  const [cameraPosition, setCameraPosition] = useState({ x: 0, y: 200, z: 1000 })
  const [autoRotate, setAutoRotate] = useState(false)
  const [showStats, setShowStats] = useState(true)
  const [showLabels, setShowLabels] = useState(false)
  
  // Process graph data with enhanced positioning
  const processedData = useMemo(() => {
    if (!graphData?.nodes) return { nodes: [], edges: [] }
    
    // Group nodes by type for intelligent positioning
    const nodesByType = {}
    graphData.nodes.forEach(node => {
      const type = node.type || 'Unknown'
      if (!nodesByType[type]) nodesByType[type] = []
      nodesByType[type].push(node)
    })
    
    // Enhanced hierarchical layout
    const layoutConfig = {
      'Product': { 
        center: { x: 0, y: 0, z: 0 }, 
        radius: 200, 
        layers: 4,
        color: '#10B981'
      },
      'Category': { 
        center: { x: 0, y: 150, z: 0 }, 
        radius: 120, 
        layers: 2,
        color: '#8B5CF6'
      },
      'Country': { 
        center: { x: -200, y: 0, z: 100 }, 
        radius: 150, 
        layers: 3,
        color: '#3B82F6'
      },
      'Plant': { 
        center: { x: 250, y: -100, z: -50 }, 
        radius: 80, 
        layers: 2,
        color: '#84CC16'
      },
      'Brand': { 
        center: { x: 180, y: 120, z: 0 }, 
        radius: 100, 
        layers: 2,
        color: '#F59E0B'
      }
    }
    
    const nodes = []
    
    // Position nodes using enhanced clustering
    Object.entries(nodesByType).forEach(([type, typeNodes]) => {
      const config = layoutConfig[type] || layoutConfig['Product']
      
      typeNodes.forEach((node, index) => {
        let position
        
        if (type === 'Product') {
          // Spiral layout for products
          const layer = index % config.layers
          const layerRadius = config.radius * (0.2 + (layer * 0.25))
          const nodesInLayer = Math.ceil(typeNodes.length / config.layers)
          const layerIndex = Math.floor(index / config.layers)
          const angle = (layerIndex / nodesInLayer) * Math.PI * 2
          const yOffset = (layer - 1.5) * 60
          
          position = {
            x: config.center.x + Math.cos(angle) * layerRadius,
            y: config.center.y + yOffset + (Math.random() - 0.5) * 30,
            z: config.center.z + Math.sin(angle) * layerRadius
          }
        } else {
          // Organized clusters for other types
          const angle = (index / typeNodes.length) * Math.PI * 2
          const radius = config.radius * (0.6 + Math.random() * 0.4)
          
          position = {
            x: config.center.x + Math.cos(angle) * radius,
            y: config.center.y + (Math.random() - 0.5) * 40,
            z: config.center.z + Math.sin(angle) * radius
          }
        }
        
        nodes.push({
          ...node,
          position,
          layoutType: type,
          layoutConfig: config
        })
      })
    })
    
    // Process edges
    const edges = (graphData.links || graphData.edges || [])
      .map(edge => ({
        ...edge,
        source: nodes.find(n => n.id === edge.source),
        target: nodes.find(n => n.id === edge.target)
      }))
      .filter(edge => edge.source && edge.target)
    
    return { nodes, edges, layoutConfig, nodesByType }
  }, [graphData])
  
  // Filter nodes and edges based on current filters
  const filteredNodes = useMemo(() => {
    return processedData.nodes.filter(node => {
      switch (node.type) {
        case 'Product': return nodeFilters?.showProducts !== false
        case 'Plant': return nodeFilters?.showPlants !== false
        case 'StorageLocation': return nodeFilters?.showStorage !== false
        case 'Category': return nodeFilters?.showRevenue !== false || nodeFilters?.showGroups !== false
        case 'Brand': return nodeFilters?.showProfit !== false || nodeFilters?.showGroups !== false
        case 'Country': return nodeFilters?.showGroups !== false
        default: return nodeFilters?.showGroups !== false
      }
    })
  }, [processedData.nodes, nodeFilters])
  
  const filteredEdges = useMemo(() => {
    return processedData.edges.filter(edge => {
      const edgeType = edge.type
      switch (edgeType) {
        case 'BELONGS_TO': return edgeFilters?.showBelongsTo
        case 'BRANDED_AS': return edgeFilters?.showBrandedAs
        case 'SOLD_IN': return edgeFilters?.showSoldIn
        case 'OPERATES_IN': return edgeFilters?.showSoldIn
        case 'MANUFACTURED_AT': return edgeFilters?.showManufacturedAt
        case 'PART_OF': return edgeFilters?.showPartOf
        default: return false
      }
    })
  }, [processedData.edges, edgeFilters])
  
  // Calculate distances for LOD
  const calculateDistance = useCallback((nodePosition) => {
    return Math.sqrt(
      Math.pow(nodePosition.x - cameraPosition.x, 2) +
      Math.pow(nodePosition.y - cameraPosition.y, 2) +
      Math.pow(nodePosition.z - cameraPosition.z, 2)
    )
  }, [cameraPosition])
  
  const handleNodeSelect = useCallback((node) => {
    if (onNodeSelect) onNodeSelect(node)
  }, [onNodeSelect])
  
  const handleReset = useCallback(() => {
    setCameraPosition({ x: 0, y: 200, z: 1000 })
    if (onNodeSelect) onNodeSelect(null)
  }, [onNodeSelect])
  
  return (
    <div className="relative w-full h-full bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 overflow-hidden">
      {/* 3D Canvas */}
      <Canvas
        className="absolute inset-0"
        camera={{ position: [0, 200, 1000], fov: 75 }}
        gl={{ 
          antialias: true, 
          alpha: false,
          powerPreference: "high-performance",
          stencil: false,
          depth: true,
          preserveDrawingBuffer: false
        }}
        onCreated={({ gl, scene }) => {
          gl.setClearColor('#0a0a0a')
          gl.shadowMap.enabled = true
          gl.shadowMap.type = THREE.PCFSoftShadowMap
          gl.setPixelRatio(Math.min(window.devicePixelRatio, 2))
        }}
      >
        {/* Environment */}
        <Environment preset="night" />
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        
        {/* Lighting */}
        <ambientLight intensity={0.4} />
        <pointLight position={[100, 100, 100]} intensity={1.0} color="#4FFFEF" />
        <pointLight position={[-100, -100, -100]} intensity={0.6} color="#FF6B6B" />
        <directionalLight position={[0, 100, 0]} intensity={0.8} castShadow />
        
        {/* Camera Controls */}
        <EnhancedCameraControls 
          onCameraChange={setCameraPosition}
          autoRotate={autoRotate}
        />
        
        {/* Render Nodes */}
        {filteredNodes.map(node => {
          const distance = calculateDistance(node.position)
          return (
            <EnhancedNode
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
        {filteredEdges.map((edge, index) => {
          if (!edge.source || !edge.target) return null
          
          const distance = (calculateDistance(edge.source.position) + calculateDistance(edge.target.position)) / 2
          const maxDistance = 2000
          
          return (
            <EnhancedEdge
              key={`edge-${index}`}
              edge={edge}
              visible={distance < maxDistance}
              distance={distance}
              sourceNode={edge.source}
              targetNode={edge.target}
            />
          )
        })}
        
        {/* Stats */}
        {showStats && <Stats />
      </Canvas>
      
      {/* Overlay Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
        <button
          onClick={() => setAutoRotate(!autoRotate)}
          className="p-2 bg-black/50 hover:bg-black/70 rounded-lg transition-colors"
          title="Toggle Auto-Rotation"
        >
          <RotateCcw className={`w-4 h-4 text-white ${autoRotate ? 'text-green-400' : ''}`} />
        </button>
        <button
          onClick={handleReset}
          className="p-2 bg-black/50 hover:bg-black/70 rounded-lg transition-colors"
          title="Reset View"
        >
          <Compass className="w-4 h-4 text-white" />
        </button>
        <button
          onClick={() => setShowStats(!showStats)}
          className="p-2 bg-black/50 hover:bg-black/70 rounded-lg transition-colors"
          title="Toggle Stats"
        >
          <BarChart3 className="w-4 h-4 text-white" />
        </button>
      </div>
      
      {/* Info Panel */}
      <div className="absolute bottom-4 left-4 bg-black/50 p-4 rounded-lg text-white text-sm">
        <div className="flex items-center gap-2 mb-2">
          <Network className="w-4 h-4" />
          <span className="font-semibold">Graph Info</span>
        </div>
        <div className="space-y-1">
          <div>Nodes: {filteredNodes.length}</div>
          <div>Edges: {filteredEdges.length}</div>
          <div>Camera: [{Math.round(cameraPosition.x)}, {Math.round(cameraPosition.y)}, {Math.round(cameraPosition.z)}]</div>
        </div>
      </div>
    </div>
  )
}

export default EnhancedGraphVisualizer
