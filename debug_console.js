// Debug script to capture detailed console output
const puppeteer = require('puppeteer');

async function debugConsole() {
  console.log('🔍 Debugging Console Output...');
  
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  // Capture all console messages
  const consoleMessages = [];
  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });
  
  // Capture page errors
  const pageErrors = [];
  page.on('pageerror', error => {
    pageErrors.push(error.message);
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
    
    // Print page errors
    if (pageErrors.length > 0) {
      console.log('\n❌ Page Errors:');
      pageErrors.forEach((error, i) => {
        console.log(`  [${i}] ${error}`);
      });
    }
    
    // Check if ForceGraph3D is available
    const forceGraphStatus = await page.evaluate(() => {
      try {
        // Check if ForceGraph3D is imported
        if (window.ForceGraph3D) {
          return 'ForceGraph3D available globally';
        }
        
        // Check if it's available in React
        const root = document.querySelector('#root');
        if (root && root._reactInternalFiber) {
          return 'React root found';
        }
        
        return 'ForceGraph3D not detected';
      } catch (error) {
        return `Error checking ForceGraph3D: ${error.message}`;
      }
    });
    
    console.log('\n🔍 ForceGraph3D Status:', forceGraphStatus);
    
    // Check the actual rendered content
    const renderedContent = await page.evaluate(() => {
      // Look for the main visualization area (not the sidebar)
      const vizArea = document.querySelector('main') || 
                     document.querySelector('[class*="bg-gradient"]') ||
                     document.querySelector('[class*="absolute inset-0"]');
      
      if (vizArea) {
        return {
          tagName: vizArea.tagName,
          className: vizArea.className,
          childrenCount: vizArea.children.length,
          children: Array.from(vizArea.children).map(child => ({
            tagName: child.tagName,
            className: child.className,
            id: child.id,
            textContent: child.textContent?.substring(0, 100)
          }))
        };
      }
      
      // If not found, check all divs with flex-1
      const allFlex1 = document.querySelectorAll('[class*="flex-1"]');
      return {
        message: 'Main viz area not found, showing all flex-1 elements',
        count: allFlex1.length,
        elements: Array.from(allFlex1).map((el, i) => ({
          index: i,
          tagName: el.tagName,
          className: el.className,
          childrenCount: el.children.length
        }))
      };
    });
    
    console.log('\n🏗️ Rendered Content:', JSON.stringify(renderedContent, null, 2));
    
  } catch (error) {
    console.error('❌ Debug failed:', error.message);
  } finally {
    await browser.close();
  }
}

debugConsole();
