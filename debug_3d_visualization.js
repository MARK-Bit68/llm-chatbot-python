// Debug script for 3D visualization issues
const puppeteer = require('puppeteer');

async function debug3DVisualization() {
  console.log('🔍 Debugging 3D Graph Visualization...');
  
  const browser = await puppeteer.launch({ headless: false }); // Use non-headless to see what's happening
  const page = await browser.newPage();
  
  // Listen for all console messages
  page.on('console', msg => {
    console.log(`📝 [${msg.type()}] ${msg.text()}`);
  });
  
  // Listen for page errors
  page.on('pageerror', error => {
    console.log('❌ Page Error:', error.message);
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
    
    // Check if the ForceGraph3D component is being imported
    const importStatus = await page.evaluate(() => {
      // Check if ForceGraph3D is available
      if (window.ForceGraph3D) {
        return 'ForceGraph3D is available globally';
      }
      
      // Check if React components are rendering
      const root = document.querySelector('#root');
      if (root) {
        const reactInstance = root._reactInternalFiber;
        if (reactInstance) {
          return 'React is rendering';
        }
      }
      
      return 'React not detected';
    });
    
    console.log('📦 Import status:', importStatus);
    
    // Check the actual DOM structure
    const domStructure = await page.evaluate(() => {
      const vizArea = document.querySelector('[class*="flex-1"]');
      if (vizArea) {
        return {
          tagName: vizArea.tagName,
          className: vizArea.className,
          childrenCount: vizArea.children.length,
          children: Array.from(vizArea.children).map(child => ({
            tagName: child.tagName,
            className: child.className,
            id: child.id
          }))
        };
      }
      return null;
    });
    
    console.log('🏗️ DOM Structure:', domStructure);
    
    // Check if there are any error boundaries or fallback content
    const errorContent = await page.evaluate(() => {
      const errorElements = document.querySelectorAll('[class*="error"], [class*="fallback"], [class*="placeholder"]');
      return Array.from(errorElements).map(el => ({
        className: el.className,
        textContent: el.textContent.substring(0, 100)
      }));
    });
    
    console.log('⚠️ Error/Fallback content:', errorContent);
    
    // Wait for user to see the page
    console.log('👀 Browser window opened - please check the page manually');
    await page.waitForTimeout(30000); // Wait 30 seconds for manual inspection
    
  } catch (error) {
    console.error('❌ Debug failed:', error.message);
  } finally {
    await browser.close();
  }
}

debug3DVisualization();
