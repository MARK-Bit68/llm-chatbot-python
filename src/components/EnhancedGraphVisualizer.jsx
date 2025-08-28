import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import * as THREE from 'three'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { 
  OrbitControls, 
  Text, 
  Sphere, 
  Line, 
  Html,
  Stats,
  Environment,
  Stars,
  Float,
  Sparkles
} from '@react-three/drei'
import { 
  Network, 
  Compass, 
  Search, 
  Filter,
  Eye,
  RotateCcw,
  BarChart3,
  Package,
  Box,
  Globe,
  Factory,
  MapPin,
  Zap,
  Target,
  Layers
} from 'lucide-react'

// Enhanced Node Component with rich visual feedback
const EnhancedNode = ({ node, selected, onSelect, isHovered, distance }) => {
  const meshRef = useRef()
  const [hovered, setHovered] = useState(false)
  const [isAnimating, setIsAnimating] = useState(false)
  
  // Node configuration based on type and importance
  const nodeConfig = useMemo(() => {
    const baseSize = 2
    const baseColor = '#6B7280'
    
    switch (node.type) {
      case 'Product':
        return {
          size: baseSize * 1.5,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#10B981',
          icon: Package,
          glow: true,
          pulse: true
        }
      case 'Category':
        return {
          size: baseSize * 3,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#8B5CF6',
          icon: Box,
          glow: true,
          pulse: false
        }
      case 'Country':
        return {
          size: baseSize * 2.5,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#3B82F6',
          icon: Globe,
          glow: true,
          pulse: false
        }
      case 'Plant':
        return {
          size: baseSize * 2.8,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#84CC16',
          icon: Factory,
          glow: true,
          pulse: false
        }
      case 'Storage':
        return {
          size: baseSize * 2.2,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#F59E0B',
          icon: MapPin,
          glow: true,
          pulse: false
        }
      default:
        return {
          size: baseSize,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : baseColor,
          icon: Network,
          glow: false,
          pulse: false
        }
    }
  }, [node.type, selected, hovered])
  
  // Animate node
  useFrame((state) => {
    if (!meshRef.current) return
    
    const scale = selected ? 1.8 : hovered ? 1.4 : 1
    meshRef.current.scale.lerp(new THREE.Vector3(scale, scale, scale), 0.1)
    
    // Floating animation for selected or hovered nodes
    if (selected || hovered) {
      meshRef.current.position.y = node.y + Math.sin(state.clock.elapsedTime * 2) * 0.5
    } else {
      meshRef.current.position.y = node.y
    }
    
    // Rotation for selected nodes
    if (selected) {
      meshRef.current.rotation.y += 0.02
    }
  })
  
  const handleClick = useCallback(() => {
    setIsAnimating(true)
    onSelect(node)
    setTimeout(() => setIsAnimating(false), 500)
  }, [node, onSelect])
  
  const handlePointerOver = useCallback(() => {
    setHovered(true)
  }, [])
  
  const handlePointerOut = useCallback(() => {
    setHovered(false)
  }, [])
  
  return (
    <group position={[node.x || 0, node.y || 0, node.z || 0]}>
      {/* Main node sphere */}
      <mesh
        ref={meshRef}
        onClick={handleClick}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
      >
        <sphereGeometry args={[nodeConfig.size, 16, 16]} />
        <meshStandardMaterial 
          color={nodeConfig.color}
          emissive={nodeConfig.color}
          emissiveIntensity={selected ? 0.4 : hovered ? 0.3 : 0}
          transparent
          opacity={0.9}
          metalness={0.8}
          roughness={0.2}
        />
      </mesh>
      
      {/* Glow effect for important nodes */}
      {nodeConfig.glow && (selected || hovered) && (
        <Sphere args={[nodeConfig.size * 1.8, 16, 16]}>
          <meshStandardMaterial
            color={nodeConfig.color}
            transparent
            opacity={0.3}
            emissive={nodeConfig.color}
            emissiveIntensity={0.6}
          />
        </Sphere>
      )}
      
      {/* Sparkles for selected nodes */}
      {selected && (
        <Sparkles
          count={30}
          scale={nodeConfig.size * 3}
          size={3}
          speed={0.8}
          color={nodeConfig.color}
        />
      )}
      
      {/* Node Label */}
      {(selected || hovered) && (
        <Html position={[0, nodeConfig.size + 3, 0]} center>
          <div className="bg-black/90 text-white px-3 py-2 rounded-lg text-sm whitespace-nowrap border border-white/20">
            <div className="font-semibold">{node.name || node.id}</div>
            <div className="text-xs opacity-75">{node.type}</div>
          </div>
        </Html>
      )}
    </group>
  )
}

