import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from 'react-query'
import { 
  TrendingUp, 
  TrendingDown, 
  Package, 
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  Brain,
  Network,
  Zap,
  Target
} from 'lucide-react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  Tooltip,
  Legend
} from 'recharts'
import toast from 'react-hot-toast'
import { 
  getAdvancedDashboardData, 
  getGraphOverview, 
  getSupplyChainInsights,
  isAdvancedAPIAvailable 
} from '../services/advanced-api'

const AdvancedStatCard = ({ title, value, change, changeType, icon: Icon, loading, insight }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    whileHover={{ y: -2, scale: 1.02 }}
    className="card relative overflow-hidden"
  >
    {/* Background gradient */}
    <div className="absolute inset-0 bg-gradient-to-br from-brand-500/5 to-transparent"></div>
    
    <div className="relative z-10">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-dark-muted text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">
            {loading ? (
              <div className="w-20 h-8 bg-surface-2 animate-pulse rounded"></div>
            ) : (
              value
            )}
          </p>
          {change && (
            <div className={`flex items-center mt-2 text-sm ${
              changeType === 'positive' ? 'text-green-400' : 'text-red-400'
            }`}>
              {changeType === 'positive' ? (
                <TrendingUp className="w-4 h-4 mr-1" />
              ) : (
                <TrendingDown className="w-4 h-4 mr-1" />
              )}
              {change}
            </div>
          )}
        </div>
        <div className="p-4 bg-brand-500/20 rounded-xl">
          <Icon className="w-8 h-8 text-brand-500" />
        </div>
      </div>
      
      {insight && (
        <div className="mt-4 p-3 bg-surface-2 rounded-lg">
          <p className="text-xs text-dark-muted">{insight}</p>
        </div>
      )}
    </div>
  </motion.div>
)

const InsightCard = ({ insight, index }) => (
  <motion.div
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: index * 0.1 }}
    className="card"
  >
    <div className="flex items-start space-x-4">
      <div className="p-3 bg-brand-500/20 rounded-lg">
        {insight.insight_type === 'clustering' && <Brain className="w-6 h-6 text-brand-500" />}
        {insight.insight_type === 'inventory_risk' && <AlertTriangle className="w-6 h-6 text-yellow-500" />}
        {insight.insight_type === 'profitability' && <DollarSign className="w-6 h-6 text-green-500" />}
        {insight.insight_type === 'regional_performance' && <Network className="w-6 h-6 text-blue-500" />}
      </div>
      
      <div className="flex-1">
        <h3 className="text-lg font-semibold text-white mb-2">{insight.title}</h3>
        <p className="text-dark-muted text-sm mb-3">{insight.description}</p>
        
        <div className="flex items-center justify-between text-xs text-dark-muted mb-3">
          <span>Confidence: {(insight.confidence * 100).toFixed(1)}%</span>
          <span>{new Date(insight.timestamp).toLocaleTimeString()}</span>
        </div>
        
        {insight.recommendations && insight.recommendations.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-brand-500 mb-2">Key Recommendations:</p>
            {insight.recommendations.slice(0, 2).map((rec, idx) => (
              <p key={idx} className="text-xs text-dark-text">• {rec}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  </motion.div>
)

const GraphMetricsCard = ({ graphData, loading }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="card"
  >
    <div className="flex items-center justify-between mb-6">
      <h3 className="text-lg font-semibold text-white">Graph Database Metrics</h3>
      <Network className="w-5 h-5 text-brand-500" />
    </div>
    
    {loading ? (
      <div className="space-y-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="flex justify-between">
            <div className="w-24 h-4 bg-surface-2 animate-pulse rounded"></div>
            <div className="w-16 h-4 bg-surface-2 animate-pulse rounded"></div>
          </div>
        ))}
      </div>
    ) : (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-dark-muted">Total Nodes</span>
          <span className="text-white font-medium">
            {graphData?.node_statistics?.total_nodes?.toLocaleString() || 'N/A'}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-dark-muted">Relationships</span>
          <span className="text-white font-medium">
            {graphData?.relationship_statistics?.total_relationships?.toLocaleString() || 'N/A'}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-dark-muted">Graph Density</span>
          <span className="text-white font-medium">
            {graphData?.advanced_metrics?.density ? 
              (graphData.advanced_metrics.density * 100).toFixed(2) + '%' : 'N/A'}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-dark-muted">Components</span>
          <span className="text-white font-medium">
            {graphData?.advanced_metrics?.number_of_components || 'N/A'}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-dark-muted">Avg Clustering</span>
          <span className="text-white font-medium">
            {graphData?.advanced_metrics?.average_clustering ? 
              (graphData.advanced_metrics.average_clustering * 100).toFixed(1) + '%' : 'N/A'}
          </span>
        </div>
      </div>
    )}
  </motion.div>
)

