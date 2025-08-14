import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from 'react-query'
import { 
  Search, 
  Filter, 
  Download, 
  Eye,
  TrendingUp,
  TrendingDown,
  Package,
  DollarSign
} from 'lucide-react'
import { fetchSKUs } from '../services/api'

const SKUCard = ({ sku }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    whileHover={{ y: -2 }}
    className="card cursor-pointer group"
  >
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="text-lg font-semibold text-white group-hover:text-brand-500 transition-colors">
          {sku.id}
        </h3>
        <p className="text-dark-muted text-sm">{sku.name}</p>
      </div>
      <button className="p-2 hover:bg-surface-2 rounded-lg transition-colors opacity-0 group-hover:opacity-100">
        <Eye className="w-4 h-4" />
      </button>
    </div>

    <div className="grid grid-cols-2 gap-4 mb-4">
      <div>
        <p className="text-xs text-dark-muted mb-1">Category</p>
        <p className="text-sm font-medium text-white">{sku.category}</p>
      </div>
      <div>
        <p className="text-xs text-dark-muted mb-1">Country</p>
        <p className="text-sm font-medium text-white">{sku.country}</p>
      </div>
    </div>

    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm text-dark-muted">Unit Price</span>
        <span className="text-sm font-medium text-white">${sku.unitPrice}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-dark-muted">Gross Profit</span>
        <span className="text-sm font-medium text-green-500">${sku.grossProfit}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-dark-muted">Margin</span>
        <span className="text-sm font-medium text-white">{sku.margin}%</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-dark-muted">Lead Time</span>
        <span className="text-sm font-medium text-white">{sku.leadTime} days</span>
      </div>
    </div>

    <div className="mt-4 pt-4 border-t border-white border-opacity-10">
      <div className="flex items-center justify-between">
        <span className="text-sm text-dark-muted">Inventory</span>
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-white">{sku.inventory} units</span>
          <div className={`w-2 h-2 rounded-full ${
            sku.inventory > 500 ? 'bg-green-500' : 
            sku.inventory > 200 ? 'bg-yellow-500' : 'bg-red-500'
          }`}></div>
        </div>
      </div>
    </div>
  </motion.div>
)

