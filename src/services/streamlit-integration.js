import axios from 'axios'

// Configuration for Streamlit integration
const STREAMLIT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8501',
  timeout: 30000,
}

// Create axios instance for Streamlit API
const streamlitAPI = axios.create(STREAMLIT_CONFIG)

// Add request interceptor
streamlitAPI.interceptors.request.use((config) => {
  console.log(`🔗 API Request: ${config.method?.toUpperCase()} ${config.url}`)
  return config
})

// Add response interceptor
streamlitAPI.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('❌ API Error:', error.message)
    return Promise.reject(error)
  }
)

// Real Streamlit integration functions
export const sendMessageToStreamlit = async (message) => {
  try {
    // This would integrate with your actual Streamlit backend
    // For now, we'll simulate the API call structure
    const response = await streamlitAPI.post('/_stcore/stream', {
      type: 'chat_message',
      data: { message }
    })
    
    return response.data
  } catch (error) {
    console.error('Failed to send message to Streamlit:', error)
    throw error
  }
}

export const fetchStreamlitData = async (endpoint) => {
  try {
    const response = await streamlitAPI.get(endpoint)
    return response.data
  } catch (error) {
    console.error(`Failed to fetch data from ${endpoint}:`, error)
    throw error
  }
}

export const getStreamlitHealth = async () => {
  try {
    const response = await streamlitAPI.get('/_stcore/health')
    return response.status === 200
  } catch (error) {
    console.warn('Streamlit health check failed, using mock data')
    return false
  }
}

// Enhanced chat integration with your existing agent
export const chatWithAgent = async (message) => {
  try {
    // Check if Streamlit backend is available
    const isHealthy = await getStreamlitHealth()
    
    if (isHealthy) {
      // Use real Streamlit backend
      return await sendMessageToStreamlit(message)
    } else {
      // Fallback to mock responses (for development)
      console.warn('🔄 Using mock data - Streamlit backend not available')
      return getMockChatResponse(message)
    }
  } catch (error) {
    console.error('Chat request failed:', error)
    // Fallback to mock response
    return getMockChatResponse(message)
  }
}

// Mock response function (enhanced from existing api.js)
function getMockChatResponse(message) {
  const lowerMessage = message.toLowerCase()
  
  // Your existing mock response logic from api.js
  if (lowerMessage.includes('sku001')) {
    return `# 📊 Executive Summary: SKU001 Analysis

**Product**: Premium Beverage SKU001
**Category**: Beverages
**Country**: USA

## 💰 Financial Performance
- **Unit Price**: $12.50
- **Unit Cost**: $8.75
- **Gross Profit**: $3.75 per unit
- **Margin**: 30%

## 📦 Inventory Status
- **Current Stock**: 1,250 units
- **Lead Time**: 14 days
- **Reorder Point**: 300 units
- **Safety Stock**: 150 units

## 🎯 Strategic Insights
- Strong profit margin performer
- Consistent demand pattern
- Optimal inventory levels
- No immediate supply chain concerns

This SKU demonstrates excellent financial performance with healthy margins and stable inventory management.`
  }
  
  // Add other mock responses here...
  return `I understand you're asking about "${message}". 

🔗 **Connection Status**: Currently using mock data for development.

Once deployed to Railway with your Streamlit backend, this will connect to your real:
- Neo4j database with actual SKU data
- LangChain agents for intelligent responses  
- OpenAI integration for advanced analysis

**Available in production:**
- Real-time SKU information
- Live inventory data
- Actual supply chain metrics
- Your trained AI assistant responses`
}

export default streamlitAPI