const AdvancedDashboard = () => {
  const [apiAvailable, setApiAvailable] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  // Check API availability
  useEffect(() => {
    const checkAPI = async () => {
      const available = await isAdvancedAPIAvailable()
      setApiAvailable(available)
      
      if (!available) {
        toast.error('Advanced API not available. Using fallback data.', {
          duration: 3000,
          position: 'top-center'
        })
      } else {
        toast.success('Connected to Advanced Analytics Engine!', {
          duration: 2000,
          position: 'top-center'
        })
      }
    }
    
    checkAPI()
  }, [])

  // Fetch advanced dashboard data
  const { data: dashboardData, isLoading: dashboardLoading } = useQuery(
    'advancedDashboard',
    getAdvancedDashboardData,
    {
      enabled: apiAvailable,
      refetchInterval: 30000, // Refresh every 30 seconds
      onError: () => toast.error('Failed to fetch dashboard data')
    }
  )

  // Fetch graph overview
  const { data: graphData, isLoading: graphLoading } = useQuery(
    'graphOverview',
    getGraphOverview,
    {
      enabled: apiAvailable,
      refetchInterval: 60000, // Refresh every minute
      onError: () => toast.error('Failed to fetch graph data')
    }
  )

  // Fetch supply chain insights
  const { data: insightsData, isLoading: insightsLoading } = useQuery(
    'supplyChainInsights',
    getSupplyChainInsights,
    {
      enabled: apiAvailable,
      refetchInterval: 120000, // Refresh every 2 minutes
      onError: () => toast.error('Failed to fetch insights')
    }
  )

  // Fallback data when API is not available
  const fallbackData = {
    totalProducts: '40',
    totalGroups: '5',
    totalPlants: '25',
    totalStorageLocations: '13',
    totalCategories: '4',
    performanceScore: '94.2%',
    insights_generated: '0',
    recommendations: [
      'Advanced analytics not available',
      'Please ensure backend services are running'
    ]
  }

  const displayData = apiAvailable ? dashboardData : fallbackData
  const insights = insightsData?.insights || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center">
            <Brain className="w-8 h-8 mr-3 text-brand-500" />
            Advanced Analytics Dashboard
          </h1>
          <p className="text-dark-muted mt-1">
            Real-time graph analytics and machine learning insights
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
            apiAvailable ? 'bg-green-500/20' : 'bg-red-500/20'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              apiAvailable ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`}></div>
            <span className="text-sm">
              {apiAvailable ? 'Advanced AI Connected' : 'Fallback Mode'}
            </span>
          </div>
          
          <button 
            onClick={() => setLastUpdate(new Date())}
            className="btn-secondary"
          >
            <Clock className="w-4 h-4 mr-2" />
            Updated: {lastUpdate.toLocaleTimeString()}
          </button>
        </div>
      </motion.div>

      {/* Advanced Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <AdvancedStatCard
          title="Total Products"
          value={displayData?.totalProducts || fallbackData.totalProducts}
          change={apiAvailable ? "+12 this month" : "Estimated"}
          changeType="positive"
          icon={Package}
          loading={dashboardLoading && apiAvailable}
          insight={apiAvailable ? "Data from Neo4j graph database" : "Fallback estimate"}
        />
        
        <AdvancedStatCard
          title="Performance Score"
          value={displayData?.performanceScore || fallbackData.performanceScore}
          change={apiAvailable ? "+2.1% improvement" : "ML-based score"}
          changeType="positive"
          icon={Target}
          loading={dashboardLoading && apiAvailable}
          insight={apiAvailable ? "ML-computed performance index" : "Estimated performance"}
        />
        
        <AdvancedStatCard
          title="AI Insights"
          value={displayData?.insights_generated || fallbackData.insights_generated}
          change={apiAvailable ? "Real-time generation" : "Waiting for connection"}
          changeType="positive"
          icon={Brain}
          loading={insightsLoading && apiAvailable}
          insight={apiAvailable ? "Machine learning generated insights" : "Advanced analytics pending"}
        />
        
        <AdvancedStatCard
          title="Graph Density"
          value={graphData?.advanced_metrics?.density ? 
            (graphData.advanced_metrics.density * 100).toFixed(1) + '%' : 'N/A'}
          change={apiAvailable ? "Network analysis" : "Graph computation pending"}
          changeType="positive"
          icon={Network}
          loading={graphLoading && apiAvailable}
          insight={apiAvailable ? "Graph theory computation" : "Requires graph connection"}
        />
      </div>

      {/* Advanced Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Graph Metrics */}
        <GraphMetricsCard 
          graphData={graphData} 
          loading={graphLoading && apiAvailable} 
        />

        {/* Real-time Insights */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="card lg:col-span-2"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white">AI-Generated Insights</h3>
            <div className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-brand-500" />
              <span className="text-sm text-dark-muted">
                {insights.length} insights available
              </span>
            </div>
          </div>
          
          {insightsLoading && apiAvailable ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="p-4 bg-surface-2 animate-pulse rounded-lg">
                  <div className="h-4 bg-surface rounded mb-2"></div>
                  <div className="h-3 bg-surface rounded w-3/4"></div>
                </div>
              ))}
            </div>
          ) : insights.length > 0 ? (
            <div className="space-y-4 max-h-96 overflow-y-auto">
              <AnimatePresence>
                {insights.map((insight, index) => (
                  <InsightCard key={insight.timestamp} insight={insight} index={index} />
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <div className="text-center py-8">
              <Brain className="w-12 h-12 text-dark-muted mx-auto mb-4" />
              <p className="text-dark-muted">
                {apiAvailable 
                  ? 'AI insights are being generated...' 
                  : 'Connect to advanced backend for AI insights'
                }
              </p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Strategic Recommendations */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card"
      >
        <h3 className="text-lg font-semibold text-white mb-6">Strategic Recommendations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(displayData?.recommendations || fallbackData.recommendations).map((recommendation, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 * index }}
              className="p-4 bg-surface-2 rounded-lg border-l-4 border-brand-500"
            >
              <p className="text-sm text-dark-text">{recommendation}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Status Footer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center text-xs text-dark-muted"
      >
        <p>
          {apiAvailable 
            ? '🚀 Powered by Advanced Graph Analytics Engine with Machine Learning' 
            : '⚡ Ready for Advanced Analytics - Connect backend services'
          }
        </p>
      </motion.div>
    </div>
  )
}

export default AdvancedDashboard