// Enhanced Edge Component with flow animations
const EnhancedEdge = ({ edge, sourceNode, targetNode, isVisible }) => {
  const lineRef = useRef()
  const [flowProgress, setFlowProgress] = useState(0)
  
  // Edge configuration based on type
  const edgeConfig = useMemo(() => {
    switch (edge.type) {
      case 'BELONGS_TO':
        return { color: '#00FF88', width: 3, dashArray: [0, 0], flowSpeed: 2 }
      case 'BRANDED_AS':
        return { color: '#FF8800', width: 3, dashArray: [5, 5], flowSpeed: 1.5 }
      case 'SOLD_IN':
        return { color: '#0088FF', width: 3, dashArray: [10, 5], flowSpeed: 1.8 }
      case 'OPERATES_IN':
        return { color: '#0088FF', width: 3, dashArray: [10, 5], flowSpeed: 1.8 }
      case 'MANUFACTURED_AT':
        return { color: '#BB00FF', width: 3, dashArray: [15, 5], flowSpeed: 2.2 }
      case 'PART_OF':
        return { color: '#00FFFF', width: 3, dashArray: [20, 5], flowSpeed: 1.6 }
      default:
        return { color: '#888888', width: 2, dashArray: [0, 0], flowSpeed: 1 }
    }
  }, [edge.type])
  
  // Animate edge flow
  useFrame((state) => {
    if (!lineRef.current || !lineRef.current.material) return
    
    const time = state.clock.elapsedTime
    const flowOpacity = 0.7 + Math.sin(time * edgeConfig.flowSpeed) * 0.3
    lineRef.current.material.opacity = flowOpacity
    
    // Update flow progress
    setFlowProgress((time * edgeConfig.flowSpeed) % 1)
  })
  
  if (!isVisible || !sourceNode || !targetNode) return null
  
  // Create curved path for edges
  const curvePoints = useMemo(() => {
    const start = new THREE.Vector3(sourceNode.x || 0, sourceNode.y || 0, sourceNode.z || 0)
    const end = new THREE.Vector3(targetNode.x || 0, targetNode.y || 0, targetNode.z || 0)
    
    // Create a curved path
    const midPoint = start.clone().lerp(end, 0.5)
    midPoint.y += Math.random() * 30 - 15 // Random height variation
    
    return [start, midPoint, end]
  }, [sourceNode, targetNode])
  
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
        opacity={0.7}
      />
      
      {/* Flow particles */}
      <Float speed={1} rotationIntensity={0.5} floatIntensity={0.5}>
        <Sphere args={[0.4, 8, 8]} position={curvePoints[1]}>
          <meshStandardMaterial
            color={edgeConfig.color}
            emissive={edgeConfig.color}
            emissiveIntensity={0.8}
          />
        </Sphere>
      </Float>
    </group>
  )
}

// Camera Controls Component
const EnhancedCameraControls = ({ onCameraChange, autoRotate }) => {
  const { camera } = useThree()
  
  useFrame(() => {
    if (onCameraChange) {
      onCameraChange({
        x: camera.position.x,
        y: camera.position.y,
        z: camera.position.z
      })
    }
  })
  
  return (
    <OrbitControls
      enablePan={true}
      enableZoom={true}
      enableRotate={true}
      autoRotate={autoRotate}
      autoRotateSpeed={0.3}
      maxDistance={3000}
      minDistance={50}
      dampingFactor={0.05}
      enableDamping={true}
    />
  )
}

