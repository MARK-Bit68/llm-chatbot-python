import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, Database, Calendar, Hash, CheckCircle, AlertCircle, Info } from 'lucide-react';

const GraphMetadata = () => {
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMetadata();
  }, []);

  const fetchMetadata = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/graph/metadata');
      const data = await response.json();
      
      console.log('📋 Metadata API response:', data);
      
      if (data.success && data.has_data) {
        if (data.metadata) {
          setMetadata(data.metadata);
        } else {
          // Data exists but no metadata - show a message
          setMetadata(null);
          setError(null);
        }
      } else if (data.success && !data.has_data) {
        // No data found - this is normal for fresh installations
        setMetadata(null);
        setError(null);
      } else {
        setError('Failed to fetch metadata');
      }
    } catch (err) {
      console.error('❌ Metadata fetch error:', err);
      setError('Error fetching metadata');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6"
      >
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="text-gray-600 dark:text-gray-400">Loading graph metadata...</span>
        </div>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6"
      >
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <span className="text-red-800 dark:text-red-200">{error}</span>
        </div>
      </motion.div>
    );
  }

  if (!metadata) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6"
      >
        <div className="flex items-center space-x-2">
          <Info className="h-5 w-5 text-blue-600" />
          <span className="text-blue-800 dark:text-blue-200">
            Graph data is available but import metadata was not preserved. The data was successfully imported and is ready for use.
          </span>
        </div>
      </motion.div>
    );
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getConnectivityColor = (percentage) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6 border border-gray-200 dark:border-gray-700"
      data-testid="graph-metadata"
    >
      <div className="flex items-center space-x-2 mb-4">
        <Database className="h-6 w-6 text-blue-600" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Graph Data Source
        </h2>
        {metadata.import_success && (
          <CheckCircle className="h-5 w-5 text-green-600" />
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* File Information */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center space-x-2">
            <FileText className="h-5 w-5 text-gray-600" />
            <span>Source File</span>
          </h3>
          
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Filename</label>
              <p className="text-sm text-gray-900 dark:text-white font-mono bg-gray-50 dark:bg-gray-700 px-2 py-1 rounded">
                {metadata.filename}
              </p>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400">File Size</label>
              <p className="text-sm text-gray-900 dark:text-white">
                {formatFileSize(metadata.file_size_bytes)}
              </p>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400">File Hash</label>
              <p className="text-sm text-gray-900 dark:text-white font-mono bg-gray-50 dark:bg-gray-700 px-2 py-1 rounded text-xs">
                {metadata.file_hash}
              </p>
            </div>
          </div>
        </div>

        {/* Import Information */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-gray-600" />
            <span>Import Details</span>
          </h3>
          
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Import Date</label>
              <p className="text-sm text-gray-900 dark:text-white">
                {formatDate(metadata.import_timestamp)}
              </p>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Format Detected</label>
              <p className="text-sm text-gray-900 dark:text-white capitalize">
                {metadata.format_detected.replace('_', ' ')}
              </p>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Sheets Processed</label>
              <p className="text-sm text-gray-900 dark:text-white">
                {metadata.total_sheets} sheet{metadata.total_sheets !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Graph Statistics */}
      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Graph Statistics
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {metadata.products_created || 0}
            </div>
            <div className="text-sm text-blue-600">Products</div>
          </div>
          
          <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {metadata.total_relationships || 0}
            </div>
            <div className="text-sm text-green-600">Relationships</div>
          </div>
          
          <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {metadata.categories_created || 0}
            </div>
            <div className="text-sm text-purple-600">Categories</div>
          </div>
          
          <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {metadata.countries_created || 0}
            </div>
            <div className="text-sm text-orange-600">Countries</div>
          </div>
        </div>
        
        {/* Additional node types for Enhanced format */}
        {(metadata.customers_created > 0 || metadata.orders_created > 0 || metadata.campaigns_created > 0 || metadata.regions_created > 0) && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            {metadata.customers_created > 0 && (
              <div className="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-lg">
                <div className="text-2xl font-bold text-indigo-600">
                  {metadata.customers_created}
                </div>
                <div className="text-sm text-indigo-600">Customers</div>
              </div>
            )}
            
            {metadata.orders_created > 0 && (
              <div className="bg-pink-50 dark:bg-pink-900/20 p-4 rounded-lg">
                <div className="text-2xl font-bold text-pink-600">
                  {metadata.orders_created}
                </div>
                <div className="text-sm text-pink-600">Orders</div>
              </div>
            )}
            
            {metadata.campaigns_created > 0 && (
              <div className="bg-teal-50 dark:bg-teal-900/20 p-4 rounded-lg">
                <div className="text-2xl font-bold text-teal-600">
                  {metadata.campaigns_created}
                </div>
                <div className="text-sm text-teal-600">Campaigns</div>
              </div>
            )}
            
            {metadata.regions_created > 0 && (
              <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg">
                <div className="text-2xl font-bold text-amber-600">
                  {metadata.regions_created}
                </div>
                <div className="text-sm text-amber-600">Regions</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Connectivity Status */}
      {metadata.connectivity && (
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Connectivity Status
            </h3>
            <div className={`text-lg font-semibold ${getConnectivityColor(metadata.connectivity.connectivity_percentage)}`}>
              {metadata.connectivity.connectivity_percentage.toFixed(1)}% Connected
            </div>
          </div>
          
          <div className="mt-2 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                metadata.connectivity.connectivity_percentage >= 80
                  ? 'bg-green-600'
                  : metadata.connectivity.connectivity_percentage >= 50
                  ? 'bg-yellow-600'
                  : 'bg-red-600'
              }`}
              style={{ width: `${Math.min(metadata.connectivity.connectivity_percentage, 100)}%` }}
            ></div>
          </div>
          
          <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            {metadata.connectivity.connected_nodes} of {metadata.connectivity.total_nodes} nodes are connected
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default GraphMetadata;
