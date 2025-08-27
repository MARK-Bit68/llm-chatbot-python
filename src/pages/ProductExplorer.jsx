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
  DollarSign,
  Factory,
  Warehouse
} from 'lucide-react'
import { fetchProducts } from '../services/advanced-api'

const ProductCard = ({ product }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    whileHover={{ y: -2 }}
    className="card cursor-pointer group"
  >
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="text-lg font-semibold text-white group-hover:text-brand-500 transition-colors">
          {product.code}
        </h3>
        <p className="text-dark-muted text-sm">{product.group} - {product.subgroup}</p>
      </div>
      <button className="p-2 hover:bg-surface-2 rounded-lg transition-colors opacity-0 group-hover:opacity-100">
        <Eye className="w-4 h-4" />
      </button>
    </div>

    <div className="grid grid-cols-2 gap-4 mb-4">
      <div>
        <p className="text-xs text-dark-muted mb-1">Group</p>
        <p className="text-sm font-medium text-white">{product.group}</p>
      </div>
      <div>
        <p className="text-xs text-dark-muted mb-1">SubGroup</p>
        <p className="text-sm font-medium text-white">{product.subgroup}</p>
      </div>
    </div>

    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm text-dark-muted">Plants</span>
        <span className="text-sm font-medium text-white">{product.plants?.length || 0}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-dark-muted">Storage Locations</span>
        <span className="text-sm font-medium text-white">{product.storage_locations?.length || 0}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-dark-muted">Time Series</span>
        <span className="text-sm font-medium text-white">{product.time_series?.length || 0}</span>
      </div>

      <div className="mt-4 pt-4 border-t border-white border-opacity-10">
        <div className="flex items-center justify-between">
          <span className="text-sm text-dark-muted">Data Availability</span>
          <div className={`w-3 h-3 rounded-full ${
            (product.time_series?.length || 0) > 0 ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
        </div>
      </div>
    </div>
  </motion.div>
)

const ProductExplorer = () => {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [group, setGroup] = useState('')
  const [viewMode, setViewMode] = useState('grid') // 'grid' or 'table'

  const { data: productData, isLoading } = useQuery(
    ['products', page, search, group],
    () => fetchProducts({ page, search, group }),
    {
      keepPreviousData: true,
      refetchInterval: 30000 // Refresh every 30 seconds
    }
  )

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-6"
      >
        <div>
          <h1 className="text-3xl font-bold text-white">Product Explorer</h1>
          <p className="text-dark-muted mt-1">
            Browse and analyze SupplyGraph products
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button className="btn-secondary">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card mb-6"
      >
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-80">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-muted" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search products..."
                className="input-field pl-10"
              />
            </div>
          </div>
          
          <div className="min-w-48">
            <select
              value={group}
              onChange={(e) => setGroup(e.target.value)}
              className="input-field"
            >
              <option value="">All Groups</option>
              <option value="S">Group S</option>
              <option value="P">Group P</option>
              <option value="A">Group A</option>
              <option value="M">Group M</option>
              <option value="E">Group E</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'grid' 
                  ? 'bg-brand-500 text-white' 
                  : 'bg-surface-2 text-dark-muted hover:text-white'
              }`}
            >
              <Package className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'table' 
                  ? 'bg-brand-500 text-white' 
                  : 'bg-surface-2 text-dark-muted hover:text-white'
              }`}
            >
              <Filter className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Stats Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6"
      >
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Total Products</p>
              <p className="text-2xl font-bold text-white">{productData?.total || "Loading..."}</p>
            </div>
            <div className="p-3 bg-brand-500/20 rounded-lg">
              <Package className="w-6 h-6 text-brand-500" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Groups</p>
              <p className="text-2xl font-bold text-white">Loading...</p>
            </div>
            <div className="p-3 bg-blue-500/20 rounded-lg">
              <TrendingUp className="w-6 h-6 text-blue-500" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Plants</p>
              <p className="text-2xl font-bold text-white">Loading...</p>
            </div>
            <div className="p-3 bg-green-500/20 rounded-lg">
              <Factory className="w-6 h-6 text-green-500" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Storage Locations</p>
              <p className="text-2xl font-bold text-white">Loading...</p>
            </div>
            <div className="p-3 bg-purple-500/20 rounded-lg">
              <Warehouse className="w-6 h-6 text-purple-500" />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Product Grid/Table */}
      <div className="flex-1">
        {isLoading ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-500 mx-auto mb-4"></div>
              <p className="text-dark-muted">Loading products...</p>
            </div>
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            {viewMode === 'grid' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {productData?.products?.map((product) => (
                  <ProductCard key={product.code} product={product} />
                ))}
              </div>
            ) : (
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b border-white border-opacity-10">
                      <tr>
                        <th className="text-left py-3 px-4 text-dark-muted font-medium">Product Code</th>
                        <th className="text-left py-3 px-4 text-dark-muted font-medium">Group</th>
                        <th className="text-left py-3 px-4 text-dark-muted font-medium">SubGroup</th>
                        <th className="text-left py-3 px-4 text-dark-muted font-medium">Plants</th>
                        <th className="text-left py-3 px-4 text-dark-muted font-medium">Storage</th>
                        <th className="text-left py-3 px-4 text-dark-muted font-medium">Time Series</th>
                        <th className="text-left py-3 px-4 text-dark-muted font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {productData?.products?.map((product) => (
                        <tr key={product.code} className="border-b border-white border-opacity-10 hover:bg-surface-2 transition-colors">
                          <td className="py-3 px-4 text-white font-medium">{product.code}</td>
                          <td className="py-3 px-4 text-dark-text">{product.group}</td>
                          <td className="py-3 px-4 text-dark-text">{product.subgroup}</td>
                          <td className="py-3 px-4 text-white">{product.plants?.length || 0}</td>
                          <td className="py-3 px-4 text-white">{product.storage_locations?.length || 0}</td>
                          <td className="py-3 px-4">
                            <div className="flex items-center space-x-2">
                              <span className="text-white">{product.time_series?.length || 0}</span>
                              <div className={`w-2 h-2 rounded-full ${
                                (product.time_series?.length || 0) > 0 ? 'bg-green-500' : 'bg-red-500'
                              }`}></div>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              (product.time_series?.length || 0) > 0
                                ? 'bg-green-500/20 text-green-500'
                                : 'bg-red-500/20 text-red-500'
                            }`}>
                              {(product.time_series?.length || 0) > 0 ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Pagination */}
      {productData?.totalPages > 1 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-center space-x-2 mt-6"
        >
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          
          <div className="flex items-center space-x-2">
            {[...Array(Math.min(5, productData.totalPages))].map((_, i) => {
              const pageNumber = i + 1
              return (
                <button
                  key={pageNumber}
                  onClick={() => setPage(pageNumber)}
                  className={`px-3 py-2 rounded-lg transition-colors ${
                    page === pageNumber
                      ? 'bg-brand-500 text-white'
                      : 'bg-surface-2 text-dark-text hover:bg-surface-3'
                  }`}
                >
                  {pageNumber}
                </button>
              )
            })}
          </div>
          
          <button
            onClick={() => setPage(Math.min(productData.totalPages, page + 1))}
            disabled={page === productData.totalPages}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </motion.div>
      )}
    </div>
  )
}

export default ProductExplorer