const SKUExplorer = () => {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [page, setPage] = useState(1)
  const [view, setView] = useState('grid') // 'grid' or 'table'

  const { data: skuData, isLoading } = useQuery(
    ['skus', page, search, category],
    () => fetchSKUs({ page, search, category }),
    {
      keepPreviousData: true,
    }
  )

  const categories = ['All Categories', 'Beverages', 'Snacks', 'Dairy', 'Packaged Foods']

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-white">SKU Explorer</h1>
          <p className="text-dark-muted mt-1">Browse and analyze your product portfolio</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="btn-secondary">
            <Filter className="w-4 h-4 mr-2" />
            Advanced Filters
          </button>
          <button className="btn-primary">
            <Download className="w-4 h-4 mr-2" />
            Export Data
          </button>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card"
      >
        <div className="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-muted" />
            <input
              type="text"
              placeholder="Search SKUs..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-10 w-full"
            />
          </div>
          
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="input-field w-48"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat === 'All Categories' ? '' : cat}>
                {cat}
              </option>
            ))}
          </select>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setView('grid')}
              className={`p-2 rounded-lg transition-colors ${
                view === 'grid' ? 'bg-brand-500 text-white' : 'bg-surface-2 text-dark-muted'
              }`}
            >
              <Package className="w-4 h-4" />
            </button>
            <button
              onClick={() => setView('table')}
              className={`p-2 rounded-lg transition-colors ${
                view === 'table' ? 'bg-brand-500 text-white' : 'bg-surface-2 text-dark-muted'
              }`}
            >
              <DollarSign className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Total SKUs</p>
              <p className="text-2xl font-bold text-white">{skuData?.total || 247}</p>
            </div>
            <Package className="w-8 h-8 text-brand-500" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Avg Margin</p>
              <p className="text-2xl font-bold text-white">24.3%</p>
              <div className="flex items-center text-green-500 text-sm mt-1">
                <TrendingUp className="w-3 h-3 mr-1" />
                +2.1%
              </div>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Total Value</p>
              <p className="text-2xl font-bold text-white">$4.2M</p>
              <div className="flex items-center text-green-500 text-sm mt-1">
                <TrendingUp className="w-3 h-3 mr-1" />
                +5.8%
              </div>
            </div>
            <DollarSign className="w-8 h-8 text-brand-500" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Low Stock</p>
              <p className="text-2xl font-bold text-white">23</p>
              <div className="flex items-center text-red-500 text-sm mt-1">
                <TrendingDown className="w-3 h-3 mr-1" />
                Attention needed
              </div>
            </div>
            <TrendingDown className="w-8 h-8 text-red-500" />
          </div>
        </motion.div>
      </div>

      {/* SKU Grid/Table */}
      {view === 'grid' ? (
        <div>
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {[...Array(12)].map((_, i) => (
                <div key={i} className="card animate-pulse">
                  <div className="h-4 bg-surface-2 rounded mb-4"></div>
                  <div className="h-3 bg-surface-2 rounded mb-2"></div>
                  <div className="h-3 bg-surface-2 rounded mb-4"></div>
                  <div className="space-y-2">
                    <div className="h-2 bg-surface-2 rounded"></div>
                    <div className="h-2 bg-surface-2 rounded"></div>
                    <div className="h-2 bg-surface-2 rounded"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {skuData?.skus?.map((sku) => (
                <SKUCard key={sku.id} sku={sku} />
              ))}
            </div>
          )}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card"
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white border-opacity-10">
                  <th className="text-left py-3 px-4 text-dark-muted font-medium">SKU ID</th>
                  <th className="text-left py-3 px-4 text-dark-muted font-medium">Name</th>
                  <th className="text-left py-3 px-4 text-dark-muted font-medium">Category</th>
                  <th className="text-left py-3 px-4 text-dark-muted font-medium">Price</th>
                  <th className="text-left py-3 px-4 text-dark-muted font-medium">Margin</th>
                  <th className="text-left py-3 px-4 text-dark-muted font-medium">Inventory</th>
                  <th className="text-left py-3 px-4 text-dark-muted font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {skuData?.skus?.map((sku) => (
                  <tr key={sku.id} className="border-b border-white border-opacity-10 hover:bg-surface-2 transition-colors">
                    <td className="py-3 px-4 text-white font-medium">{sku.id}</td>
                    <td className="py-3 px-4 text-dark-text">{sku.name}</td>
                    <td className="py-3 px-4 text-dark-text">{sku.category}</td>
                    <td className="py-3 px-4 text-white">${sku.unitPrice}</td>
                    <td className="py-3 px-4 text-white">{sku.margin}%</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        <span className="text-white">{sku.inventory}</span>
                        <div className={`w-2 h-2 rounded-full ${
                          sku.inventory > 500 ? 'bg-green-500' : 
                          sku.inventory > 200 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}></div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <button className="text-brand-500 hover:text-brand-400 transition-colors">
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Pagination */}
      {skuData?.totalPages > 1 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-center space-x-2"
        >
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          
          <div className="flex items-center space-x-1">
            {[...Array(Math.min(5, skuData.totalPages))].map((_, i) => {
              const pageNum = i + 1
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`px-3 py-2 rounded-lg transition-colors ${
                    page === pageNum
                      ? 'bg-brand-500 text-white'
                      : 'bg-surface-2 text-dark-text hover:bg-surface-3'
                  }`}
                >
                  {pageNum}
                </button>
              )
            })}
          </div>
          
          <button
            onClick={() => setPage(Math.min(skuData.totalPages, page + 1))}
            disabled={page === skuData.totalPages}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </motion.div>
      )}
    </div>
  )
}

export default SKUExplorer