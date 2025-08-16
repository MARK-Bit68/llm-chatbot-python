import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';

const ExcelUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      // Validate file type
      if (!selectedFile.name.endsWith('.xlsx') && !selectedFile.name.endsWith('.xls')) {
        toast.error('Please select an Excel file (.xlsx or .xls)');
        return;
      }
      setFile(selectedFile);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select a file first');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload/excel', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setUploadResult(result);
        toast.success('Excel file uploaded and processed successfully!');
        
        // Refresh the page after a short delay to show updated graph
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        toast.error(result.detail || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (!droppedFile.name.endsWith('.xlsx') && !droppedFile.name.endsWith('.xls')) {
        toast.error('Please select an Excel file (.xlsx or .xls)');
        return;
      }
      setFile(droppedFile);
      setUploadResult(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6"
      >
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            📊 Upload Excel File
          </h2>
          <p className="text-gray-600 dark:text-gray-300">
            Upload an Excel file to regenerate the graph database with enhanced connectivity
          </p>
        </div>

        {/* File Upload Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            file
              ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-blue-500 dark:hover:border-blue-400'
          }`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <div className="space-y-4">
            <div className="text-4xl">📁</div>
            <div>
              <p className="text-lg font-medium text-gray-900 dark:text-white">
                {file ? file.name : 'Drop your Excel file here'}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                or click to browse
              </p>
            </div>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg cursor-pointer transition-colors"
            >
              Choose File
            </label>
          </div>
        </div>

        {/* Upload Button */}
        {file && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 text-center"
          >
            <button
              onClick={handleUpload}
              disabled={uploading}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {uploading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Processing...</span>
                </div>
              ) : (
                'Upload and Process Excel File'
              )}
            </button>
          </motion.div>
        )}

        {/* Upload Result */}
        {uploadResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4"
          >
            <h3 className="text-lg font-semibold text-green-800 dark:text-green-200 mb-3">
              ✅ Upload Successful!
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300">File:</p>
                <p className="text-gray-600 dark:text-gray-400">{uploadResult.filename}</p>
              </div>
              
              {uploadResult.import_stats && (
                <>
                  <div>
                    <p className="font-medium text-gray-700 dark:text-gray-300">Nodes Created:</p>
                    <div className="text-gray-600 dark:text-gray-400">
                      {Object.entries(uploadResult.import_stats.nodes_created || {}).map(([type, count]) => (
                        <div key={type} className="flex justify-between">
                          <span className="capitalize">{type}:</span>
                          <span>{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <p className="font-medium text-gray-700 dark:text-gray-300">Relationships Created:</p>
                    <div className="text-gray-600 dark:text-gray-400">
                      {Object.entries(uploadResult.import_stats.relationships_created || {}).map(([type, count]) => (
                        <div key={type} className="flex justify-between">
                          <span className="capitalize">{type.replace('_', ' ')}:</span>
                          <span>{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {uploadResult.import_stats.connectivity && (
                    <div className="md:col-span-2">
                      <p className="font-medium text-gray-700 dark:text-gray-300">Connectivity:</p>
                      <div className="text-gray-600 dark:text-gray-400">
                        <div className="flex justify-between">
                          <span>Total Nodes:</span>
                          <span>{uploadResult.import_stats.connectivity.total_nodes}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Connected Nodes:</span>
                          <span>{uploadResult.import_stats.connectivity.connected_nodes}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Isolated Nodes:</span>
                          <span>{uploadResult.import_stats.connectivity.isolated_nodes}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Connectivity:</span>
                          <span>{uploadResult.import_stats.connectivity.connectivity_percentage.toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
            
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                🔄 The page will refresh automatically to show the updated graph visualization.
              </p>
            </div>
          </motion.div>
        )}

        {/* Instructions */}
        <div className="mt-8 bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            📋 Instructions
          </h3>
          <div className="text-sm text-gray-600 dark:text-gray-300 space-y-2">
            <p>• Upload an Excel file with FMCG supply chain data</p>
            <p>• The file should contain sheets with "Raw - Nodes", "Raw - Node Types", "Raw - Edges Group", etc.</p>
            <p>• The system will create a fully connected graph with no isolated nodes</p>
            <p>• All existing graph data will be replaced with the new data</p>
            <p>• The graph visualization will be updated automatically</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ExcelUpload;
