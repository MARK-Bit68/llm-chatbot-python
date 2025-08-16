// Detailed test to debug 3D visualization issues
const puppeteer = require('puppeteer');

async function test3DDetailed() {
  console.log('🔍 Detailed 3D Visualization Debug...');
  
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  // Capture all console messages
  const consoleMessages = [];
  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text()
    });
  });
  
  try {
    // Navigate to the graph page
    await page.goto('https://llm-chatbot-python-production-7e6f.up.railway.app/graph', {
      waitUntil: 'networkidle0',
      timeout: 30000
    });
    
    console.log('✅ Page loaded successfully');
    
    // Wait for the 3D visualization to load
    await page.waitForTimeout(10000);
    
    // Print all console messages
    console.log('\n📝 All Console Messages:');
    consoleMessages.forEach((msg, i) => {
      console.log(`  [${i}] [${msg.type}] ${msg.text}`);
    });
    
    // Check viewMode
    const viewMode = await page.evaluate(() => {
      // Try to access React state
      const root = document.querySelector('#root');
      if (root && root._reactInternalFiber) {
        return 'React root found';
      }
      return 'React root not accessible';
    });
    
    console.log('\n🎯 ViewMode Status:', viewMode);
    
    // Check if 3D controls are actually rendered
    const controlsStatus = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const controlButtons = buttons.filter(btn => 
        btn.textContent.includes('Reset Camera') ||
        btn.textContent.includes('Zoom In') ||
        btn.textContent.includes('Zoom Out')
      );
      
      return {
        totalButtons: buttons.length,
        controlButtons: controlButtons.length,
        buttonTexts: buttons.map(btn => btn.textContent.trim()),
        controlButtonTexts: controlButtons.map(btn => btn.textContent.trim())
      };
    });
    
    console.log('\n🎛️ Controls Status:', controlsStatus);
    
    // Check the actual DOM structure
    const domStructure = await page.evaluate(() => {
      const main = document.querySelector('main');
      if (main) {
        return {
          tagName: main.tagName,
          className: main.className,
          childrenCount: main.children.length,
          children: Array.from(main.children).map(child => ({
            tagName: child.tagName,
            className: child.className,
            childrenCount: child.children.length
          }))
        };
      }
      return null;
    });
    
    console.log('\n🏗️ DOM Structure:', JSON.stringify(domStructure, null, 2));
    
    // Check if ForceGraph3D is rendering edges
    const edgeStatus = await page.evaluate(() => {
      const canvas = document.querySelector('canvas');
      if (canvas) {
        // Check if there are any WebGL draw calls or 3D elements
        const webglContext = canvas.getContext('webgl') || canvas.getContext('webgl2');
        if (webglContext) {
          // Try to get some WebGL info
          return {
            hasCanvas: true,
            hasWebGL: true,
            webglVendor: webglContext.getParameter(webglContext.VENDOR),
            webglRenderer: webglContext.getParameter(webglContext.RENDERER),
            webglVersion: webglContext.getParameter(webglContext.VERSION)
          };
        }
      }
      return { hasCanvas: false, hasWebGL: false };
    });
    
    console.log('\n🔗 Edge Status:', edgeStatus);
    
    // Check the graph data being passed to ForceGraph3D
    const graphDataDebug = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/graph/visualization');
        const data = await response.json();
        
        // Check if edges have proper source/target mapping
        const sampleEdges = data.edges?.slice(0, 5) || [];
        const nodeIds = data.nodes?.map(n => n.id) || [];
        
        return {
          nodesCount: data.nodes?.length || 0,
          edgesCount: data.edges?.length || 0,
          sampleEdges: sampleEdges,
          nodeIds: nodeIds.slice(0, 10),
          edgeSourceTypes: sampleEdges.map(e => typeof e.source),
          edgeTargetTypes: sampleEdges.map(e => typeof e.target)
        };
      } catch (error) {
        return { error: error.message };
      }
    });
    
    console.log('\n📊 Graph Data Debug:', JSON.stringify(graphDataDebug, null, 2));
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

test3DDetailed();
