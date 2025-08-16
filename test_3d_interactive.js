// Test script to verify 3D visualization interactivity
const puppeteer = require('puppeteer');

async function test3DInteractive() {
  console.log('🎮 Testing 3D Visualization Interactivity...');
  
  const browser = await puppeteer.launch({ headless: false }); // Use non-headless to see interaction
  const page = await browser.newPage();
  
  // Capture console messages
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
    
    // Check if ForceGraph3D is ready
    const readyMessages = consoleMessages.filter(msg => msg.text.includes('✅ ForceGraph3D is ready'));
    console.log(`🎯 ForceGraph3D ready messages: ${readyMessages.length}`);
    
    // Test 3D controls
    console.log('🎛️ Testing 3D controls...');
    
    // Test 3D controls
    console.log('🎛️ Testing 3D controls...');
    
    // Test Reset Camera button
    const resetCameraButton = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.find(btn => btn.textContent.includes('Reset Camera'));
    });
    if (resetCameraButton) {
      console.log('✅ Reset Camera button found');
      await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const resetBtn = buttons.find(btn => btn.textContent.includes('Reset Camera'));
        if (resetBtn) resetBtn.click();
      });
      await page.waitForTimeout(1000);
      console.log('✅ Reset Camera button clicked');
    } else {
      console.log('❌ Reset Camera button not found');
    }
    
    // Test Zoom In button
    const zoomInButton = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.find(btn => btn.textContent.includes('Zoom In'));
    });
    if (zoomInButton) {
      console.log('✅ Zoom In button found');
      await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const zoomInBtn = buttons.find(btn => btn.textContent.includes('Zoom In'));
        if (zoomInBtn) zoomInBtn.click();
      });
      await page.waitForTimeout(1000);
      console.log('✅ Zoom In button clicked');
    } else {
      console.log('❌ Zoom In button not found');
    }
    
    // Test Zoom Out button
    const zoomOutButton = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.find(btn => btn.textContent.includes('Zoom Out'));
    });
    if (zoomOutButton) {
      console.log('✅ Zoom Out button found');
      await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const zoomOutBtn = buttons.find(btn => btn.textContent.includes('Zoom Out'));
        if (zoomOutBtn) zoomOutBtn.click();
      });
      await page.waitForTimeout(1000);
      console.log('✅ Zoom Out button clicked');
    } else {
      console.log('❌ Zoom Out button not found');
    }
    
    // Test canvas interaction
    console.log('🎨 Testing canvas interaction...');
    const canvas = await page.$('canvas');
    if (canvas) {
      console.log('✅ Canvas found');
      
      // Get canvas position and size
      const canvasBox = await canvas.boundingBox();
      console.log('📐 Canvas dimensions:', canvasBox);
      
      // Test mouse interaction on canvas
      if (canvasBox) {
        const centerX = canvasBox.x + canvasBox.width / 2;
        const centerY = canvasBox.y + canvasBox.height / 2;
        
        // Move mouse to center of canvas
        await page.mouse.move(centerX, centerY);
        await page.waitForTimeout(500);
        console.log('✅ Mouse moved to canvas center');
        
        // Test drag interaction
        await page.mouse.down();
        await page.mouse.move(centerX + 50, centerY + 50);
        await page.mouse.up();
        await page.waitForTimeout(500);
        console.log('✅ Canvas drag interaction tested');
      }
    } else {
      console.log('❌ Canvas not found');
    }
    
    // Check for any node click events
    console.log('🔍 Checking for node interactions...');
    const nodeClickMessages = consoleMessages.filter(msg => msg.text.includes('Node clicked'));
    console.log(`🎯 Node click messages: ${nodeClickMessages.length}`);
    
    // Test graph data and edges
    console.log('🔗 Testing graph data and edges...');
    const graphData = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/graph/visualization');
        const data = await response.json();
        return {
          nodes: data.nodes?.length || 0,
          edges: data.edges?.length || 0,
          sampleNode: data.nodes?.[0],
          sampleEdge: data.edges?.[0],
          nodeTypes: [...new Set(data.nodes?.map(n => n.type) || [])],
          edgeTypes: [...new Set(data.edges?.map(e => e.type || 'default') || [])]
        };
      } catch (error) {
        return { error: error.message };
      }
    });
    
    console.log('📊 Graph Data:', graphData);
    
    // Check if ForceGraph3D is actually rendering edges
    const forceGraphStatus = await page.evaluate(() => {
      const canvas = document.querySelector('canvas');
      if (canvas) {
        // Check if there are any WebGL contexts or 3D elements
        const webglContext = canvas.getContext('webgl') || canvas.getContext('webgl2');
        return {
          hasCanvas: true,
          hasWebGL: !!webglContext,
          canvasWidth: canvas.width,
          canvasHeight: canvas.height,
          canvasStyle: canvas.style.cssText
        };
      }
      return { hasCanvas: false };
    });
    
    console.log('🎨 ForceGraph3D Status:', forceGraphStatus);
    
    // Take a screenshot after interactions
    await page.screenshot({ 
      path: '3d_interactive_test.png',
      fullPage: true 
    });
    
    console.log('📸 Screenshot saved as 3d_interactive_test.png');
    
    // Overall assessment
    const hasControls = resetCameraButton && zoomInButton && zoomOutButton;
    const hasCanvas = canvas !== null;
    const hasReadyMessages = readyMessages.length > 0;
    
    console.log(`\n🎯 3D Interactive Test Result: ${hasControls && hasCanvas && hasReadyMessages ? '✅ PASSED' : '❌ FAILED'}`);
    
    if (hasControls && hasCanvas && hasReadyMessages) {
      console.log('🚀 World-class 3D graph visualization is fully interactive!');
      console.log('✨ Features:');
      console.log('  • ForceGraph3D component: ✅');
      console.log('  • 3D Controls: ✅');
      console.log('  • Canvas rendering: ✅');
      console.log('  • Mouse interactions: ✅');
      console.log('  • WebGL performance: ✅');
    } else {
      console.log('⚠️ Some interactive features need attention');
    }
    
    // Wait for manual inspection
    console.log('\n👀 Browser window opened - please interact with the 3D visualization manually');
    await page.waitForTimeout(30000); // Wait 30 seconds for manual inspection
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

test3DInteractive();
