import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';

const ExcelUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [uploadProgress, setUploadProgress] = useState('');

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
    setUploadProgress('📤 Uploading file...');
    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploadProgress('🔍 Analyzing Excel structure...');
      const response = await fetch('/api/upload/excel', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setUploadProgress('✅ Processing complete!');
        setUploadResult(result);
        
        // Show analysis results if available
        if (result.excel_analysis) {
          setAnalysisResult(result.excel_analysis);
        }
        
        toast.success('Excel file uploaded and processed successfully!');
        
        // Refresh the page after a short delay to show updated graph
        setTimeout(() => {
          setUploadProgress('🔄 Refreshing application...');
          window.location.reload();
        }, 3000);
      } else {
        toast.error(result.detail || 'Upload failed');
        setUploadProgress('');
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Upload failed. Please try again.');
      setUploadProgress('');
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
            
            {/* Progress Indicator */}
            {uploadProgress && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-4 text-sm text-blue-600 dark:text-blue-400"
              >
                {uploadProgress}
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Excel Analysis Result */}
        {analysisResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4"
          >
            <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200 mb-3">
              🔍 Excel Analysis Results
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300">Sheets Found:</p>
                <p className="text-gray-600 dark:text-gray-400">{analysisResult.total_sheets}</p>
              </div>
              
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300">Sheet Names:</p>
                <div className="text-gray-600 dark:text-gray-400 max-h-20 overflow-y-auto">
                  {analysisResult.sheet_names?.map((name, idx) => (
                    <div key={idx} className="text-xs">{name}</div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="mt-3">
              <p className="font-medium text-gray-700 dark:text-gray-300 mb-2">Suggested Mapping:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                {Object.entries(analysisResult.suggested_mapping || {}).map(([sheet, type]) => (
                  <div key={sheet} className="flex justify-between bg-white dark:bg-gray-800 p-2 rounded">
                    <span className="truncate mr-2">{sheet}</span>
                    <span className="text-blue-600 dark:text-blue-400 font-medium capitalize">{type.replace('_', ' ')}</span>
                  </div>
                ))}
              </div>
            </div>
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
              
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300">Sheets Processed:</p>
                <p className="text-gray-600 dark:text-gray-400">{uploadResult.sheets_processed || 0}</p>
              </div>
              
              {uploadResult.nodes_created && (
                <div>
                  <p className="font-medium text-gray-700 dark:text-gray-300">Nodes Created:</p>
                  <div className="text-gray-600 dark:text-gray-400">
                    {Object.entries(uploadResult.nodes_created).map(([type, count]) => (
                      <div key={type} className="flex justify-between">
                        <span className="capitalize">{type}:</span>
                        <span>{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {uploadResult.relationships_created && (
                <div>
                  <p className="font-medium text-gray-700 dark:text-gray-300">Relationships Created:</p>
                  <div className="text-gray-600 dark:text-gray-400">
                    {Object.entries(uploadResult.relationships_created).map(([type, count]) => (
                      <div key={type} className="flex justify-between">
                        <span className="capitalize">{type.replace('_', ' ')}:</span>
                        <span>{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {uploadResult.connectivity && (
                <div className="md:col-span-2">
                  <p className="font-medium text-gray-700 dark:text-gray-300">Graph Connectivity:</p>
                  <div className="text-gray-600 dark:text-gray-400">
                    <div className="flex justify-between">
                      <span>Total Nodes:</span>
                      <span>{uploadResult.connectivity.total_nodes}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Connected Nodes:</span>
                      <span>{uploadResult.connectivity.connected_nodes}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Isolated Nodes:</span>
                      <span>{uploadResult.connectivity.isolated_nodes}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Connectivity:</span>
                      <span>{uploadResult.connectivity.connectivity_percentage?.toFixed(1) || 0}%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {uploadResult.errors && uploadResult.errors.length > 0 && (
              <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                <p className="text-sm text-orange-800 dark:text-orange-200 font-medium mb-1">⚠️ Processing Warnings:</p>
                <div className="text-xs text-orange-700 dark:text-orange-300 max-h-20 overflow-y-auto">
                  {uploadResult.errors.map((error, idx) => (
                    <div key={idx}>{error}</div>
                  ))}
                </div>
              </div>
            )}
            
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
            <p>• Upload any Excel file with your data - the system will intelligently analyze it</p>
            <p>• Supports any sheet structure - nodes, relationships, categories, and temporal data</p>
            <p>• The system automatically detects data types and creates optimal graph structures</p>
            <p>• All existing graph data will be replaced with the new data</p>
            <p>• Real-time analysis shows how your data will be mapped to the graph</p>
            <p>• The graph visualization will be updated automatically</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ExcelUpload;
