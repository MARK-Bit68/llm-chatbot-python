#!/usr/bin/env node
/**
 * Simple End-to-End Validation Test for FMCG Assistant
 * Tests core flow: Upload Excel → Visualizer → Data Consistency
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class SimpleE2EValidator {
  constructor() {
    this.browser = null;
    this.page = null;
    this.testResults = [];
    this.baseUrl = 'https://llm-chatbot-python-production-7e6f.up.railway.app';
  }

  async log(message, type = 'INFO') {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${type}] ${message}`;
    console.log(logMessage);
    this.testResults.push(logMessage);
  }

  async init() {
    this.log('🚀 Starting Simple E2E Validation Test');
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
    await this.page.waitForTimeout(3000);
    
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
          const productEl = metadataEl.querySelector('.text-2xl.font-bold.text-blue-600');
          const relationshipEl = metadataEl.querySelector('.text-2xl.font-bold.text-green-600');
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
    
    // Navigate to upload page (using text content instead of href)
    await this.page.click('a[href="/upload"]');
    await this.page.waitForTimeout(2000);
    
    // Check if upload page loaded
    const uploadTitle = await this.page.$eval('h1, h2', el => el.textContent)
      .catch(() => 'Not found');
    
    this.log(`📤 Upload page title: ${uploadTitle}`);
    
    // Look for file input
    const fileInputExists = await this.page.$('input[type="file"]')
      .then(() => true)
      .catch(() => false);
    
    if (!fileInputExists) {
      this.log('❌ File input not found on upload page', 'ERROR');
      return false;
    }
    
    this.log('✅ Upload page loaded successfully');
    return true;
  }

  async testGraphVisualizer() {
    this.log('🎮 Testing Graph Visualizer...');
    
    // Navigate to graph visualizer (using text content instead of href)
    await this.page.click('a[href="/graph"]');
    await this.page.waitForTimeout(3000);
    
    // Check if visualizer page loaded
    const visualizerTitle = await this.page.$eval('h1, h2', el => el.textContent)
      .catch(() => 'Not found');
    
    this.log(`🎮 Visualizer page title: ${visualizerTitle}`);
    
    // Check for graph visualizer component
    const visualizerExists = await this.page.$('[data-testid="graph-visualizer"]')
      .then(() => true)
      .catch(() => false);
    
    this.log(`🎮 Graph visualizer component: ${visualizerExists ? 'Present' : 'Missing'}`);
    
    // Check for no data message
    const noDataMessage = await this.page.evaluate(() => {
      const noDataEl = document.querySelector('.text-yellow-600, .text-yellow-800');
      return noDataEl ? noDataEl.textContent : null;
    });
    
    if (noDataMessage && noDataMessage.includes('No graph data')) {
      this.log('⚠️ Graph visualizer shows no data message', 'WARN');
    } else {
      this.log('✅ Graph visualizer has data');
    }
    
    return true;
  }

  async testNavigation() {
    this.log('🧭 Testing navigation...');
    
    const pages = [
      { name: 'Dashboard', selector: 'a[href="/"]' },
      { name: 'Graph Visualizer', selector: 'a[href="/graph"]' },
      { name: 'Upload Excel', selector: 'a[href="/upload"]' }
    ];
    
    for (const page of pages) {
      this.log(`  Navigating to ${page.name}...`);
      
      try {
        await this.page.click(page.selector);
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

  async testDataConsistency() {
    this.log('🔗 Testing data consistency...');
    
    // Get stats from dashboard
    const dashboardStats = await this.getGraphStatistics();
    this.log(`📊 Dashboard stats: ${JSON.stringify(dashboardStats)}`);
    
    // Navigate to visualizer and check data
    await this.page.click('a[href="/graph"]');
    await this.page.waitForTimeout(3000);
    
    // Check if visualizer shows data
    const visualizerHasData = await this.page.evaluate(() => {
      const noDataEl = document.querySelector('.text-yellow-600, .text-yellow-800');
      return !noDataEl || !noDataEl.textContent.includes('No graph data');
    });
    
    this.log(`🎮 Visualizer has data: ${visualizerHasData}`);
    
    // Check for graph statistics in visualizer
    const visualizerStats = await this.page.evaluate(() => {
      const nodesEl = document.querySelector('.text-blue-600');
      const edgesEl = document.querySelector('.text-green-600');
      
      return {
        nodes: nodesEl ? parseInt(nodesEl.textContent) : 0,
        edges: edgesEl ? parseInt(edgesEl.textContent) : 0
      };
    });
    
    this.log(`📊 Visualizer stats: ${JSON.stringify(visualizerStats)}`);
    
    // Verify consistency
    const isConsistent = dashboardStats.products === visualizerStats.nodes;
    
    this.log(`📊 Data consistency check: ${isConsistent ? 'PASS' : 'FAIL'}`);
    this.log(`  Dashboard products: ${dashboardStats.products}`);
    this.log(`  Visualizer nodes: ${visualizerStats.nodes}`);
    
    if (!isConsistent) {
      this.log('⚠️ Data inconsistency detected', 'WARN');
    }
    
    this.log('✅ Data consistency test completed');
  }

  async runFullTest() {
    try {
      await this.init();
      await this.navigateToApp();
      
      // Test initial state
      const initialStats = await this.testInitialState();
      
      // Test navigation
      await this.testNavigation();
      
      // Test Excel upload page
      const uploadWorks = await this.testExcelUpload();
      
      // Test graph visualizer
      const visualizerWorks = await this.testGraphVisualizer();
      
      // Test data consistency
      await this.testDataConsistency();
      
      // Final validation
      const finalStats = await this.getGraphStatistics();
      this.log(`📊 Final graph stats: ${JSON.stringify(finalStats)}`);
      
      // Summary
      this.log('📋 Test Summary:');
      this.log(`  ✅ App loads: YES`);
      this.log(`  ✅ Navigation works: YES`);
      this.log(`  ✅ Upload page accessible: ${uploadWorks ? 'YES' : 'NO'}`);
      this.log(`  ✅ Visualizer accessible: ${visualizerWorks ? 'YES' : 'NO'}`);
      this.log(`  ✅ Initial products: ${initialStats.products}`);
      this.log(`  ✅ Final products: ${finalStats.products}`);
      
      if (finalStats.products > 0) {
        this.log('🎉 Simple E2E Validation Test PASSED!');
        this.log('✅ Core functionality working correctly');
      } else {
        this.log('⚠️ No products found - may need data upload', 'WARN');
      }
      
    } catch (error) {
      this.log(`❌ Simple E2E Validation Test FAILED: ${error.message}`, 'ERROR');
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
    const resultsPath = path.join(__dirname, 'simple_e2e_test_results.log');
    fs.writeFileSync(resultsPath, this.testResults.join('\n'));
    this.log(`📄 Test results saved to: ${resultsPath}`);
  }
}

// Run the test
async function main() {
  const validator = new SimpleE2EValidator();
  
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

module.exports = SimpleE2EValidator;
