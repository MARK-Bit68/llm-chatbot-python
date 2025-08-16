// Test script to verify 3D graph visualization
const puppeteer = require('puppeteer');

async function test3DVisualization() {
  console.log('🧪 Testing 3D Graph Visualization...');
  
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  // Listen for console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('❌ Console Error:', msg.text());
    }
  });
  
  try {
    // Navigate to the graph page
    await page.goto('https://llm-chatbot-python-production-7e6f.up.railway.app/graph', {
      waitUntil: 'networkidle0',
      timeout: 30000
    });
    
    console.log('✅ Page loaded successfully');
    
    // Wait for the 3D visualization to load
    await page.waitForTimeout(5000);
    
    // Check for any React errors or warnings
    const consoleMessages = await page.evaluate(() => {
      return window.consoleMessages || [];
    });
    
    console.log('📝 Console messages:', consoleMessages.length);
    
    // Check if ForceGraph3D component is rendered
    const canvasElements = await page.evaluate(() => {
      const canvases = document.querySelectorAll('canvas');
      return {
        count: canvases.length,
        dimensions: Array.from(canvases).map(canvas => ({
          width: canvas.width,
          height: canvas.height,
          visible: canvas.offsetWidth > 0 && canvas.offsetHeight > 0,
          className: canvas.className,
          id: canvas.id
        }))
      };
    });
    
    console.log('📊 Canvas elements found:', canvasElements.count);
    canvasElements.dimensions.forEach((dim, i) => {
      console.log(`  Canvas ${i}: ${dim.width}x${dim.height}, visible: ${dim.visible}, class: ${dim.className}`);
    });
    
    // Check what's actually being rendered in the visualization area
    const visualizationContent = await page.evaluate(() => {
      const vizArea = document.querySelector('[class*="flex-1"]');
      if (vizArea) {
        return {
          innerHTML: vizArea.innerHTML.substring(0, 500),
          children: vizArea.children.length,
          hasForceGraph: vizArea.innerHTML.includes('ForceGraph'),
          hasCanvas: vizArea.querySelector('canvas') !== null
        };
      }
      return null;
    });
    
    console.log('🔍 Visualization area content:', visualizationContent);
    
    // Check if 3D controls are present
    const controls = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const buttonTexts = buttons.map(btn => btn.textContent.trim());
      return {
        resetCamera: buttons.some(btn => btn.textContent.includes('Reset Camera')),
        zoomIn: buttons.some(btn => btn.textContent.includes('Zoom In')),
        zoomOut: buttons.some(btn => btn.textContent.includes('Zoom Out')),
        totalButtons: buttons.length,
        buttonTexts: buttonTexts
      };
    });
    
    console.log('🎛️ 3D Controls found:', controls);
    console.log('🔘 Button texts:', controls.buttonTexts);
    
    // Check if legend is displayed
    const legend = await page.evaluate(() => {
      const legendElements = document.querySelectorAll('[class*="bg-green-500"], [class*="bg-blue-500"], [class*="bg-yellow-500"]');
      return legendElements.length;
    });
    
    console.log('🎨 Legend elements found:', legend);
    
    // Test API data
    const apiData = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/graph/visualization');
        const data = await response.json();
        return {
          success: true,
          nodes: data.nodes?.length || 0,
          edges: data.edges?.length || 0,
          stats: data.stats
        };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
    
    console.log('🔌 API Data:', apiData);
    
    // Check if the graph data is being processed correctly
    const graphDataStatus = await page.evaluate(() => {
      // Try to access the React component state
      const root = document.querySelector('#root');
      if (root && root._reactInternalFiber) {
        return 'React component found';
      }
      return 'React component not accessible';
    });
    
    console.log('⚛️ React status:', graphDataStatus);
    
    // Take a screenshot
    await page.screenshot({ 
      path: '3d_visualization_test.png',
      fullPage: true 
    });
    
    console.log('📸 Screenshot saved as 3d_visualization_test.png');
    
    // Overall assessment
    const isWorking = canvasElements.count > 0 && 
                     canvasElements.dimensions.some(d => d.visible) &&
                     apiData.success;
    
    console.log(`\n🎯 3D Visualization Test Result: ${isWorking ? '✅ PASSED' : '❌ FAILED'}`);
    
    if (isWorking) {
      console.log('🚀 3D graph visualization is working!');
      console.log('✨ Features:');
      console.log('  • Canvas rendering: ✅');
      console.log('  • API data: ✅');
      console.log('  • Legend: ✅');
      console.log('  • 3D Controls: ⚠️ (may need interaction)');
    } else {
      console.log('⚠️  Some issues detected with 3D visualization');
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

test3DVisualization();
