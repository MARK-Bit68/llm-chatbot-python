import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth or other headers
api.interceptors.request.use((config) => {
  // Add any auth tokens or other headers here
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// Chat API - Integrates with FastAPI backend
export const sendChatMessage = async ({ message, session_id = 'default' }) => {
  try {
    const response = await api.post('/chat', { 
      message, 
      session_id 
    })
    
    return {
      response: response.data.response,
      timestamp: response.data.timestamp,
      session_id: response.data.session_id,
      status: response.data.status,
      source: 'fastapi'
    }
  } catch (error) {
    console.error('Chat API Error:', error)
    throw new Error('Failed to send chat message to backend')
  }
}

// Dashboard API
export const fetchDashboardData = async () => {
  try {
    // Try FastAPI backend first
    const response = await api.get('/dashboard')
    
    // Transform FastAPI response to dashboard format
    const dashboard = response.data
    console.log('Dashboard API response:', dashboard) // Debug log
    
    return {
      totalSKUs: dashboard.totalProducts,
      totalRevenue: dashboard.totalRevenue,
      supplyIssues: dashboard.supplyIssues || 0,
      performanceScore: dashboard.performanceScore,
      recentActivity: dashboard.recentActivity || []
    }
  } catch (error) {
    console.error('Dashboard API unavailable:', error)
    throw new Error('Failed to fetch dashboard data from backend')
  }
}

// SKU API
export const fetchSKUs = async ({ page = 1, limit = 20, search = '', category = '' } = {}) => {
  try {
    const response = await new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: {
            skus: generateMockSKUs(page, limit, search, category),
            total: 247,
            page,
            totalPages: Math.ceil(247 / limit)
          }
        })
      }, 800)
    })
    
    return response.data
  } catch (error) {
    throw new Error('Failed to fetch SKUs')
  }
}

// Analytics API
export const fetchAnalytics = async ({ timeRange = '30d', metrics = [] } = {}) => {
  try {
    // Try to fetch from real backend first
    const response = await api.get('/analytics/dashboard')
    
    const data = response.data
    
    // Transform backend data to match frontend expectations
    return {
      metrics: {
        total_revenue: data.metrics.total_revenue,
        total_profit: data.metrics.total_profit,
        active_skus: data.metrics.active_skus,
        efficiency_score: data.metrics.efficiency_score
      },
      time_series: data.time_series,
      categories: data.categories,
      regions: data.regions,
      efficiency: data.efficiency,
      insights: data.insights
    }
  } catch (error) {
    console.error('Error fetching analytics from backend:', error)
    throw new Error('Failed to fetch analytics data from backend')
  }
}




export default api