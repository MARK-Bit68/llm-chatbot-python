import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from 'react-query'
import { 
  Calendar, 
  Download, 
  Filter,
  TrendingUp,
  BarChart3,
  PieChart as PieChartIcon,
  Activity
} from 'lucide-react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts'
import { fetchAnalytics } from '../services/api'

const Analytics = () => {
  const [timeRange, setTimeRange] = useState('30d')
  const [selectedMetrics, setSelectedMetrics] = useState(['revenue', 'profit', 'efficiency'])

  const { data: analyticsData, isLoading } = useQuery(
    ['analytics', timeRange, selectedMetrics],
    () => fetchAnalytics({ timeRange, metrics: selectedMetrics }),
    {
      refetchInterval: 60000, // Refresh every minute
    }
  )

  const revenueData = [
    { month: 'Jan', revenue: 450000, profit: 135000, units: 12500 },
    { month: 'Feb', revenue: 520000, profit: 156000, units: 14300 },
    { month: 'Mar', revenue: 480000, profit: 144000, units: 13200 },
    { month: 'Apr', revenue: 610000, profit: 183000, units: 16800 },
    { month: 'May', revenue: 550000, profit: 165000, units: 15200 },
    { month: 'Jun', revenue: 670000, profit: 201000, units: 18500 },
  ]

  const categoryPerformance = [
    { category: 'Beverages', revenue: 420000, growth: 12.5, skus: 87 },
    { category: 'Snacks', revenue: 310000, growth: 8.3, skus: 62 },
    { category: 'Dairy', revenue: 280000, growth: 15.7, skus: 49 },
    { category: 'Packaged Foods', revenue: 190000, growth: 6.2, skus: 49 },
  ]

  const efficiencyMetrics = [
    { metric: 'Inventory Turnover', value: 8.5, target: 8.0, status: 'good' },
    { metric: 'Fill Rate', value: 94.2, target: 95.0, status: 'warning' },
    { metric: 'Cost Efficiency', value: 87.3, target: 85.0, status: 'good' },
    { metric: 'Lead Time Performance', value: 91.8, target: 90.0, status: 'good' },
  ]

  const regionData = [
    { name: 'North America', value: 42, color: '#7C4DFF' },
    { name: 'Europe', value: 35, color: '#00BCD4' },
    { name: 'Asia-Pacific', value: 23, color: '#4CAF50' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics Dashboard</h1>
          <p className="text-dark-muted mt-1">Advanced insights and performance metrics</p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="input-field"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <button className="btn-secondary">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </button>
          <button className="btn-primary">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </motion.div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { title: 'Total Revenue', value: '$1.2M', change: '+9.1%', icon: TrendingUp },
          { title: 'Gross Profit', value: '$360K', change: '+12.3%', icon: BarChart3 },
          { title: 'Active SKUs', value: '247', change: '+5.1%', icon: PieChartIcon },
          { title: 'Efficiency Score', value: '94.2%', change: '+2.6%', icon: Activity },
        ].map((metric, index) => {
          const Icon = metric.icon
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="card"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-dark-muted text-sm font-medium">{metric.title}</p>
                  <p className="text-2xl font-bold text-white mt-1">{metric.value}</p>
                  <p className="text-green-500 text-sm mt-1">{metric.change} vs last period</p>
                </div>
                <div className="p-3 bg-brand-500/20 rounded-lg">
                  <Icon className="w-6 h-6 text-brand-500" />
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trend */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-white mb-6">Revenue & Profit Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="month" stroke="#9AA4B2" />
              <YAxis stroke="#9AA4B2" />
              <Area
                type="monotone"
                dataKey="revenue"
                stackId="1"
                stroke="#7C4DFF"
                fill="#7C4DFF"
                fillOpacity={0.3}
              />
              <Area
                type="monotone"
                dataKey="profit"
                stackId="1"
                stroke="#00BCD4"
                fill="#00BCD4"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Regional Distribution */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-white mb-6">Regional Revenue Distribution</h3>
          <div className="flex items-center justify-center">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={regionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {regionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2 mt-4">
            {regionData.map((item, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div className="flex items-center">
                  <div 
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: item.color }}
                  ></div>
                  <span className="text-dark-muted">{item.name}</span>
                </div>
                <span className="text-white font-medium">{item.value}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Performance */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card lg:col-span-2"
        >
          <h3 className="text-lg font-semibold text-white mb-6">Category Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categoryPerformance}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="category" stroke="#9AA4B2" />
              <YAxis stroke="#9AA4B2" />
              <Bar dataKey="revenue" fill="#7C4DFF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Efficiency Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-white mb-6">Efficiency Metrics</h3>
          <div className="space-y-4">
            {efficiencyMetrics.map((metric, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-dark-muted">{metric.metric}</span>
                  <span className="text-white font-medium">{metric.value}%</span>
                </div>
                <div className="w-full bg-surface-2 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      metric.status === 'good' ? 'bg-green-500' : 
                      metric.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(metric.value, 100)}%` }}
                  />
                </div>
                <div className="text-xs text-dark-muted">
                  Target: {metric.target}%
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Insights */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="card"
      >
        <h3 className="text-lg font-semibold text-white mb-6">Key Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {analyticsData?.insights?.map((insight, index) => (
            <div key={index} className="p-4 bg-surface-2 rounded-lg">
              <p className="text-sm text-dark-text">{insight}</p>
            </div>
          )) || [
            'Revenue increased 12% compared to last month',
            'Beverages category showing strong performance',
            'Supply chain efficiency improved by 8%',
            'Inventory turnover rate optimized'
          ].map((insight, index) => (
            <div key={index} className="p-4 bg-surface-2 rounded-lg">
              <p className="text-sm text-dark-text">{insight}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}

export default Analytics