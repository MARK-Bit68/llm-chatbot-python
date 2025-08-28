import { useState, useEffect, useCallback } from 'react'

export const useImportStatus = () => {
  const [importStatus, setImportStatus] = useState(null)
  const [isImporting, setIsImporting] = useState(false)
  const [error, setError] = useState(null)

  const startImport = useCallback(async (file) => {
    setIsImporting(true)
    setError(null)
    setImportStatus({
      analyzing: 0,
      format_detected: false,
      preparing: 0,
      creating_nodes: 0,
      building_relationships: 0,
      validating: 0,
      completed: false,
      error: null
    })

    try {
      // Create FormData for file upload
      const formData = new FormData()
      formData.append('file', file)

      // Start the upload
      const response = await fetch('/api/upload/excel', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()

      if (result.success) {
        // Simulate progress updates based on the actual import result
        const importStats = result.import_stats
        
        // Update status with real data
        setImportStatus(prev => ({
          ...prev,
          analyzing: 100,
          format_detected: true,
          preparing: 100,
          creating_nodes: 100,
          building_relationships: 100,
          validating: 100,
          completed: true,
          nodes_created: importStats.nodes_created,
          relationships_created: importStats.relationships_created,
          connectivity: importStats.connectivity,
          message: importStats.message
        }))
      } else {
        throw new Error(result.message || 'Import failed')
      }

    } catch (err) {
      setError(err.message)
      setImportStatus(prev => ({
        ...prev,
        error: err.message
      }))
    } finally {
      setIsImporting(false)
    }
  }, [])

  const resetImport = useCallback(() => {
    setImportStatus(null)
    setIsImporting(false)
    setError(null)
  }, [])

  return {
    importStatus,
    isImporting,
    error,
    startImport,
    resetImport
  }
}
