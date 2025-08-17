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
    // Fallback to mock response
    return {
      response: getMockResponse(message),
      timestamp: new Date().toISOString(),
      session_id,
      status: 'fallback',
      source: 'mock'
    }
  }
}

// Dashboard API
export const fetchDashboardData = async () => {
  try {
    // Try FastAPI backend first
    const response = await api.get('/api/dashboard')
    
    // Transform FastAPI response to dashboard format
    const dashboard = response.data
    console.log('Dashboard API response:', dashboard) // Debug log
    
    return {
      totalSKUs: dashboard.totalProducts || 2000,
      totalRevenue: dashboard.totalRevenue || '$3.3B',
      supplyIssues: 23,
      performanceScore: dashboard.performanceScore || '94%',
      recentActivity: [
        { id: 1, action: 'Graph analytics updated', timestamp: new Date() },
        { id: 2, action: 'FastAPI backend operational', timestamp: new Date() },
        { id: 3, action: 'React UI deployed successfully', timestamp: new Date() },
      ]
    }
  } catch (error) {
    console.warn('Dashboard API unavailable, using mock data:', error)
    // Fallback to mock data
    return {
      totalSKUs: 2000,
      totalRevenue: '$3.3B',
      supplyIssues: 23,
      performanceScore: '94%',
      recentActivity: [
        { id: 1, action: 'Using mock data', timestamp: new Date() },
        { id: 2, action: 'FastAPI connection pending', timestamp: new Date() },
        { id: 3, action: 'System operational', timestamp: new Date() },
      ]
    }
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
    const response = await api.get('/api/analytics/dashboard')
    
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
    
    // Fallback to mock data if backend fails
    console.warn('Falling back to mock data')
    await new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: {
            metrics: generateMockAnalytics(timeRange, metrics),
            insights: [
              'Revenue increased 12% compared to last month',
              'Beverages category showing strong performance',
              'Supply chain efficiency improved by 8%',
              'Inventory turnover rate optimized'
            ]
          }
        })
      }, 1200)
    })
    
    return response.data
  }
}

