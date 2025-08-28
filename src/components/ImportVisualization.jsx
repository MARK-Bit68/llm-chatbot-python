import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FileSpreadsheet, 
  Database, 
  Network, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  BarChart3,
  Zap,
  Globe,
  Factory,
  Package,
  Users,
  TrendingUp
} from 'lucide-react'

const ImportVisualization = ({ 
  isVisible = false, 
  importStatus = null, 
  onComplete = null,
  onError = null 
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [stepProgress, setStepProgress] = useState(0)
  const [showGraph, setShowGraph] = useState(false)
  const [graphData, setGraphData] = useState(null)
  const canvasRef = useRef(null)
  const animationRef = useRef(null)

  const steps = [
    {
      id: 'file-analysis',
      title: 'Analyzing Excel Structure',
      description: 'Detecting sheets, columns, and data types',
      icon: FileSpreadsheet,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/20'
    },
    {
      id: 'format-detection',
      title: 'Detecting Data Format',
      description: 'Identifying FMCG, Raw, or Enhanced format',
      icon: BarChart3,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
      borderColor: 'border-purple-500/20'
    },
    {
      id: 'graph-preparation',
      title: 'Preparing Graph Database',
      description: 'Clearing existing data and setting up schema',
      icon: Database,
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/10',
      borderColor: 'border-orange-500/20'
    },
    {
      id: 'node-creation',
      title: 'Creating Graph Nodes',
      description: 'Generating products, categories, and entities',
      icon: Package,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/20'
    },
    {
      id: 'relationship-building',
      title: 'Building Relationships',
      description: 'Connecting nodes with meaningful links',
      icon: Network,
      color: 'text-cyan-500',
      bgColor: 'bg-cyan-500/10',
      borderColor: 'border-cyan-500/20'
    },
    {
      id: 'connectivity-validation',
      title: 'Validating Connectivity',
      description: 'Ensuring graph integrity and performance',
      icon: Zap,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
      borderColor: 'border-yellow-500/20'
    },
    {
      id: 'finalization',
      title: 'Finalizing Import',
      description: 'Storing metadata and preparing for use',
      icon: CheckCircle,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/20'
    }
  ]

  // Simulate import progress based on real status
  useEffect(() => {
    if (!isVisible || !importStatus) return

    let step = 0
    let progress = 0

    if (importStatus.analyzing) {
      step = 0
      progress = importStatus.analyzing
    } else if (importStatus.format_detected) {
      step = 1
      progress = 100
    } else if (importStatus.preparing) {
      step = 2
      progress = importStatus.preparing
    } else if (importStatus.creating_nodes) {
      step = 3
      progress = importStatus.creating_nodes
    } else if (importStatus.building_relationships) {
      step = 4
      progress = importStatus.building_relationships
    } else if (importStatus.validating) {
      step = 5
      progress = importStatus.validating
    } else if (importStatus.completed) {
      step = 6
      progress = 100
    }

    setCurrentStep(step)
    setStepProgress(progress)

    // Show graph visualization when relationships are being built
    if (step >= 4) {
      setShowGraph(true)
    }

    // Complete when done
    if (step === 6 && progress === 100) {
      setTimeout(() => {
        if (onComplete) onComplete()
      }, 2000)
    }
  }, [isVisible, importStatus, onComplete])

  // Animated graph visualization
  useEffect(() => {
    if (!showGraph || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const nodes = []
    const edges = []

    // Create animated nodes
    for (let i = 0; i < 20; i++) {
      nodes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 2,
        radius: Math.random() * 3 + 2,
        color: `hsl(${Math.random() * 360}, 70%, 60%)`
      })
    }

    // Create edges between nearby nodes
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x
        const dy = nodes[i].y - nodes[j].y
        const distance = Math.sqrt(dx * dx + dy * dy)
        if (distance < 100) {
          edges.push({ from: i, to: j, opacity: 0 })
        }
      }
    }

    let frame = 0
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Update node positions
      nodes.forEach(node => {
        node.x += node.vx
        node.y += node.vy

        // Bounce off walls
        if (node.x < 0 || node.x > canvas.width) node.vx *= -1
        if (node.y < 0 || node.y > canvas.height) node.vy *= -1

        // Draw node
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2)
        ctx.fillStyle = node.color
        ctx.fill()
      })

      // Draw edges with fade-in animation
      edges.forEach((edge, index) => {
        if (frame > index * 5) {
          edge.opacity = Math.min(1, (frame - index * 5) / 30)
          const from = nodes[edge.from]
          const to = nodes[edge.to]

          ctx.beginPath()
          ctx.moveTo(from.x, from.y)
          ctx.lineTo(to.x, to.y)
          ctx.strokeStyle = `rgba(255, 255, 255, ${edge.opacity * 0.3})`
          ctx.lineWidth = 1
          ctx.stroke()
        }
      })

      frame++
      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [showGraph])

  if (!isVisible) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      >
        <motion.div
          initial={{ y: 50 }}
          animate={{ y: 0 }}
          className="bg-surface-1 border border-white/10 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="text-center mb-8">
            <motion.div
              initial={{ rotate: 0 }}
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="inline-flex items-center justify-center w-16 h-16 bg-brand-500/20 rounded-full mb-4"
            >
              <Database className="w-8 h-8 text-brand-500" />
            </motion.div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Transforming Your Data
            </h2>
            <p className="text-dark-muted">
              Converting Excel sheets into a powerful graph database
            </p>
          </div>

          {/* Progress Steps */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Import Progress</h3>
              <div className="space-y-3">
                {steps.map((step, index) => {
                  const isActive = index === currentStep
                  const isCompleted = index < currentStep
                  const Icon = step.icon

                  return (
                    <motion.div
                      key={step.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`flex items-center space-x-3 p-3 rounded-lg border transition-all duration-300 ${
                        isActive 
                          ? `${step.bgColor} ${step.borderColor} border-2` 
                          : isCompleted 
                            ? 'bg-green-500/10 border-green-500/20' 
                            : 'bg-surface-2 border-white/5'
                      }`}
                    >
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        isActive 
                          ? step.bgColor 
                          : isCompleted 
                            ? 'bg-green-500/20' 
                            : 'bg-surface-3'
                      }`}>
                        {isCompleted ? (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        ) : isActive ? (
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                          >
                            <Loader2 className="w-5 h-5 text-blue-500" />
                          </motion.div>
                        ) : (
                          <Icon className={`w-5 h-5 ${step.color}`} />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium ${
                          isActive ? 'text-white' : isCompleted ? 'text-green-400' : 'text-dark-muted'
                        }`}>
                          {step.title}
                        </p>
                        <p className="text-xs text-dark-muted">{step.description}</p>
                      </div>
                      {isActive && (
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${stepProgress}%` }}
                          className="h-1 bg-brand-500 rounded-full"
                          style={{ width: `${stepProgress}%` }}
                        />
                      )}
                    </motion.div>
                  )
                })}
              </div>
            </div>

            {/* Graph Visualization */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Graph Formation</h3>
              <div className="relative">
                {showGraph ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-surface-2 rounded-lg p-4 h-64 relative overflow-hidden"
                  >
                    <canvas
                      ref={canvasRef}
                      width={400}
                      height={240}
                      className="w-full h-full"
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <Network className="w-12 h-12 text-brand-500 mx-auto mb-2" />
                        <p className="text-sm text-dark-muted">Building connections...</p>
                      </div>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-surface-2 rounded-lg p-8 h-64 flex items-center justify-center"
                  >
                    <div className="text-center">
                      <FileSpreadsheet className="w-16 h-16 text-dark-muted mx-auto mb-4" />
                      <p className="text-dark-muted">Preparing to visualize graph...</p>
                    </div>
                  </motion.div>
                )}
              </div>

              {/* Live Stats */}
              {importStatus && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 grid grid-cols-2 gap-4"
                >
                  {importStatus.nodes_created && (
                    <div className="bg-surface-2 rounded-lg p-3 text-center">
                      <Package className="w-6 h-6 text-green-500 mx-auto mb-1" />
                      <p className="text-lg font-bold text-white">
                        {importStatus.nodes_created.products || 0}
                      </p>
                      <p className="text-xs text-dark-muted">Products</p>
                    </div>
                  )}
                  {importStatus.relationships_created && (
                    <div className="bg-surface-2 rounded-lg p-3 text-center">
                      <Network className="w-6 h-6 text-cyan-500 mx-auto mb-1" />
                      <p className="text-lg font-bold text-white">
                        {importStatus.relationships_created.total_relationships || 0}
                      </p>
                      <p className="text-xs text-dark-muted">Relationships</p>
                    </div>
                  )}
                </motion.div>
              )}
            </div>
          </div>

          {/* Educational Info */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="bg-surface-2 rounded-lg p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <Zap className="w-5 h-5 text-yellow-500 mr-2" />
              What's Happening?
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <FileSpreadsheet className="w-4 h-4 text-blue-500" />
                </div>
                <div>
                  <p className="font-medium text-white mb-1">Excel Analysis</p>
                  <p className="text-dark-muted">Intelligently detecting data structure and relationships</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <Database className="w-4 h-4 text-green-500" />
                </div>
                <div>
                  <p className="font-medium text-white mb-1">Graph Creation</p>
                  <p className="text-dark-muted">Converting tabular data into connected nodes and edges</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <Network className="w-4 h-4 text-purple-500" />
                </div>
                <div>
                  <p className="font-medium text-white mb-1">Relationship Building</p>
                  <p className="text-dark-muted">Creating meaningful connections between entities</p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Error Handling */}
          {importStatus?.error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mt-6 bg-red-500/10 border border-red-500/20 rounded-lg p-4"
            >
              <div className="flex items-center space-x-3">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <div>
                  <p className="font-medium text-red-400">Import Error</p>
                  <p className="text-sm text-red-300">{importStatus.error}</p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Success Message */}
          {importStatus?.completed && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 bg-green-500/10 border border-green-500/20 rounded-lg p-4"
            >
              <div className="flex items-center space-x-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <div>
                  <p className="font-medium text-green-400">Import Successful!</p>
                  <p className="text-sm text-green-300">
                    Your data has been successfully converted to a graph database and is ready for analysis.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default ImportVisualization
