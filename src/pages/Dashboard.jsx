import React from 'react'
import { motion } from 'framer-motion'
import { useQuery } from 'react-query'
import { 
  TrendingUp, 
  TrendingDown, 
  Package, 
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { fetchDashboardData } from '../services/api'
import GraphMetadata from '../components/GraphMetadata'

const StatCard = ({ title, value, change, changeType, icon: Icon, loading }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="card"
  >
    <div className="flex items-center justify-between">
      <div>
        <p className="text-dark-muted text-sm font-medium">{title}</p>
        <p className="text-2xl font-bold text-white mt-1">
          {loading ? (
            <div className="w-16 h-8 bg-surface-2 animate-pulse rounded"></div>
          ) : (
            value
          )}
        </p>
        {change && (
          <div className={`flex items-center mt-2 text-sm ${
            changeType === 'positive' ? 'text-green-500' : 'text-red-500'
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
      <div className="p-3 bg-brand-500/20 rounded-lg">
        <Icon className="w-6 h-6 text-brand-500" />
      </div>
    </div>
  </motion.div>
)

const Dashboard = () => {
  const { data: dashboardData, isLoading } = useQuery(
    'dashboardData',
    fetchDashboardData,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  )

  const mockChartData = [
    { month: 'Jan', revenue: 45000, profit: 12000 },
    { month: 'Feb', revenue: 52000, profit: 15600 },
    { month: 'Mar', revenue: 48000, profit: 14400 },
    { month: 'Apr', revenue: 61000, profit: 18300 },
    { month: 'May', revenue: 55000, profit: 16500 },
    { month: 'Jun', revenue: 67000, profit: 20100 },
  ]

  const mockPieData = [
    { name: 'Beverages', value: 35, color: '#7C4DFF' },
    { name: 'Snacks', value: 25, color: '#00BCD4' },
    { name: 'Dairy', value: 20, color: '#4CAF50' },
    { name: 'Packaged Foods', value: 20, color: '#FF9800' },
  ]

  return (
    <div className="space-y-6">
      {/* Graph Metadata - Prominently displayed */}
      <GraphMetadata />
      
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-white">Supply Chain Dashboard</h1>
          <p className="text-dark-muted mt-1">Real-time insights into your FMCG operations</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="btn-secondary">
            <Clock className="w-4 h-4 mr-2" />
            Last updated: {new Date().toLocaleTimeString()}
          </button>
          <button className="btn-primary">
            Generate Report
          </button>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total SKUs"
          value={dashboardData?.totalSKUs || "247"}
          change="+12 this month"
          changeType="positive"
          icon={Package}
          loading={isLoading}
        />
        <StatCard
          title="Total Revenue"
          value={dashboardData?.totalRevenue || "$1.2M"}
          change="+8.2% vs last month"
          changeType="positive"
          icon={DollarSign}
          loading={isLoading}
        />
        <StatCard
          title="Supply Issues"
          value={dashboardData?.supplyIssues || "23"}
          change="-5 from last week"
          changeType="positive"
          icon={AlertTriangle}
          loading={isLoading}
        />
        <StatCard
          title="Performance Score"
          value={dashboardData?.performanceScore || "94%"}
          change="+2.1% improvement"
          changeType="positive"
          icon={CheckCircle}
          loading={isLoading}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Trend */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card lg:col-span-2"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white">Revenue & Profit Trends</h3>
            <BarChart3 className="w-5 h-5 text-brand-500" />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={mockChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="month" stroke="#9AA4B2" />
              <YAxis stroke="#9AA4B2" />
              <Line 
                type="monotone" 
                dataKey="revenue" 
                stroke="#7C4DFF" 
                strokeWidth={3}
                dot={{ fill: '#7C4DFF', strokeWidth: 2, r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="profit" 
                stroke="#00BCD4" 
                strokeWidth={3}
                dot={{ fill: '#00BCD4', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Category Distribution */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-white mb-6">Category Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={mockPieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {mockPieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-2 mt-4">
            {mockPieData.map((item, index) => (
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

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card"
      >
        <h3 className="text-lg font-semibold text-white mb-6">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            'Inventory Analysis',
            'Demand Forecast',
            'Supply Planning',
            'Cost Analysis',
            'Performance Review',
            'Risk Assessment'
          ].map((action, index) => (
            <button
              key={index}
              className="btn-secondary text-center p-4 h-auto"
            >
              {action}
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  )
}

export default Dashboard