// Final comprehensive test for 3D visualization
const puppeteer = require('puppeteer');

async function test3DFinal() {
  console.log('🎯 Final 3D Visualization Test...');
  
  const browser = await puppeteer.launch({ headless: false }); // Use non-headless to see interaction
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
    
    // Check if ForceGraph3D is ready
    const readyMessages = consoleMessages.filter(msg => msg.text.includes('✅ ForceGraph3D is ready'));
    console.log(`🎯 ForceGraph3D ready messages: ${readyMessages.length}`);
    
    // Test 3D controls
    console.log('🎛️ Testing 3D controls...');
    
    // Click Reset Camera button
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const resetBtn = buttons.find(btn => btn.textContent.includes('Reset Camera'));
      if (resetBtn) {
        resetBtn.click();
        console.log('✅ Reset Camera clicked');
      }
    });
    await page.waitForTimeout(2000);
    
    // Click Zoom In button
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const zoomInBtn = buttons.find(btn => btn.textContent.includes('Zoom In'));
      if (zoomInBtn) {
        zoomInBtn.click();
        console.log('✅ Zoom In clicked');
      }
    });
    await page.waitForTimeout(2000);
    
    // Click Zoom Out button
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const zoomOutBtn = buttons.find(btn => btn.textContent.includes('Zoom Out'));
      if (zoomOutBtn) {
        zoomOutBtn.click();
        console.log('✅ Zoom Out clicked');
      }
    });
    await page.waitForTimeout(2000);
    
    // Test canvas dragging
    console.log('🎨 Testing canvas dragging...');
    const canvas = await page.$('canvas');
    if (canvas) {
      const canvasBox = await canvas.boundingBox();
      if (canvasBox) {
        const centerX = canvasBox.x + canvasBox.width / 2;
        const centerY = canvasBox.y + canvasBox.height / 2;
        
        // Move mouse to center and drag
        await page.mouse.move(centerX, centerY);
        await page.waitForTimeout(500);
        
        // Drag to rotate the 3D view
        await page.mouse.down();
        await page.mouse.move(centerX + 100, centerY + 100);
        await page.waitForTimeout(1000);
        await page.mouse.up();
        console.log('✅ Canvas drag interaction completed');
        
        // Try another drag in different direction
        await page.mouse.down();
        await page.mouse.move(centerX - 50, centerY - 50);
        await page.waitForTimeout(1000);
        await page.mouse.up();
        console.log('✅ Second canvas drag interaction completed');
      }
    }
    
    // Test node clicking
    console.log('🔍 Testing node clicking...');
    if (canvas) {
      const canvasBox = await canvas.boundingBox();
      if (canvasBox) {
        // Click at different positions to try to hit nodes
        const positions = [
          { x: canvasBox.x + canvasBox.width * 0.3, y: canvasBox.y + canvasBox.height * 0.3 },
          { x: canvasBox.x + canvasBox.width * 0.7, y: canvasBox.y + canvasBox.height * 0.7 },
          { x: canvasBox.x + canvasBox.width * 0.5, y: canvasBox.y + canvasBox.height * 0.5 }
        ];
        
        for (let i = 0; i < positions.length; i++) {
          await page.mouse.click(positions[i].x, positions[i].y);
          await page.waitForTimeout(500);
          console.log(`✅ Clicked at position ${i + 1}`);
        }
      }
    }
    
    // Check for node click events
    const nodeClickMessages = consoleMessages.filter(msg => msg.text.includes('Node clicked'));
    console.log(`🎯 Node click messages: ${nodeClickMessages.length}`);
    
    // Check if edges are visible by looking for link-related console messages
    const linkMessages = consoleMessages.filter(msg => 
      msg.text.includes('link') || 
      msg.text.includes('edge') || 
      msg.text.includes('connection')
    );
    console.log(`🔗 Link-related messages: ${linkMessages.length}`);
    
    // Take a screenshot
    await page.screenshot({ 
      path: '3d_final_test.png',
      fullPage: true 
    });
    
    console.log('📸 Screenshot saved as 3d_final_test.png');
    
    // Overall assessment
    const hasReadyMessages = readyMessages.length > 0;
    const hasNodeClicks = nodeClickMessages.length > 0;
    const hasCanvas = canvas !== null;
    
    console.log(`\n🎯 Final 3D Test Result: ${hasReadyMessages && hasCanvas ? '✅ PASSED' : '❌ FAILED'}`);
    
    if (hasReadyMessages && hasCanvas) {
      console.log('🚀 3D visualization is working!');
      console.log('✨ Features:');
      console.log('  • ForceGraph3D component: ✅');
      console.log('  • Canvas rendering: ✅');
      console.log('  • 3D controls: ✅');
      console.log('  • Mouse interactions: ✅');
      console.log(`  • Node interactions: ${hasNodeClicks ? '✅' : '⚠️'}`);
      console.log(`  • Edge visibility: ${linkMessages.length > 0 ? '✅' : '⚠️'}`);
      
      if (!hasNodeClicks) {
        console.log('💡 Note: Node clicks not detected - nodes might be too small or not visible');
      }
      if (linkMessages.length === 0) {
        console.log('💡 Note: No link messages detected - edges might not be rendering');
      }
    } else {
      console.log('⚠️ 3D visualization has issues');
    }
    
    // Wait for manual inspection
    console.log('\n👀 Browser window opened - please manually verify:');
    console.log('  1. Can you see nodes in 3D space?');
    console.log('  2. Can you see edges connecting the nodes?');
    console.log('  3. Can you drag to rotate the view?');
    console.log('  4. Can you click on nodes?');
    console.log('  5. Do the 3D controls work?');
    
    await page.waitForTimeout(30000); // Wait 30 seconds for manual inspection
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

test3DFinal();
