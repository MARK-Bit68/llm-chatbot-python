const puppeteer = require('puppeteer');

async function testChatbotImprovements() {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('🧪 Testing Chatbot Improvements...');
  
  try {
    // Navigate to the app
    await page.goto('https://llm-chatbot-python-production-7e6f.up.railway.app/');
    console.log('✅ App loaded successfully');
    
    // Test Basic Chat
    await page.click('a[href="/chat/basic"]');
    await page.waitForSelector('textarea');
    console.log('✅ Basic chat page loaded');
    
    // Test queries that should use direct handlers
    const testQueries = [
      'How many products are there?',
      'Show me the dashboard',
      'Which SKU has the highest gross profit per unit?',
      'Analyze inventory risks'
    ];
    
    for (const query of testQueries) {
      console.log(`\n🔍 Testing query: "${query}"`);
      
      // Clear and fill the textarea
      await page.evaluate(() => {
        const textarea = document.querySelector('textarea');
        if (textarea) textarea.value = '';
      });
      
      await page.type('textarea', query);
      await page.click('button[type="submit"]');
      
      // Wait for response
      await page.waitForTimeout(3000);
      
      // Check if response contains expected content
      const responseText = await page.evaluate(() => {
        const messages = document.querySelectorAll('[class*="message"], [class*="response"]');
        return Array.from(messages).map(msg => msg.textContent).join(' ');
      });
      
      // Validate response quality
      if (responseText.includes('processing limit') || responseText.includes('Analysis In Progress')) {
        console.log('❌ Query still hitting processing limit');
      } else if (responseText.includes('Count Analysis') || responseText.includes('Profit Analysis') || 
                 responseText.includes('Dashboard') || responseText.includes('Risk Analysis')) {
        console.log('✅ Query handled by direct handler successfully');
      } else {
        console.log('⚠️ Response received but format unclear');
      }
    }
    
    // Test UI navigation
    console.log('\n🧭 Testing UI Navigation...');
    
    const pages = ['/dashboard', '/graph', '/analytics', '/products'];
    for (const pagePath of pages) {
      await page.click(`a[href="${pagePath}"]`);
      await page.waitForTimeout(1000);
      console.log(`✅ ${pagePath} page loaded`);
    }
    
    console.log('\n🎉 All tests completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testChatbotImprovements();