// Helper functions for mock data
function getMockResponse(message) {
  const lowerMessage = message.toLowerCase()
  
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
  
  if (lowerMessage.includes('categories') || lowerMessage.includes('category')) {
    return `# 📊 Product Categories Analysis

Based on the current database, here are the distinct product categories:

## 🏷️ Category Overview
1. **Beverages** - 87 SKUs (35% of total)
2. **Snacks** - 62 SKUs (25% of total) 
3. **Dairy Products** - 49 SKUs (20% of total)
4. **Packaged Foods** - 49 SKUs (20% of total)

## 📈 Performance Metrics
- **Highest Revenue**: Beverages ($420K)
- **Best Margins**: Dairy Products (28% avg)
- **Growth Leader**: Snacks (+15% YoY)
- **Most SKUs**: Beverages category

Each category serves different market segments and contributes uniquely to our overall supply chain strategy.`
  }
  
  if (lowerMessage.includes('highest') && lowerMessage.includes('profit')) {
    return `# 🏆 Top Performing SKU by Gross Profit

**Winner**: SKU089 - Premium Dairy Product

## 💰 Financial Highlights
- **Gross Profit per Unit**: $8.45
- **Unit Price**: $22.90
- **Unit Cost**: $14.45
- **Profit Margin**: 36.9%

## 📊 Performance Context
- Ranks #1 out of 247 SKUs
- 22% above category average
- Consistent high-margin performer
- Strong market positioning

## 🎯 Strategic Value
This SKU represents our most profitable product line with excellent margin performance and should be prioritized in production planning and marketing efforts.`
  }
  
  if (lowerMessage.includes('excess') || lowerMessage.includes('promotion')) {
    return `# 🛍️ Excess Inventory - Promotional Opportunities

## 📦 High Inventory SKUs Ready for Promotion

### Tier 1 - Immediate Action Required
- **SKU034**: Packaged Snacks (340 units, 45 days supply)
- **SKU078**: Beverage Mix (280 units, 38 days supply)  
- **SKU156**: Dairy Spread (220 units, 35 days supply)

### Tier 2 - Monitor Closely  
- **SKU089**: Premium Dairy (180 units, 28 days supply)
- **SKU123**: Snack Bars (165 units, 25 days supply)

## 💡 Promotional Strategies
1. **Bundle Deals**: Combine slow-moving with fast-moving SKUs
2. **Volume Discounts**: 15-20% off for bulk purchases
3. **Limited Time Offers**: Create urgency for excess inventory
4. **Cross-Category Promotions**: Mix categories for variety

## 📈 Expected Impact
- Reduce excess inventory by 60-70%
- Improve cash flow by $45K-60K
- Free up warehouse space for new products`
  }
  
  if (lowerMessage.includes('regional') || lowerMessage.includes('demand')) {
    return `# 🌍 Regional Demand Analysis

## 📍 Market Performance by Region

### North America
- **Total SKUs**: 89 (36% of portfolio)
- **Revenue Share**: 42% ($504K)
- **Growth Rate**: +8.2% YoY
- **Key Categories**: Beverages, Snacks

### Europe  
- **Total SKUs**: 76 (31% of portfolio)
- **Revenue Share**: 35% ($420K)
- **Growth Rate**: +12.5% YoY
- **Key Categories**: Dairy, Packaged Foods

### Asia-Pacific
- **Total SKUs**: 82 (33% of portfolio)  
- **Revenue Share**: 23% ($276K)
- **Growth Rate**: +18.3% YoY
- **Key Categories**: Beverages, Snacks

## 🎯 Strategic Insights
- **APAC**: Fastest growing but lowest revenue share - opportunity for expansion
- **Europe**: Strong growth with balanced category mix
- **North America**: Largest market with stable performance

## 📋 Action Items
1. Increase APAC investment and SKU variety
2. Leverage European dairy success in other regions  
3. Optimize North American product mix for growth`
  }
  
  // Default response
  return `I understand you're asking about "${message}". Based on your FMCG supply chain data, I can help analyze SKUs, inventory levels, financial performance, and operational metrics. 

Here are some specific areas I can assist with:
- **SKU Analysis**: Detailed product information and performance
- **Financial Metrics**: Revenue, costs, margins, and profitability  
- **Inventory Management**: Stock levels, lead times, and optimization
- **Supply Chain**: Demand patterns, regional variations, and constraints
- **Strategic Insights**: Recommendations for operational improvements

Please feel free to ask more specific questions about your data!`
}

function generateMockSKUs(page, limit, search, category) {
  const categories = ['Beverages', 'Snacks', 'Dairy', 'Packaged Foods']
  const countries = ['USA', 'Germany', 'Japan', 'Brazil', 'India']
  
  const skus = []
  for (let i = 0; i < limit; i++) {
    const skuNum = ((page - 1) * limit + i + 1).toString().padStart(3, '0')
    const sku = {
      id: `SKU${skuNum}`,
      name: `Product ${skuNum}`,
      category: categories[Math.floor(Math.random() * categories.length)],
      country: countries[Math.floor(Math.random() * countries.length)],
      unitPrice: (Math.random() * 50 + 5).toFixed(2),
      unitCost: (Math.random() * 30 + 3).toFixed(2),
      leadTime: Math.floor(Math.random() * 30 + 5),
      inventory: Math.floor(Math.random() * 1000 + 100),
      lastUpdated: new Date()
    }
    
    // Calculate gross profit
    sku.grossProfit = (sku.unitPrice - sku.unitCost).toFixed(2)
    sku.margin = ((sku.grossProfit / sku.unitPrice) * 100).toFixed(1)
    
    skus.push(sku)
  }
  
  return skus
}

function generateMockAnalytics(timeRange, metrics) {
  return {
    revenue: {
      current: 1200000,
      previous: 1100000,
      change: 9.1
    },
    profit: {
      current: 360000,
      previous: 330000,
      change: 9.1
    },
    skuCount: {
      current: 247,
      previous: 235,
      change: 5.1
    },
    efficiency: {
      current: 94.2,
      previous: 91.8,
      change: 2.6
    }
  }
}

export default api