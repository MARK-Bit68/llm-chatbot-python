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
  RotateCcw,
  Maximize2,
  TrendingUp,
  Users,
  Box,
  Activity,
  TrendingDown,
  BarChart3
} from 'lucide-react'

// Gaming-style Graph Node Component
const GraphNode = ({ node, selected, distance, onSelect, cameraPosition }) => {
  const meshRef = useRef()
  const [hovered, setHovered] = useState(false)
  const [isMounted, setIsMounted] = useState(true)
  
  // Component mount tracking to prevent React error #300
  useEffect(() => {
    setIsMounted(true)
    return () => {
      setIsMounted(false)
    }
  }, [])
  
  // Level of Detail based on distance
  const lod = useMemo(() => {
    if (distance > 1000) return 0 // Very far - don't render
    if (distance > 500) return 1  // Far - simple geometry
    if (distance > 200) return 2  // Medium - normal geometry
    return 3 // Close - full detail
  }, [distance])
  
  // Don't render if too far
  if (lod === 0) return null
  
  // Animate node on hover/selection with mount checking
  useFrame((state) => {
    // CRITICAL: Skip if component is unmounted to prevent React error #300
    if (!isMounted || !meshRef.current) return
    
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
  
  // Enhanced node colors with better visibility and consistency
  const nodeColor = useMemo(() => {
    if (selected) return '#FFFF00' // Bright Yellow when selected
    if (hovered) return '#00FFFF' // Bright Cyan when hovered
    
    // Use layout-consistent colors for better visual hierarchy
    if (node.layoutConfig?.color) {
      return node.layoutConfig.color
    }
    
    // Enhanced bright colors matching edge colors for consistency
    switch (node.type) {
      case 'Product': return '#00FF88'        // Bright Green (Core)
      case 'Category': return '#BB00FF'       // Bright Purple (Classification)
      case 'Brand': return '#FF8800'          // Bright Orange (Brand)
      case 'Country': return '#0088FF'        // Bright Blue (Geography)
      case 'Region': return '#00FFFF'         // Bright Cyan (Geography)
      case 'Plant': return '#88FF00'          // Bright Lime (Operations)
      case 'ManufacturingPlant': return '#44FF44' // Bright Green (Operations)
      case 'Metadata': return '#AAAAAA'       // Light Gray (Meta)
      default: return '#AAAAAA'               // Light Gray (Unknown)
    }
  }, [node.type, node.layoutConfig, selected, hovered])
  
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
          emissiveIntensity={selected ? 0.4 : hovered ? 0.15 : 0.02}
          shininess={100}
          transparent
          opacity={selected || hovered ? 1.0 : 0.9}
        />
      </mesh>
      
      {/* Enhanced node label with better visibility */}
      {(selected || hovered || distance < 150) && (
        <Html
          position={[0, nodeSize + 3, 0]}
          center
          style={{
            pointerEvents: 'none',
            userSelect: 'none'
          }}
        >
          <div 
            className="px-2 py-1 rounded text-xs font-bold whitespace-nowrap border-2 shadow-lg"
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.9)',
              color: nodeColor,
              borderColor: nodeColor,
              boxShadow: `0 0 15px ${nodeColor}60`,
              textShadow: `0 0 5px ${nodeColor}`
            }}
          >
            {node.name}
          </div>
        </Html>
      )}
      
      {/* Enhanced glow effect for better visual hierarchy */}
      {(selected || hovered || node.type === 'Group') && (
        <mesh position={[0, 0, 0]} scale={[2, 2, 2]}>
          <sphereGeometry args={[nodeSize * 1.3, 32, 32]} />
          <meshBasicMaterial 
            color={nodeColor}
            transparent
            opacity={selected ? 0.3 : hovered ? 0.2 : 0.1}
          />
        </mesh>
      )}
      
      {/* Additional ring effect for selected nodes */}
      {selected && (
        <mesh position={[0, 0, 0]} rotation={[Math.PI/2, 0, 0]}>
          <ringGeometry args={[nodeSize * 1.5, nodeSize * 2, 32]} />
          <meshBasicMaterial 
            color={nodeColor}
            transparent
            opacity={0.6}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}
    </group>
  )
}

// Focus on core graph visualization - temporal features removed

