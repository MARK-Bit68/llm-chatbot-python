#!/usr/bin/env node
/**
 * Test only the deployed Railway app
 */

const puppeteer = require('puppeteer');

async function testDeployedApp() {
    console.log('🚀 Testing Deployed Railway App');
    
    const browser = await puppeteer.launch({
        headless: false,
        defaultViewport: { width: 1920, height: 1080 }
    });

    const page = await browser.newPage();
    
    try {
        console.log('🔍 Testing: https://llm-chatbot-python-production-d789.up.railway.app');
        
        const response = await page.goto('https://llm-chatbot-python-production-d789.up.railway.app', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log(`✅ Response: ${response.status()} ${response.statusText()}`);
        
        // Take a screenshot
        await page.screenshot({ 
            path: './railway_app_screenshot.png', 
            fullPage: true 
        });
        console.log('📸 Screenshot saved: railway_app_screenshot.png');
        
        // Check what's on the page
        const title = await page.title();
        console.log(`📄 Page Title: ${title}`);
        
        const bodyText = await page.evaluate(() => document.body.innerText);
        console.log(`📝 Page Content (first 500 chars): ${bodyText.substring(0, 500)}...`);
        
        // Check if it's our React app or an error page
        const hasReactApp = await page.evaluate(() => {
            return document.body.textContent.includes('SupplyGraph') ||
                   document.body.textContent.includes('Product Explorer') ||
                   document.body.textContent.includes('Advanced Dashboard') ||
                   document.querySelector('[data-testid="app"], .min-h-screen, #root') !== null;
        });
        
        if (hasReactApp) {
            console.log('✅ React app detected!');
        } else {
            console.log('❌ React app not detected - likely showing error page');
        }
        
        // Test health endpoint
        try {
            const healthResponse = await page.goto('https://llm-chatbot-python-production-d789.up.railway.app/health');
            console.log(`🏥 Health Check: ${healthResponse.status()} ${healthResponse.statusText()}`);
            
            if (healthResponse.ok()) {
                const healthData = await page.evaluate(() => document.body.textContent);
                console.log(`💓 Health Data: ${healthData}`);
            }
        } catch (error) {
            console.log(`❌ Health check failed: ${error.message}`);
        }
        
    } catch (error) {
        console.log(`❌ Error: ${error.message}`);
        
        // Take error screenshot
        await page.screenshot({ 
            path: './railway_app_error.png', 
            fullPage: true 
        });
        console.log('📸 Error screenshot saved: railway_app_error.png');
    }
    
    await browser.close();
}

testDeployedApp().catch(console.error);