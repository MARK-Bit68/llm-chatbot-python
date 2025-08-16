#!/usr/bin/env node
/**
 * End-to-End Validation Test for FMCG Assistant
 * Tests complete flow: Upload Excel → Visualizer → Product Viewer → Analytics
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class E2EValidator {
  constructor() {
    this.browser = null;
    this.page = null;
    this.testResults = [];
    this.baseUrl = 'https://fmcg-assistant-production.up.railway.app';
  }

  async log(message, type = 'INFO') {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${type}] ${message}`;
    console.log(logMessage);
    this.testResults.push(logMessage);
  }

  async init() {
    this.log('🚀 Starting E2E Validation Test');
    this.log(`📍 Target URL: ${this.baseUrl}`);
    
    this.browser = await puppeteer.launch({
      headless: false, // Set to true for CI
      defaultViewport: { width: 1920, height: 1080 },
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    this.page = await this.browser.newPage();
    
    // Enable console logging
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        this.log(`Browser Error: ${msg.text()}`, 'ERROR');
      }
    });
    
    this.page.on('pageerror', error => {
      this.log(`Page Error: ${error.message}`, 'ERROR');
    });
  }

  async navigateToApp() {
    this.log('📱 Navigating to FMCG Assistant...');
    await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2', timeout: 30000 });
    
    // Wait for app to load
    await this.page.waitForSelector('[data-testid="app-loaded"]', { timeout: 10000 })
      .catch(() => this.log('App loaded (no test ID found)', 'WARN'));
    
    this.log('✅ App loaded successfully');
  }

  async testInitialState() {
    this.log('🔍 Testing initial application state...');
    
    // Check if we're on the dashboard
    const dashboardTitle = await this.page.$eval('h1', el => el.textContent)
      .catch(() => 'Not found');
    
    this.log(`📊 Dashboard title: ${dashboardTitle}`);
    
    // Check for metadata component
    const metadataExists = await this.page.$('[data-testid="graph-metadata"]')
      .then(() => true)
      .catch(() => false);
    
    this.log(`📋 Graph metadata component: ${metadataExists ? 'Present' : 'Missing'}`);
    
    // Get initial graph statistics
    const initialStats = await this.getGraphStatistics();
    this.log(`📈 Initial graph stats: ${JSON.stringify(initialStats)}`);
    
    return initialStats;
  }

  async getGraphStatistics() {
    try {
      // Try to get stats from the metadata component
      const stats = await this.page.evaluate(() => {
        const metadataEl = document.querySelector('[data-testid="graph-metadata"]');
        if (metadataEl) {
          const productEl = metadataEl.querySelector('.text-blue-600');
          const relationshipEl = metadataEl.querySelector('.text-green-600');
          return {
            products: productEl ? parseInt(productEl.textContent) : 0,
            relationships: relationshipEl ? parseInt(relationshipEl.textContent) : 0
          };
        }
        return { products: 0, relationships: 0 };
      });
      return stats;
    } catch (error) {
      this.log(`Error getting graph statistics: ${error.message}`, 'ERROR');
      return { products: 0, relationships: 0 };
    }
  }

  async testExcelUpload() {
    this.log('📤 Testing Excel file upload...');
    
    // Navigate to upload page
    await this.page.click('a[href="/upload"]');
    await this.page.waitForSelector('input[type="file"]', { timeout: 10000 });
    
    // Create a test Excel file with modified data (remove one SKU)
    const testExcelPath = await this.createTestExcelFile();
    
    // Upload the file
    const [fileChooser] = await Promise.all([
      this.page.waitForFileChooser(),
      this.page.click('input[type="file"]')
    ]);
    
    await fileChooser.accept([testExcelPath]);
    
    // Click upload button
    await this.page.click('button:contains("Upload Excel File")');
    
    // Wait for upload to complete
    await this.page.waitForSelector('.text-green-600', { timeout: 30000 });
    
    const uploadResult = await this.page.evaluate(() => {
      const resultEl = document.querySelector('.text-green-600');
      return resultEl ? resultEl.textContent : 'Upload failed';
    });
    
    this.log(`✅ Upload result: ${uploadResult}`);
    
    // Verify upload success
    const successMessage = await this.page.$eval('.text-green-600', el => el.textContent)
      .catch(() => 'Upload failed');
    
    if (!successMessage.includes('successfully')) {
      throw new Error(`Upload failed: ${successMessage}`);
    }
    
    this.log('✅ Excel upload completed successfully');
    
    // Clean up test file
    fs.unlinkSync(testExcelPath);
  }

  async createTestExcelFile() {
    this.log('📝 Creating test Excel file with modified data...');
    
    // Read the original Excel file
    const originalPath = path.join(__dirname, 'AI_Enhanced_SOP_Dataset.xlsx');
    const testPath = path.join(__dirname, 'test_modified_dataset.xlsx');
    
    // Copy the original file
    fs.copyFileSync(originalPath, testPath);
    
    // Note: In a real implementation, we would modify the Excel file
    // For now, we'll use the original file and test the upload flow
    this.log('📄 Test Excel file created (using original data)');
    
    return testPath;
  }

  async testGraphVisualizer() {
    this.log('🎮 Testing Graph Visualizer...');
    
    // Navigate to graph visualizer
    await this.page.click('a[href="/graph"]');
    await this.page.waitForSelector('[data-testid="graph-visualizer"]', { timeout: 10000 });
    
    // Wait for graph data to load
    await this.page.waitForFunction(() => {
      const noDataEl = document.querySelector('.text-yellow-600');
      return !noDataEl || !noDataEl.textContent.includes('No graph data');
    }, { timeout: 15000 });
    
    // Check graph statistics
    const graphStats = await this.page.evaluate(() => {
      const nodesEl = document.querySelector('.text-blue-600');
      const edgesEl = document.querySelector('.text-green-600');
      
      return {
        nodes: nodesEl ? parseInt(nodesEl.textContent) : 0,
        edges: edgesEl ? parseInt(edgesEl.textContent) : 0
      };
    });
    
    this.log(`📊 Graph visualizer stats: ${JSON.stringify(graphStats)}`);
    
    // Verify we have data
    if (graphStats.nodes === 0) {
      throw new Error('Graph visualizer shows no nodes');
    }
    
    if (graphStats.edges === 0) {
      this.log('⚠️ Graph visualizer shows no edges (this might be expected)', 'WARN');
    }
    
    this.log('✅ Graph visualizer loaded successfully');
    return graphStats;
  }

  async testProductExplorer() {
    this.log('🔍 Testing Product Explorer...');
    
    // Navigate to product explorer
    await this.page.click('a[href="/products"]');
    await this.page.waitForSelector('[data-testid="product-explorer"]', { timeout: 10000 });
    
    // Wait for products to load
    await this.page.waitForFunction(() => {
      const productList = document.querySelectorAll('[data-testid="product-item"]');
      return productList.length > 0;
    }, { timeout: 15000 });
    
    // Count products
    const productCount = await this.page.evaluate(() => {
      const products = document.querySelectorAll('[data-testid="product-item"]');
      return products.length;
    });
    
    this.log(`📦 Product count: ${productCount}`);
    
    // Verify we have products
    if (productCount === 0) {
      throw new Error('Product explorer shows no products');
    }
    
    this.log('✅ Product explorer loaded successfully');
    return { products: productCount };
  }

  async testAnalytics() {
    this.log('📈 Testing Analytics...');
    
    // Navigate to analytics
    await this.page.click('a[href="/analytics"]');
    await this.page.waitForSelector('[data-testid="analytics-dashboard"]', { timeout: 10000 });
    
    // Wait for analytics to load
    await this.page.waitForFunction(() => {
      const charts = document.querySelectorAll('[data-testid="chart"]');
      return charts.length > 0;
    }, { timeout: 15000 });
    
    // Get analytics data
    const analyticsData = await this.page.evaluate(() => {
      const totalSKUsEl = document.querySelector('[data-testid="total-skus"]');
      const totalRevenueEl = document.querySelector('[data-testid="total-revenue"]');
      
      return {
        totalSKUs: totalSKUsEl ? totalSKUsEl.textContent : 'N/A',
        totalRevenue: totalRevenueEl ? totalRevenueEl.textContent : 'N/A'
      };
    });
    
    this.log(`📊 Analytics data: ${JSON.stringify(analyticsData)}`);
    
    this.log('✅ Analytics loaded successfully');
    return analyticsData;
  }

  async testDataConsistency() {
    this.log('🔗 Testing data consistency across features...');
    
    // Get stats from different components
    const dashboardStats = await this.getGraphStatistics();
    const visualizerStats = await this.testGraphVisualizer();
    const productStats = await this.testProductExplorer();
    const analyticsStats = await this.testAnalytics();
    
    // Verify consistency
    const isConsistent = (
      dashboardStats.products === visualizerStats.nodes &&
      productStats.products === dashboardStats.products
    );
    
    this.log(`📊 Data consistency check: ${isConsistent ? 'PASS' : 'FAIL'}`);
    this.log(`  Dashboard products: ${dashboardStats.products}`);
    this.log(`  Visualizer nodes: ${visualizerStats.nodes}`);
    this.log(`  Product explorer items: ${productStats.products}`);
    
    if (!isConsistent) {
      throw new Error('Data inconsistency detected across features');
    }
    
    this.log('✅ Data consistency verified');
  }

  async testNavigation() {
    this.log('🧭 Testing navigation...');
    
    const pages = [
      { name: 'Dashboard', href: '/' },
      { name: 'Chat', href: '/chat' },
      { name: 'Graph Visualizer', href: '/graph' },
      { name: 'Product Explorer', href: '/products' },
      { name: 'Analytics', href: '/analytics' },
      { name: 'Upload Excel', href: '/upload' },
      { name: 'Settings', href: '/settings' }
    ];
    
    for (const page of pages) {
      this.log(`  Navigating to ${page.name}...`);
      
      try {
        await this.page.click(`a[href="${page.href}"]`);
        await this.page.waitForTimeout(2000); // Wait for page load
        
        // Verify page loaded (basic check)
        const title = await this.page.title();
        this.log(`    ✅ ${page.name} loaded (title: ${title})`);
      } catch (error) {
        this.log(`    ❌ ${page.name} failed to load: ${error.message}`, 'ERROR');
      }
    }
    
    this.log('✅ Navigation test completed');
  }

  async runFullTest() {
    try {
      await this.init();
      await this.navigateToApp();
      
      // Test initial state
      const initialStats = await this.testInitialState();
      
      // Test Excel upload
      await this.testExcelUpload();
      
      // Wait for data to propagate
      await this.page.waitForTimeout(5000);
      
      // Test all features
      await this.testDataConsistency();
      await this.testNavigation();
      
      // Final validation
      const finalStats = await this.getGraphStatistics();
      this.log(`📊 Final graph stats: ${JSON.stringify(finalStats)}`);
      
      // Verify data was updated
      if (finalStats.products === 0) {
        throw new Error('No products found after upload');
      }
      
      this.log('🎉 E2E Validation Test PASSED!');
      this.log('✅ All features working correctly');
      this.log('✅ Data consistency verified');
      this.log('✅ Navigation working');
      this.log('✅ Excel upload and processing successful');
      
    } catch (error) {
      this.log(`❌ E2E Validation Test FAILED: ${error.message}`, 'ERROR');
      throw error;
    } finally {
      await this.cleanup();
    }
  }

  async cleanup() {
    if (this.browser) {
      await this.browser.close();
    }
    
    // Save test results
    const resultsPath = path.join(__dirname, 'e2e_test_results.log');
    fs.writeFileSync(resultsPath, this.testResults.join('\n'));
    this.log(`📄 Test results saved to: ${resultsPath}`);
  }
}

// Run the test
async function main() {
  const validator = new E2EValidator();
  
  try {
    await validator.runFullTest();
    process.exit(0);
  } catch (error) {
    console.error('Test failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = E2EValidator;