// Dynamic Group Label Component with Accurate Cluster Positioning
const GroupLabel = ({ config, nodeType, nodeCount, distance, cameraPosition }) => {
  const labelRef = useRef()
  const lineRef = useRef()
  const [isMounted, setIsMounted] = useState(true)
  
  // Component mount tracking to prevent React error #300
  useEffect(() => {
    setIsMounted(true)
    return () => {
      setIsMounted(false)
    }
  }, [])
  
  // Don't render if config is invalid or if too close (labels are for overview)
  if (!config || !config.center || distance < 200) return null
  
  // Calculate actual cluster bounds for more accurate positioning
  const clusterBounds = useMemo(() => {
    const baseRadius = config.radius || 50
    const center = config.center
    
    return {
      minX: center.x - baseRadius,
      maxX: center.x + baseRadius,
      minY: center.y - baseRadius * 0.5,
      maxY: center.y + baseRadius * 0.5,
      minZ: center.z - baseRadius,
      maxZ: center.z + baseRadius,
      center: center // Include center in bounds for easy access
    }
  }, [config])
  
  // Smart label positioning with improved accuracy - pointing to actual cluster edges
  const labelPosition = useMemo(() => {
    const baseRadius = config.radius || 50
    
    // Position labels to point to the actual visible edge of each cluster
    const positionMap = {
      'Product': { 
        x: clusterBounds.center.x, 
        y: clusterBounds.maxY + 50, // Point to top of product cluster
        z: clusterBounds.center.z,
        anchorPoint: { x: clusterBounds.center.x, y: clusterBounds.maxY, z: clusterBounds.center.z }
      },
      'Category': { 
        x: clusterBounds.center.x - baseRadius * 0.2, 
        y: clusterBounds.maxY + 70, // Point to top edge
        z: clusterBounds.center.z + baseRadius * 0.3,
        anchorPoint: { x: clusterBounds.center.x, y: clusterBounds.maxY, z: clusterBounds.center.z }
      },
      'Brand': { 
        x: clusterBounds.maxX + 40, // Point to right edge of brand cluster
        y: clusterBounds.center.y + 60, 
        z: clusterBounds.center.z,
        anchorPoint: { x: clusterBounds.maxX, y: clusterBounds.center.y, z: clusterBounds.center.z }
      },
      'Country': { 
        x: clusterBounds.minX - 50, // Point to left edge of country cluster
        y: clusterBounds.center.y + 40, 
        z: clusterBounds.center.z,
        anchorPoint: { x: clusterBounds.minX, y: clusterBounds.center.y, z: clusterBounds.center.z }
      },
      'Region': { 
        x: clusterBounds.minX - 60, // Point to left edge, above countries
        y: clusterBounds.maxY + 50, 
        z: clusterBounds.center.z,
        anchorPoint: { x: clusterBounds.minX, y: clusterBounds.maxY, z: clusterBounds.center.z }
      },
      'Plant': { 
        x: clusterBounds.maxX + 45, // Point to right edge of plant cluster
        y: clusterBounds.minY - 20, 
        z: clusterBounds.center.z,
        anchorPoint: { x: clusterBounds.maxX, y: clusterBounds.minY, z: clusterBounds.center.z }
      },
      'ManufacturingPlant': { 
        x: clusterBounds.maxX + 50, 
        y: clusterBounds.minY - 40, 
        z: clusterBounds.center.z,
        anchorPoint: { x: clusterBounds.maxX, y: clusterBounds.minY, z: clusterBounds.center.z }
      },
      'Metadata': { 
        x: clusterBounds.center.x, 
        y: clusterBounds.minY - 60, // Point to bottom of metadata cluster
        z: clusterBounds.center.z,
        anchorPoint: { x: clusterBounds.center.x, y: clusterBounds.minY, z: clusterBounds.center.z }
      }
    }
    
    return positionMap[nodeType] || {
      x: clusterBounds.center.x,
      y: clusterBounds.center.y + baseRadius + 50,
      z: clusterBounds.center.z,
      anchorPoint: { x: clusterBounds.center.x, y: clusterBounds.center.y + baseRadius, z: clusterBounds.center.z }
    }
  }, [config, nodeType, clusterBounds])
  
  // Scale based on distance - labels should be more visible when zoomed out
  const scale = useMemo(() => Math.max(0.8, Math.min(1.3, distance / 600)), [distance])
  const opacity = useMemo(() => Math.max(0.8, Math.min(1.0, distance / 450)), [distance])
  
  // Animate gentle floating with label rotation toward camera
  useFrame((state) => {
    // CRITICAL: Skip if component is unmounted to prevent React error #300
    if (!isMounted || !labelRef.current || !labelPosition) return
    
    if (labelRef.current && labelPosition) {
      // Gentle floating animation
      labelRef.current.position.y = labelPosition.y + Math.sin(state.clock.elapsedTime * 0.5) * 2
      
      // Optional: Make labels face camera for better readability
      const cameraPos = new THREE.Vector3().copy(state.camera.position)
      const labelPos = new THREE.Vector3(labelPosition.x, labelRef.current.position.y, labelPosition.z)
      labelRef.current.lookAt(cameraPos)
    }
  })
  
  return (
    <group ref={labelRef}>
      {/* Improved connection line pointing to actual cluster edge */}
      <Line
        ref={lineRef}
        points={[
          [labelPosition.x, labelPosition.y - 15, labelPosition.z],
          [labelPosition.anchorPoint.x, labelPosition.anchorPoint.y, labelPosition.anchorPoint.z]
        ]}
        color={config.color || '#6B7280'}
        lineWidth={2}
        transparent
        opacity={opacity * 0.6}
        dashed
        dashSize={4}
        gapSize={3}
      />
      
      {/* Cluster boundary indicator (subtle outline) */}
      <Line
        points={[
          [clusterBounds.minX, clusterBounds.center.y, clusterBounds.minZ],
          [clusterBounds.maxX, clusterBounds.center.y, clusterBounds.minZ],
          [clusterBounds.maxX, clusterBounds.center.y, clusterBounds.maxZ],
          [clusterBounds.minX, clusterBounds.center.y, clusterBounds.maxZ],
          [clusterBounds.minX, clusterBounds.center.y, clusterBounds.minZ]
        ]}
        color={config.color || '#6B7280'}
        lineWidth={1}
        transparent
        opacity={opacity * 0.2}
        dashed
        dashSize={2}
        gapSize={4}
      />
      
      {/* Label positioned accurately relative to cluster */}
      <group position={[labelPosition.x, labelPosition.y, labelPosition.z]}>
        <Html
          center
          style={{
            pointerEvents: 'none',
            userSelect: 'none'
          }}
        >
          <div 
            className="text-center backdrop-blur-sm"
            style={{
              opacity: opacity * 0.95,
              transform: `scale(${Math.min(scale, 1.15)})`,
              transformOrigin: 'center'
            }}
          >
            <div 
              className="font-bold text-base mb-1 drop-shadow-lg px-2 py-1 rounded bg-black/40"
              style={{ 
                color: config.color || '#6B7280',
                textShadow: '2px 2px 4px rgba(0,0,0,0.9)',
                border: `1px solid ${config.color || '#6B7280'}40`
              }}
            >
              {config.description || nodeType}
            </div>
            <div className="text-gray-300 text-xs font-medium drop-shadow-md bg-black/30 px-1 rounded">
              {nodeCount} {nodeCount === 1 ? 'node' : 'nodes'}
            </div>
          </div>
        </Html>
        
        {/* Improved indicator dot with pulsing animation */}
        <mesh position={[0, -12, 0]}>
          <sphereGeometry args={[2, 12, 12]} />
          <meshBasicMaterial 
            color={config.color || '#6B7280'}
            transparent
            opacity={opacity * 0.9}
          />
        </mesh>
      </group>
    </group>
  )
}

