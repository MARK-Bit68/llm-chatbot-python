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
  Stars
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
  MapPin
} from 'lucide-react'

// Enhanced Node Component
const EnhancedNode = ({ node, selected, onSelect, isHovered }) => {
  const meshRef = useRef()
  const [hovered, setHovered] = useState(false)
  
  // Node configuration based on type
  const nodeConfig = useMemo(() => {
    const baseSize = 2
    const baseColor = '#6B7280'
    
    switch (node.type) {
      case 'Product':
        return {
          size: baseSize * 1.2,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#10B981',
          icon: Package
        }
      case 'Category':
        return {
          size: baseSize * 2.5,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#8B5CF6',
          icon: Box
        }
      case 'Country':
        return {
          size: baseSize * 2,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#3B82F6',
          icon: Globe
        }
      case 'Plant':
        return {
          size: baseSize * 2.2,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#84CC16',
          icon: Factory
        }
      case 'Storage':
        return {
          size: baseSize * 1.8,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : '#F59E0B',
          icon: MapPin
        }
      default:
        return {
          size: baseSize,
          color: selected ? '#FFFF00' : hovered ? '#00FFFF' : baseColor,
          icon: Network
        }
    }
  }, [node.type, selected, hovered])
  
  const handleClick = useCallback(() => {
    onSelect(node)
  }, [node, onSelect])
  
  const handlePointerOver = useCallback(() => {
    setHovered(true)
  }, [])
  
  const handlePointerOut = useCallback(() => {
    setHovered(false)
  }, [])
  
  return (
    <group position={[node.x || 0, node.y || 0, node.z || 0]}>
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
          emissiveIntensity={selected ? 0.3 : hovered ? 0.2 : 0}
          transparent
          opacity={0.8}
        />
      </mesh>
      
      {/* Node Label */}
      {selected && (
        <Html position={[0, nodeConfig.size + 2, 0]} center>
          <div className="bg-black/80 text-white px-2 py-1 rounded text-xs whitespace-nowrap">
            {node.name || node.id}
          </div>
        </Html>
      )}
    </group>
  )
}

// Enhanced Edge Component
const EnhancedEdge = ({ edge, sourceNode, targetNode }) => {
  const points = useMemo(() => {
    if (!sourceNode || !targetNode) return []
    
    const start = new THREE.Vector3(sourceNode.x || 0, sourceNode.y || 0, sourceNode.z || 0)
    const end = new THREE.Vector3(targetNode.x || 0, targetNode.y || 0, targetNode.z || 0)
    
    return [start, end]
  }, [sourceNode, targetNode])
  
  if (points.length < 2) return null
  
  return (
    <Line
      points={points}
      color="#4B5563"
      lineWidth={1}
      transparent
      opacity={0.6}
    />
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
      autoRotateSpeed={0.5}
      maxDistance={1000}
      minDistance={10}
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
  
  // Process and filter data
  const processedData = useMemo(() => {
    if (!data || !data.nodes || !data.links) {
      return { nodes: [], edges: [] }
    }
    
    // Process nodes
    const nodes = data.nodes.map((node, index) => ({
      ...node,
      id: node.id || `node-${index}`,
      x: node.x || (Math.random() - 0.5) * 200,
      y: node.y || (Math.random() - 0.5) * 200,
      z: node.z || (Math.random() - 0.5) * 200
    }))
    
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
      <div className={`flex items-center justify-center h-96 bg-gray-900 rounded-lg ${className}`}>
        <div className="text-white text-center">
          <Network className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p>No graph data available</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className={`relative w-full h-96 bg-gray-900 rounded-lg overflow-hidden ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 100], fov: 60 }}
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
        {processedData.nodes.map(node => (
          <EnhancedNode
            key={node.id}
            node={node}
            selected={selectedNode?.id === node.id}
            onSelect={handleNodeSelect}
          />
        ))}
        
        {/* Render Edges */}
        {processedData.edges.map((edge, index) => (
          <EnhancedEdge
            key={`edge-${index}`}
            edge={edge}
            sourceNode={edge.source}
            targetNode={edge.target}
          />
        ))}
        
        {/* Stats */}
        {showStats && <Stats />}
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
          <div>Nodes: {processedData.nodes.length}</div>
          <div>Edges: {processedData.edges.length}</div>
          <div>Camera: [{Math.round(cameraPosition.x)}, {Math.round(cameraPosition.y)}, {Math.round(cameraPosition.z)}]</div>
        </div>
      </div>
    </div>
  )
}

export default EnhancedGraphVisualizer
