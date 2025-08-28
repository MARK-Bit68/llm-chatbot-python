import React, { useState } from 'react'
import { motion } from 'framer-motion'
import ImportVisualization from './ImportVisualization'

const ImportVisualizationDemo = () => {
  const [showDemo, setShowDemo] = useState(false)
  const [demoStatus, setDemoStatus] = useState(null)

  const startDemo = () => {
    setShowDemo(true)
    setDemoStatus({
      analyzing: 0,
      format_detected: false,
      preparing: 0,
      creating_nodes: 0,
      building_relationships: 0,
      validating: 0,
      completed: false
    })

    // Simulate progress
    const simulateProgress = () => {
      let step = 0
      const interval = setInterval(() => {
        switch (step) {
          case 0:
            setDemoStatus(prev => ({ ...prev, analyzing: 100, format_detected: true }))
            break
          case 1:
            setDemoStatus(prev => ({ ...prev, preparing: 100 }))
            break
          case 2:
            setDemoStatus(prev => ({ ...prev, creating_nodes: 100 }))
            break
          case 3:
            setDemoStatus(prev => ({ 
              ...prev, 
              building_relationships: 100,
              nodes_created: { products: 1999, categories: 10, countries: 25, plants: 10 },
              relationships_created: { total_relationships: 5997 }
            }))
            break
          case 4:
            setDemoStatus(prev => ({ 
              ...prev, 
              validating: 100,
              connectivity: {
                total_nodes: 2058,
                connected_nodes: 2044,
                isolated_nodes: 14,
                total_relationships: 5997,
                connectivity_percentage: 99.3
              }
            }))
            break
          case 5:
            setDemoStatus(prev => ({ ...prev, completed: true }))
            clearInterval(interval)
            break
        }
        step++
      }, 1000)
    }

    simulateProgress()
  }

  return (
    <div className="p-8">
      <div className="max-w-md mx-auto text-center">
        <h2 className="text-2xl font-bold text-white mb-4">
          Import Visualization Demo
        </h2>
        <p className="text-dark-muted mb-6">
          Click the button below to see the animated import process
        </p>
        <button
          onClick={startDemo}
          className="px-6 py-3 bg-brand-500 hover:bg-brand-600 text-white rounded-lg font-medium transition-colors"
        >
          Start Demo
        </button>
      </div>

      <ImportVisualization
        isVisible={showDemo}
        importStatus={demoStatus}
        onComplete={() => {
          setShowDemo(false)
          setDemoStatus(null)
        }}
      />
    </div>
  )
}

export default ImportVisualizationDemo