// Intuitive Node-to-Node Connection Component
const GraphEdge = ({ edge, visible, distance, sourceNode, targetNode }) => {
  const lineRef = useRef()
  const arrowRef = useRef()
  const flowRef = useRef()
  
  // Safari cleanup on unmount
  useEffect(() => {
    return () => {
      // Clean up refs to prevent Safari memory leaks
      if (lineRef.current && lineRef.current.material) {
        lineRef.current.material.dispose()
      }
      if (arrowRef.current && arrowRef.current.material) {
        arrowRef.current.material.dispose()
      }
      if (flowRef.current && flowRef.current.material) {
        flowRef.current.material.dispose()
      }
    }
  }, [])
  
  // Adaptive LOD based on relationship importance and distance
  const lod = useMemo(() => {
    if (distance > 2500) return 0 // Don't render
    if (distance > 1200) return 1 // Basic connection
    if (distance > 600) return 2  // Enhanced connection
    return 3 // Full interactive connection
  }, [distance])
  
  if (!visible || lod === 0 || !edge.source || !edge.target || !edge.source.position || !edge.target.position) return null
  
  // Enhanced edge colors with better contrast and brightness
  const edgeColor = useMemo(() => {
    switch (edge.type) {
      case 'BELONGS_TO': return '#00FF88'        // Bright Green - Product → Category
      case 'BRANDED_AS': return '#FF8800'        // Bright Orange - Product → Brand  
      case 'SOLD_IN': return '#0088FF'           // Bright Blue - Product → Country
      case 'OPERATES_IN': return '#0088FF'       // Bright Blue - Product → Country (alternative)
      case 'MANUFACTURED_AT': return '#BB00FF'   // Bright Purple - Product → Plant
      case 'PART_OF': return '#00FFFF'           // Bright Cyan - Country → Region
      default: return '#888888'                  // Gray - Unknown
    }
  }, [edge.type])

  // Add glow effect color for enhanced visibility
  const glowColor = useMemo(() => {
    switch (edge.type) {
      case 'BELONGS_TO': return '#00FF88'
      case 'BRANDED_AS': return '#FF8800'  
      case 'SOLD_IN': return '#0088FF'
      case 'OPERATES_IN': return '#0088FF'
      case 'MANUFACTURED_AT': return '#BB00FF'
      case 'PART_OF': return '#00FFFF'
      default: return '#888888'
    }
  }, [edge.type])
  
  // Calculate precise node-to-node connection points
  const connectionGeometry = useMemo(() => {
    // Get actual node positions
    const sourceCenter = new THREE.Vector3(
      edge.source.position.x, 
      edge.source.position.y, 
      edge.source.position.z
    )
    const targetCenter = new THREE.Vector3(
      edge.target.position.x, 
      edge.target.position.y, 
      edge.target.position.z
    )
    
    // Calculate direction vector
    const direction = new THREE.Vector3()
    direction.subVectors(targetCenter, sourceCenter).normalize()
    
    // Get node sizes (estimated based on type)
    const sourceRadius = edge.source.type === 'Product' ? 3 : 
                        edge.source.type === 'Plant' ? 5 : 
                        edge.source.type === 'Group' ? 8 : 4
    const targetRadius = edge.target.type === 'Product' ? 3 : 
                        edge.target.type === 'Plant' ? 5 : 
                        edge.target.type === 'Group' ? 8 : 4
    
    // Calculate surface connection points (not center points)
    const sourceConnectionPoint = sourceCenter.clone().add(direction.clone().multiplyScalar(sourceRadius + 1))
    const targetConnectionPoint = targetCenter.clone().sub(direction.clone().multiplyScalar(targetRadius + 1))
    
    // Create curved path for better visual flow
    const distance = sourceConnectionPoint.distanceTo(targetConnectionPoint)
    const curvature = Math.min(distance * 0.2, 30) // Adaptive curvature
    
    // Calculate control point for bezier curve
    const midPoint = new THREE.Vector3().lerpVectors(sourceConnectionPoint, targetConnectionPoint, 0.5)
    const perpendicular = new THREE.Vector3(-direction.z, 0, direction.x).normalize()
    const controlPoint = midPoint.clone().add(perpendicular.multiplyScalar(curvature))
    
    // Generate smooth curve points
    const curvePoints = []
    for (let i = 0; i <= 20; i++) {
      const t = i / 20
      const point = new THREE.Vector3()
      
      // Quadratic bezier curve
      const invT = 1 - t
      point.copy(sourceConnectionPoint).multiplyScalar(invT * invT)
      point.add(controlPoint.clone().multiplyScalar(2 * invT * t))
      point.add(targetConnectionPoint.clone().multiplyScalar(t * t))
      
      curvePoints.push(point)
    }
    
    return {
      sourcePoint: sourceConnectionPoint,
      targetPoint: targetConnectionPoint,
      curvePoints: curvePoints,
      direction: direction,
      arrowPosition: curvePoints[Math.floor(curvePoints.length * 0.8)], // Arrow near target
      labelPosition: controlPoint
    }
  }, [edge.source.position, edge.target.position, edge.source.type, edge.target.type])
  
  // Static edge properties for clean visualization
  
  // Component mount tracking to prevent React error #300
  const [isMounted, setIsMounted] = useState(true)
  
  useEffect(() => {
    setIsMounted(true)
    return () => {
      setIsMounted(false)
    }
  }, [])

  // Safari-optimized animation with proper cleanup and mount checking
  useFrame((state) => {
    // Define maxDistance locally for performance culling
    const maxDistance = 2000
    
    // CRITICAL: Skip if component is unmounted to prevent React error #300
    if (!isMounted || !visible || distance > maxDistance) return
    
    const time = state.clock.elapsedTime
    
    // Throttle animation updates for Safari performance
    if (state.frameloop === false) return
    
    try {
      // Simple edge animation with safety checks
      if (lineRef.current && lineRef.current.material && lod >= 2) {
        const baseOpacity = 0.6
        const flowOpacity = baseOpacity + Math.sin(time * 1.5) * 0.2
        lineRef.current.material.opacity = flowOpacity
      }
      
      // Simple arrow animation with safety checks
      if (arrowRef.current && arrowRef.current.scale && lod >= 2) {
        const { direction, arrowPosition } = connectionGeometry
        if (direction && arrowPosition) {
          arrowRef.current.lookAt(
            arrowPosition.x + direction.x,
            arrowPosition.y + direction.y,
            arrowPosition.z + direction.z
          )
          
          const scale = 1.0 + Math.sin(time * 2) * 0.1
          arrowRef.current.scale.setScalar(scale)
        }
      }
      
      // Simple flow particles with safety checks
      if (flowRef.current && flowRef.current.position && lod === 3) {
        const particleSpeed = 0.5
        const progress = (time * particleSpeed) % 1
        const pointIndex = Math.floor(progress * (connectionGeometry.curvePoints.length - 1))
        const flowPoint = connectionGeometry.curvePoints[pointIndex]
        
        if (flowPoint && flowRef.current.material) {
          flowRef.current.position.copy(flowPoint)
          flowRef.current.material.opacity = 0.6 * Math.sin(progress * Math.PI)
          flowRef.current.scale.setScalar(1.0)
        }
      }
    } catch (error) {
      // Silent error handling for Safari WebGL context issues
      console.warn('GraphEdge animation error (likely Safari WebGL):', error)
    }
  })
  
  return (
    <group>
      {/* Background Glow for Depth (higher LOD only) */}
      {lod >= 2 && (
        <Line
          points={connectionGeometry.curvePoints}
          color={edgeColor}
          lineWidth={lod === 3 ? 6 : 4}
          transparent
          opacity={0.2}
        />
      )}
      
      {/* Main Curved Connection Line */}
      <Line
        ref={lineRef}
        points={connectionGeometry.curvePoints}
        color={edgeColor}
        lineWidth={lod === 3 ? 4 : lod === 2 ? 3 : 2}
        transparent
        opacity={lod === 3 ? 0.9 : 0.8}
      />
      
      {/* Connection Point Indicators */}
      {lod >= 2 && (
        <>
          {/* Source connection point */}
          <mesh position={connectionGeometry.sourcePoint}>
            <sphereGeometry args={[1, 8, 8]} />
            <meshBasicMaterial 
              color={edgeColor} 
              transparent 
              opacity={0.7}
            />
          </mesh>
          
          {/* Target connection point */}
          <mesh position={connectionGeometry.targetPoint}>
            <sphereGeometry args={[1, 8, 8]} />
            <meshBasicMaterial 
              color={edgeColor} 
              transparent 
              opacity={0.7}
            />
          </mesh>
        </>
      )}
      
      {/* Directional Arrow at optimal position */}
      {lod >= 2 && (
        <group ref={arrowRef} position={connectionGeometry.arrowPosition}>
          <mesh>
            <coneGeometry args={lod === 3 ? [3, 8, 8] : [2.5, 6, 6]} />
            <meshBasicMaterial 
              color={edgeColor} 
              transparent 
              opacity={1.0}
            />
          </mesh>
        </group>
      )}
      
      {/* Flow Particle for Animation (highest detail only) */}
      {lod === 3 && (
        <mesh ref={flowRef}>
          <sphereGeometry args={[0.8, 6, 6]} />
          <meshBasicMaterial 
            color={edgeColor} 
            transparent 
            opacity={0.8}
          />
        </mesh>
      )}
      
      {/* Relationship Type Label */}
      {lod >= 2 && distance < 500 && (
        <Html
          position={connectionGeometry.labelPosition}
          center
          style={{
            pointerEvents: 'none',
            userSelect: 'none'
          }}
        >
          <div 
            className="px-2 py-1 rounded text-xs font-semibold whitespace-nowrap border shadow-lg"
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.85)',
              color: edgeColor,
              borderColor: edgeColor,
              boxShadow: `0 0 8px ${edgeColor}30`
            }}
          >
            {edge.type.replace(/_/g, '→').replace(/TO/g, '').replace(/AS/g, '').replace(/IN/g, '').replace(/AT/g, '').replace(/OF/g, '').trim()}
          </div>
        </Html>
      )}
    </group>
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
  const [isMounted, setIsMounted] = useState(true)
  
  // Component mount tracking to prevent React error #300
  useEffect(() => {
    setIsMounted(true)
    return () => {
      setIsMounted(false)
    }
  }, [])
  
  useFrame(() => {
    // CRITICAL: Skip if component is unmounted to prevent React error #300
    if (!isMounted || !controlsRef.current || !onCameraChange) return
    
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
const GamingGraphVisualizer = ({ graphData, onNodeSelect, edgeFilters: externalEdgeFilters, selectedNode: externalSelectedNode, nodeFilters: externalNodeFilters }) => {
  const [cameraPosition, setCameraPosition] = useState({ x: 0, y: 150, z: 800 }) // Start zoomed out for hierarchical view
  const [showMinimap, setShowMinimap] = useState(true)
  const [showFilters, setShowFilters] = useState(false)
  
  // Focus on core graph visualization
  
  // Use external node filters from props, fallback to defaults
  const filters = externalNodeFilters || {
    showProducts: true,
    showPlants: true,
    showStorage: true,
    showRevenue: true,
    showProfit: true,
    showGroups: true
  }
  
  
  // Use external edge filters from props, fallback to defaults
  const edgeFilters = externalEdgeFilters || {
    showBelongsTo: true,
    showBrandedAs: true,
    showSoldIn: false,
    showPartOf: true,
    showManufacturedAt: false,
    focusMode: 'none'
  }
  
  // Debug disabled to prevent build errors
  
  // Use external selected node from props
  const selectedNode = externalSelectedNode
  const [autoRotate, setAutoRotate] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  
  // Safari WebGL context and memory management
  const [webglContextLost, setWebglContextLost] = useState(false)
  
  // Detect Safari browser for specific optimizations
  const isSafari = useMemo(() => {
    if (typeof navigator !== 'undefined') {
      return /^((?!chrome|android).)*safari/i.test(navigator.userAgent)
    }
    return false
  }, [])
  
  // Safari-specific cleanup when relationships change
  useEffect(() => {
    if (isSafari && Object.values(edgeFilters).some(enabled => enabled)) {
      // Throttle relationship changes in Safari to prevent crashes
      const timeoutId = setTimeout(() => {
        // Force garbage collection hints for Safari
        if (window.gc) {
          window.gc()
        }
      }, 100)
      
      return () => clearTimeout(timeoutId)
    }
  }, [edgeFilters, isSafari])
  
  // Clean graph data processing without temporal complexity
  
  // Process graph data for intuitive hierarchical 3D positioning
  const processedData = useMemo(() => {
    if (!graphData?.nodes) return { nodes: [], edges: [] }
    
    // Group nodes by type for intelligent positioning
    const nodesByType = {}
    graphData.nodes.forEach(node => {
      const type = node.type || 'Unknown'
      if (!nodesByType[type]) nodesByType[type] = []
      nodesByType[type].push(node)
    })
    
    // Hierarchical layout configuration for AI Enhanced SOP dataset
    const layoutConfig = {
      // Core business entities at center with clear separation
      'Product': { 
        center: { x: 0, y: 0, z: 0 }, 
        radius: 150, 
        layers: 3,
        description: 'Products (Core)',
        color: '#10B981'
      },
      // Categories form rings around products
      'Category': { 
        center: { x: 0, y: 120, z: 0 }, 
        radius: 80, 
        layers: 1,
        description: 'Categories (15 types)',
        color: '#8B5CF6'
      },
      // Brands positioned strategically
      'Brand': { 
        center: { x: 150, y: 80, z: 0 }, 
        radius: 60, 
        layers: 1,
        description: 'Brands (5 total)',
        color: '#F59E0B'
      },
      // Geographic hierarchy
      'Country': { 
        center: { x: -150, y: 0, z: 80 }, 
        radius: 100, 
        layers: 2,
        description: 'Countries (26)',
        color: '#3B82F6'
      },
      'Region': { 
        center: { x: -150, y: 120, z: 80 }, 
        radius: 50, 
        layers: 1,
        description: 'Regions (5)',
        color: '#06B6D4'
      },
      // Operational entities
      'Plant': { 
        center: { x: 200, y: -80, z: -50 }, 
        radius: 40, 
        layers: 1,
        description: 'Plants',
        color: '#84CC16'
      },
      'ManufacturingPlant': { 
        center: { x: 200, y: -120, z: -50 }, 
        radius: 60, 
        layers: 1,
        description: 'Manufacturing',
        color: '#22C55E'
      },
      // Metadata separate
      'Metadata': { 
        center: { x: 0, y: -200, z: 120 }, 
        radius: 40, 
        layers: 1,
        description: 'Metadata',
        color: '#6B7280'
      }
    }
    
    const nodes = []
    
    // Position each node type using intelligent clustering
    Object.entries(nodesByType).forEach(([type, typeNodes]) => {
      const config = layoutConfig[type] || layoutConfig['Product']
      
      typeNodes.forEach((node, index) => {
        let position
        
        if (type === 'Product') {
          // Products: Spiral layout in multiple layers for better distribution
          const layer = index % config.layers
          const layerRadius = config.radius * (0.3 + (layer * 0.35))
          const nodesInLayer = Math.ceil(typeNodes.length / config.layers)
          const layerIndex = Math.floor(index / config.layers)
          const angle = (layerIndex / nodesInLayer) * Math.PI * 2
          const yOffset = (layer - 1) * 40 // Vertical separation between layers
          
          position = {
            x: config.center.x + Math.cos(angle) * layerRadius,
            y: config.center.y + yOffset + (Math.random() - 0.5) * 20,
            z: config.center.z + Math.sin(angle) * layerRadius
          }
        } else if (type === 'Category' || type === 'Country') {
          // Categories and Countries: Organized rings
          const angle = (index / typeNodes.length) * Math.PI * 2
          const radiusVariation = config.radius + (Math.random() - 0.5) * 30
          
          position = {
            x: config.center.x + Math.cos(angle) * radiusVariation,
            y: config.center.y + (Math.random() - 0.5) * 20,
            z: config.center.z + Math.sin(angle) * radiusVariation
          }
        } else {
          // Other types: Compact clusters
          const angle = (index / typeNodes.length) * Math.PI * 2
          const radius = config.radius * (0.5 + Math.random() * 0.5)
          
          position = {
            x: config.center.x + Math.cos(angle) * radius,
            y: config.center.y + (Math.random() - 0.5) * 30,
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
    
    const edges = (graphData.links || graphData.edges || []).map(edge => ({
      ...edge,
      source: nodes.find(n => n.id === edge.source),
      target: nodes.find(n => n.id === edge.target)
    })).filter(edge => edge.source && edge.target)
    
    return { 
      nodes, 
      edges, 
      layoutConfig,  // Include layout config for group labels
      nodesByType    // Include node counts by type
    }
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
    if (onNodeSelect) onNodeSelect(node)
  }, [onNodeSelect])
  
  const handleReset = useCallback(() => {
    setCameraPosition({ x: 0, y: 150, z: 800 }) // Reset to hierarchical overview
    if (onNodeSelect) onNodeSelect(null)
  }, [onNodeSelect])
  
  // Filter nodes based on current filters - matching actual data types
  const filteredNodes = useMemo(() => {
    return processedData.nodes.filter(node => {
      switch (node.type) {
        case 'Product': return filters.showProducts
        case 'Plant': 
        case 'ManufacturingPlant': return filters.showPlants
        case 'StorageLocation': return filters.showStorage
        case 'Category': return filters.showRevenue || filters.showGroups // Categories are part of grouping system
        case 'Brand': return filters.showProfit || filters.showGroups // Brands are part of grouping system  
        case 'Country':
        case 'Region': return filters.showGroups // Geographic entities
        case 'Metadata': return filters.showGroups // Metadata entities
        default: return filters.showGroups // Unknown types show with groups
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
        camera={{ position: [0, 150, 800], fov: 75 }}
        gl={{ 
          antialias: true, 
          alpha: false,
          // Safari-specific WebGL optimizations
          powerPreference: "high-performance",
          stencil: false,
          depth: true,
          preserveDrawingBuffer: false,
          // Prevent Safari memory leaks
          failIfMajorPerformanceCaveat: true
        }}
        onCreated={({ gl, scene }) => {
          gl.setClearColor('#0a0a0a')
          
          // Safari WebGL context optimizations
          gl.shadowMap.enabled = true
          gl.shadowMap.type = THREE.PCFSoftShadowMap
          
          // Prevent Safari context loss
          gl.getContext().getExtension('WEBGL_lose_context')
          
          // Memory management for Safari
          scene.autoUpdate = true
          gl.setPixelRatio(Math.min(window.devicePixelRatio, 2)) // Limit pixel ratio for Safari performance
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
        
        {/* Render Filtered Edges */}
        {processedData.edges.map((edge, index) => {
          if (!edge.source || !edge.target) return null
          
          // Edge type filtering
          const edgeType = edge.type
          let showEdge = false
          
          // Debug edge types - removed console spam
          
          switch (edgeType) {
            case 'BELONGS_TO':
              showEdge = edgeFilters.showBelongsTo
              break
            case 'BRANDED_AS':
              showEdge = edgeFilters.showBrandedAs
              break
            case 'SOLD_IN': // Product -> Country relationship (market presence)
              showEdge = edgeFilters.showSoldIn
              break
            case 'OPERATES_IN': // Alternative naming for Product -> Country
              showEdge = edgeFilters.showSoldIn
              break
            case 'MANUFACTURED_AT': // Product -> Plant relationship (supply chain)
              showEdge = edgeFilters.showManufacturedAt
              break
            case 'PART_OF': // Country -> Region relationship (geographic hierarchy)
              showEdge = edgeFilters.showPartOf
              break
            default:
              showEdge = false // Unknown edge types hidden by default
          }
          
          if (!showEdge) return null
          
          // Focus mode filtering
          if (edgeFilters.focusMode === 'selected' && selectedNode) {
            const isConnectedToSelected = 
              edge.source.id === selectedNode.id || edge.target.id === selectedNode.id
            if (!isConnectedToSelected) return null
          }
          
          // Distance culling with density adjustment - made more permissive
          const distance = (calculateDistance(edge.source.position) + calculateDistance(edge.target.position)) / 2
          const maxDistance = edgeFilters.edgeDensity === 'high' ? 2000 : 
                             edgeFilters.edgeDensity === 'medium' ? 1500 : 1000
          
          return (
            <GraphEdge
              key={`edge-${index}`}
              edge={edge}
              visible={distance < maxDistance}
              distance={distance}
            />
          )
        })}
        
        {/* Render Dynamic Group Labels - Only show when node type is visible */}
        {processedData.layoutConfig && processedData.nodesByType && 
          Object.entries(processedData.layoutConfig).map(([nodeType, config]) => {
            const nodeCount = processedData.nodesByType[nodeType]?.length || 0
            if (nodeCount === 0 || !config || !config.center) return null
            
            // Check if this node type should be visible based on filters
            const shouldShowLabel = (() => {
              switch (nodeType) {
                case 'Product': return filters.showProducts
                case 'Plant': 
                case 'ManufacturingPlant': return filters.showPlants
                case 'StorageLocation': return filters.showStorage
                case 'Category': return filters.showRevenue || filters.showGroups
                case 'Brand': return filters.showProfit || filters.showGroups
                case 'Country':
                case 'Region': return filters.showGroups
                case 'Metadata': return filters.showGroups
                default: return filters.showGroups
              }
            })()
            
            if (!shouldShowLabel) return null // Hide label if node type is filtered out
            
            try {
              const labelDistance = calculateDistance(config.center)
              
              // Count visible nodes of this type (not just total nodes)
              const visibleNodeCount = filteredNodes.filter(node => node.type === nodeType).length
              if (visibleNodeCount === 0) return null // Hide if no visible nodes
              
              return (
                <GroupLabel
                  key={`label-${nodeType}`}
                  config={config}
                  nodeType={nodeType}
                  nodeCount={visibleNodeCount} // Use visible count, not total count
                  distance={labelDistance}
                  cameraPosition={cameraPosition}
                />
              )
            } catch (error) {
              console.warn('Error rendering group label for', nodeType, error)
              return null
            }
          })
        }
        
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
            
            {/* Node Filters */}
            <div className="space-y-3">
              <div className="text-cyan-300 font-medium text-sm mb-2">🎯 Node Types</div>
              {Object.entries(filters).map(([key, value]) => (
                <label key={key} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={value}
                    disabled={true}
                    className="w-4 h-4 text-purple-500 bg-gray-900 border-purple-500/30 rounded focus:ring-purple-500 opacity-50"
                    title="Use filters in the left panel"
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
            
            {/* Edge Filters */}
            <div className="mt-4 pt-3 border-t border-purple-500/20">
              <div className="text-amber-300 font-medium text-sm mb-3">🔗 Relationship Types</div>
              <div className="space-y-2">
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showBelongsTo}
                    onChange={(e) => setEdgeFilters(prev => ({ ...prev, showBelongsTo: e.target.checked }))}
                    className="w-3 h-3 text-green-500 bg-gray-900 border-green-500/30 rounded focus:ring-green-500"
                  />
                  <span className="text-white text-xs">Product → Category</span>
                  <span className="text-gray-400 text-xs ml-2">Portfolio</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showBrandedAs}
                    onChange={(e) => setEdgeFilters(prev => ({ ...prev, showBrandedAs: e.target.checked }))}
                    className="w-3 h-3 text-orange-500 bg-gray-900 border-orange-500/30 rounded focus:ring-orange-500"
                  />
                  <span className="text-white text-xs">Product → Brand</span>
                  <span className="text-gray-400 text-xs ml-2">Strategy</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showSoldIn}
                    onChange={(e) => setEdgeFilters(prev => ({ ...prev, showSoldIn: e.target.checked }))}
                    className="w-3 h-3 text-blue-500 bg-gray-900 border-blue-500/30 rounded focus:ring-blue-500"
                  />
                  <span className="text-white text-xs">Product → Market</span>
                  <span className="text-yellow-400 text-xs ml-2">Optimized</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showManufacturedAt}
                    onChange={(e) => setEdgeFilters(prev => ({ ...prev, showManufacturedAt: e.target.checked }))}
                    className="w-3 h-3 text-purple-500 bg-gray-900 border-purple-500/30 rounded focus:ring-purple-500"
                  />
                  <span className="text-white text-xs">Product → Plant</span>
                  <span className="text-gray-400 text-xs ml-2">Supply Chain</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={edgeFilters.showPartOf}
                    onChange={(e) => setEdgeFilters(prev => ({ ...prev, showPartOf: e.target.checked }))}
                    className="w-3 h-3 text-cyan-500 bg-gray-900 border-cyan-500/30 rounded focus:ring-cyan-500"
                  />
                  <span className="text-white text-xs">Country → Region</span>
                  <span className="text-gray-400 text-xs ml-2">Geographic</span>
                </label>
              </div>
              
              {/* Edge Density Control */}
              <div className="mt-3">
                <div className="text-amber-300 font-medium text-xs mb-2">Edge Density</div>
                <select
                  value={edgeFilters.edgeDensity}
                  onChange={(e) => setEdgeFilters(prev => ({ ...prev, edgeDensity: e.target.value }))}
                  className="w-full bg-gray-900 border border-purple-500/30 rounded text-white text-xs p-1"
                >
                  <option value="low">Low (Nearby only)</option>
                  <option value="medium">Medium (Balanced)</option>
                  <option value="high">High (All visible)</option>
                </select>
              </div>
              
              {/* Focus Mode */}
              <div className="mt-3">
                <div className="text-amber-300 font-medium text-xs mb-2">Focus Mode</div>
                <select
                  value={edgeFilters.focusMode}
                  onChange={(e) => setEdgeFilters(prev => ({ ...prev, focusMode: e.target.value }))}
                  className="w-full bg-gray-900 border border-purple-500/30 rounded text-white text-xs p-1"
                >
                  <option value="none">Show All</option>
                  <option value="selected">Selected Node Only</option>
                </select>
              </div>
            </div>
            
            {/* System Controls */}
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
      
      {/* Focus on core graph visualization without temporal complexity */}
    </div>
  )
}

export default GamingGraphVisualizer