// Main Enhanced Graph Visualizer Component
const EnhancedGraphVisualizer = ({ 
  data, 
  selectedRelationships = [], 
  onNodeSelect,
  className = "" 
}) => {
  const [autoRotate, setAutoRotate] = useState(false)
  const [showStats, setShowStats] = useState(false)
  const [cameraPosition, setCameraPosition] = useState({ x: 0, y: 0, z: 0 })
  const [selectedNode, setSelectedNode] = useState(null)
  const [viewMode, setViewMode] = useState('hierarchical') // 'hierarchical', 'force', 'circular'
  
  // Process and filter data with intelligent layout
  const processedData = useMemo(() => {
    if (!data || !data.nodes || !data.links) {
      return { nodes: [], edges: [] }
    }
    
    // Group nodes by type for intelligent positioning
    const nodesByType = {}
    data.nodes.forEach(node => {
      const type = node.type || 'Unknown'
      if (!nodesByType[type]) nodesByType[type] = []
      nodesByType[type].push(node)
    })
    
    // Enhanced hierarchical layout
    const layoutConfig = {
      'Product': { 
        center: { x: 0, y: 0, z: 0 }, 
        radius: 200, 
        layers: 3,
        color: '#10B981'
      },
      'Category': { 
        center: { x: 0, y: 150, z: 0 }, 
        radius: 120, 
        layers: 2,
        color: '#8B5CF6'
      },
      'Country': { 
        center: { x: -250, y: 0, z: 100 }, 
        radius: 150, 
        layers: 2,
        color: '#3B82F6'
      },
      'Plant': { 
        center: { x: 250, y: -100, z: -50 }, 
        radius: 100, 
        layers: 2,
        color: '#84CC16'
      },
      'Storage': { 
        center: { x: 200, y: 120, z: 0 }, 
        radius: 110, 
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
          const layerRadius = config.radius * (0.3 + (layer * 0.3))
          const nodesInLayer = Math.ceil(typeNodes.length / config.layers)
          const layerIndex = Math.floor(index / config.layers)
          const angle = (layerIndex / nodesInLayer) * Math.PI * 2
          const yOffset = (layer - 1) * 50
          
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
          id: node.id || `node-${index}`,
          ...position,
          layoutType: type,
          layoutConfig: config
        })
      })
    })
    
    // Process edges and filter by selected relationships
    const edges = data.links
      .filter(edge => {
        if (selectedRelationships.length === 0) return true
        return selectedRelationships.includes(edge.type)
      })
      .map(edge => {
        const sourceNode = nodes.find(n => n.id === edge.source)
        const targetNode = nodes.find(n => n.id === edge.target)
        return {
          ...edge,
          source: sourceNode,
          target: targetNode
        }
      })
      .filter(edge => edge.source && edge.target)
    
    return { nodes, edges }
  }, [data, selectedRelationships])
  
  const handleNodeSelect = useCallback((node) => {
    setSelectedNode(node)
    if (onNodeSelect) {
      onNodeSelect(node)
    }
  }, [onNodeSelect])
  
  const handleReset = useCallback(() => {
    setSelectedNode(null)
    setAutoRotate(false)
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
    <div className={`relative w-full h-full bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 ${className}`}>
      <Canvas
        camera={{ position: [0, 300, 1200], fov: 60 }}
        gl={{ 
          antialias: true, 
          alpha: true,
          powerPreference: "high-performance"
        }}
        onCreated={({ gl }) => {
          gl.setClearColor('#0F172A', 1)
          gl.setPixelRatio(Math.min(window.devicePixelRatio, 2))
        }}
      >
        {/* Environment */}
        <Environment preset="night" />
        <Stars radius={300} depth={150} count={12000} factor={8} saturation={0} fade speed={1} />
        
        {/* Lighting */}
        <ambientLight intensity={0.4} />
        <pointLight position={[300, 300, 300]} intensity={1.5} color="#4FFFEF" />
        <pointLight position={[-300, -300, -300]} intensity={1.0} color="#FF6B6B" />
        <directionalLight position={[0, 300, 0]} intensity={1.2} castShadow />
        
        {/* Camera Controls */}
        <EnhancedCameraControls 
          onCameraChange={setCameraPosition}
          autoRotate={autoRotate}
        />
        
        {/* Render Nodes */}
        {processedData.nodes.map(node => (
          <EnhancedNode
            key={node.id}
            node={node}
            selected={selectedNode?.id === node.id}
            onSelect={handleNodeSelect}
            distance={0}
          />
        ))}
        
        {/* Render Edges */}
        {processedData.edges.map((edge, index) => (
          <EnhancedEdge
            key={`edge-${index}`}
            edge={edge}
            sourceNode={edge.source}
            targetNode={edge.target}
            isVisible={true}
          />
        ))}
        
        {/* Stats */}
        {showStats && <Stats />}
      </Canvas>
      
      {/* Minimal Overlay Controls */}
      <div className="absolute top-4 left-4 flex flex-col gap-2">
        <button
          onClick={() => setAutoRotate(!autoRotate)}
          className="p-2 bg-black/60 hover:bg-black/80 rounded-lg transition-colors backdrop-blur-sm border border-white/10"
          title="Toggle Auto-Rotation"
        >
          <RotateCcw className={`w-4 h-4 text-white ${autoRotate ? 'text-green-400' : ''}`} />
        </button>
        <button
          onClick={handleReset}
          className="p-2 bg-black/60 hover:bg-black/80 rounded-lg transition-colors backdrop-blur-sm border border-white/10"
          title="Reset View"
        >
          <Compass className="w-4 h-4 text-white" />
        </button>
        <button
          onClick={() => setShowStats(!showStats)}
          className="p-2 bg-black/60 hover:bg-black/80 rounded-lg transition-colors backdrop-blur-sm border border-white/10"
          title="Toggle Stats"
        >
          <BarChart3 className="w-4 h-4 text-white" />
        </button>
      </div>
      
      {/* Minimal Info Panel */}
      <div className="absolute bottom-4 left-4 bg-black/70 p-3 rounded-lg text-white text-xs backdrop-blur-sm border border-white/10">
        <div className="flex items-center gap-2 mb-2">
          <Network className="w-4 h-4" />
          <span className="font-semibold">Network</span>
        </div>
        <div className="space-y-1">
          <div className="flex justify-between">
            <span>Nodes:</span>
            <span className="text-blue-400 font-medium">{processedData.nodes.length}</span>
          </div>
          <div className="flex justify-between">
            <span>Connections:</span>
            <span className="text-green-400 font-medium">{processedData.edges.length}</span>
          </div>
        </div>
      </div>
      
      {/* Minimal Legend */}
      <div className="absolute top-4 right-4 bg-black/70 p-3 rounded-lg text-white text-xs backdrop-blur-sm border border-white/10">
        <div className="font-semibold mb-2">Node Types</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span>Products</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-purple-500"></div>
            <span>Categories</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
            <span>Countries</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-400"></div>
            <span>Plants</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EnhancedGraphVisualizer
