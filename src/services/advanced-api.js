// Advanced API Service for Enhanced Graph Analytics
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance with enhanced configuration
const advancedAPI = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // Extended timeout for complex analytics
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor
advancedAPI.interceptors.request.use((config) => {
  console.log(`🔗 Advanced API Request: ${config.method?.toUpperCase()} ${config.url}`)
  return config
})

// Add response interceptor with enhanced error handling
advancedAPI.interceptors.response.use(
  (response) => {
    console.log(`✅ Advanced API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('❌ Advanced API Error:', error.message)
    
    // Enhanced error context
    if (error.response) {
      console.error('Error Response:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config?.url
      })
    }
    
    return Promise.reject(error)
  }
)

// Health Check
export const checkAPIHealth = async () => {
  try {
    const response = await advancedAPI.get('/health')
    return response.data
  } catch (error) {
    console.error('Health check failed:', error)
    return {
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString()
    }
  }
}

// Chat API with Advanced Features
export const sendAdvancedChatMessage = async ({ message, sessionId = 'default' }) => {
  try {
    const response = await advancedAPI.post('/api/chat', {
      message,
      session_id: sessionId
    })
    
    return {
      ...response.data,
      source: 'advanced_ai'
    }
  } catch (error) {
    console.error('Advanced chat failed:', error)
    throw new Error('Failed to send message to advanced AI agent')
  }
}

// Streaming Chat (for real-time responses)
export const createChatStream = (message, sessionId = 'default') => {
  return fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId
    })
  })
}

// Reset Chat Session
export const resetChatSession = async (sessionId) => {
  try {
    const response = await advancedAPI.delete(`/api/chat/session/${sessionId}`)
    return response.data
  } catch (error) {
    console.error('Session reset failed:', error)
    throw new Error('Failed to reset chat session')
  }
}

// Advanced Analytics APIs
export const getGraphOverview = async () => {
  try {
    const response = await advancedAPI.get('/api/analytics/overview')
    return response.data
  } catch (error) {
    console.error('Graph overview failed:', error)
    throw new Error('Failed to fetch graph overview')
  }
}

export const getSupplyChainInsights = async () => {
  try {
    const response = await advancedAPI.post('/api/analytics/insights')
    return response.data
  } catch (error) {
    console.error('Supply chain insights failed:', error)
    throw new Error('Failed to fetch supply chain insights')
  }
}

export const getCustomAnalytics = async (analysisType, parameters = {}) => {
  try {
    const response = await advancedAPI.post('/api/analytics/custom', {
      analysis_type: analysisType,
      parameters
    })
    return response.data
  } catch (error) {
    console.error('Custom analytics failed:', error)
    throw new Error(`Failed to fetch ${analysisType} analytics`)
  }
}

// Dashboard API with Real Data
export const getAdvancedDashboardData = async () => {
  try {
    const response = await advancedAPI.get('/api/dashboard')
    return response.data
  } catch (error) {
    console.error('Advanced dashboard failed:', error)
    throw new Error('Failed to fetch advanced dashboard data')
  }
}

// Analytics Types
export const ANALYTICS_TYPES = {
  OVERVIEW: 'overview',
  PATTERNS: 'patterns', 
  CLUSTERS: 'clusters',
  RISKS: 'risks',
  PROFITABILITY: 'profitability',
  REGIONAL: 'regional'
}

// Insight Types for Processing
export const INSIGHT_TYPES = {
  CLUSTERING: 'clustering',
  INVENTORY_RISK: 'inventory_risk',
  PROFITABILITY: 'profitability',
  REGIONAL_PERFORMANCE: 'regional_performance'
}

// Utility function to check if advanced API is available
export const isAdvancedAPIAvailable = async () => {
  try {
    const health = await checkAPIHealth()
    return health.status === 'healthy'
  } catch (error) {
    return false
  }
}

// Enhanced error handling with user-friendly messages
export const getErrorMessage = (error) => {
  if (error.response?.status === 404) {
    return 'The requested data could not be found'
  } else if (error.response?.status === 500) {
    return 'Server error occurred. Please try again later'
  } else if (error.response?.status === 403) {
    return 'Access denied. Please check your permissions'
  } else if (error.code === 'NETWORK_ERROR') {
    return 'Network connection error. Please check your internet connection'
  } else {
    return error.message || 'An unexpected error occurred'
  }
}

// Batch analytics request for multiple analysis types
export const getBatchAnalytics = async (analysisTypes) => {
  try {
    const promises = analysisTypes.map(type => 
      getCustomAnalytics(type).catch(error => ({
        type,
        error: error.message
      }))
    )
    
    const results = await Promise.all(promises)
    
    return {
      results,
      timestamp: new Date().toISOString(),
      success_count: results.filter(r => !r.error).length,
      error_count: results.filter(r => r.error).length
    }
  } catch (error) {
    console.error('Batch analytics failed:', error)
    throw new Error('Failed to fetch batch analytics')
  }
}

export default advancedAPI