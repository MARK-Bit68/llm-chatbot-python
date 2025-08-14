#!/usr/bin/env node
/**
 * REAL test - no false positives
 */

const puppeteer = require('puppeteer');

async function realTest() {
    console.log('🔍 REAL TEST - Checking what\'s actually deployed');
    
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🌐 Loading https://llm-chatbot-python-production-d789.up.railway.app');
        await page.goto('https://llm-chatbot-python-production-d789.up.railway.app', {
            waitUntil: 'networkidle2'
        });
        
        const title = await page.title();
        console.log(`📄 Page Title: ${title}`);
        
        // Get the actual content
        const bodyText = await page.evaluate(() => document.body.innerText);
        console.log('📝 First 500 characters of page:');
        console.log(bodyText.substring(0, 500));
        console.log('...\n');
        
        // Check specifically for React app elements
        const reactElements = await page.evaluate(() => {
            // Look for specific React app indicators
            const hasReactRoot = document.getElementById('root') !== null;
            const hasModernElements = document.querySelector('.min-h-screen') !== null;
            const hasSupplyGraphText = document.body.textContent.includes('SupplyGraph');
            const hasProductExplorer = document.body.textContent.includes('Product Explorer');
            const hasAdvancedDashboard = document.body.textContent.includes('Advanced Dashboard');
            
            return {
                hasReactRoot,
                hasModernElements,
                hasSupplyGraphText,
                hasProductExplorer,
                hasAdvancedDashboard
            };
        });
        
        console.log('🔍 React App Detection:');
        console.log(`   React root element: ${reactElements.hasReactRoot ? '✅' : '❌'}`);
        console.log(`   Modern CSS classes: ${reactElements.hasModernElements ? '✅' : '❌'}`);
        console.log(`   SupplyGraph text: ${reactElements.hasSupplyGraphText ? '✅' : '❌'}`);
        console.log(`   Product Explorer: ${reactElements.hasProductExplorer ? '✅' : '❌'}`);
        console.log(`   Advanced Dashboard: ${reactElements.hasAdvancedDashboard ? '✅' : '❌'}`);
        
        // Check for Streamlit indicators
        const streamlitElements = await page.evaluate(() => {
            const content = document.body.textContent;
            return {
                hasStreamlitText: content.includes('Streamlit'),
                hasFMCGTitle: content.includes('FMCG Supply Chain Assistant'),
                hasUITheme: content.includes('UI theme'),
                hasControls: content.includes('Controls'),
                hasMonitoring: content.includes('Enable monitoring')
            };
        });
        
        console.log('\n🔍 Streamlit Detection:');
        console.log(`   Streamlit text: ${streamlitElements.hasStreamlitText ? '❌ FOUND' : '✅'}`);
        console.log(`   FMCG title: ${streamlitElements.hasFMCGTitle ? '❌ FOUND' : '✅'}`);
        console.log(`   UI theme controls: ${streamlitElements.hasUITheme ? '❌ FOUND' : '✅'}`);
        console.log(`   Control elements: ${streamlitElements.hasControls ? '❌ FOUND' : '✅'}`);
        console.log(`   Monitoring toggle: ${streamlitElements.hasMonitoring ? '❌ FOUND' : '✅'}`);
        
        // Test health endpoint
        console.log('\n🏥 Testing Health Endpoint:');
        try {
            await page.goto('https://llm-chatbot-python-production-d789.up.railway.app/health');
            const healthContent = await page.evaluate(() => document.body.textContent);
            console.log(`   Health response: ${healthContent.substring(0, 200)}`);
        } catch (error) {
            console.log(`   Health endpoint error: ${error.message}`);
        }
        
        // Final verdict
        const isActuallyModernUI = (
            reactElements.hasReactRoot || 
            reactElements.hasSupplyGraphText || 
            reactElements.hasProductExplorer
        ) && !streamlitElements.hasFMCGTitle;
        
        console.log('\n🎯 FINAL VERDICT:');
        if (isActuallyModernUI) {
            console.log('✅ Modern React UI is deployed');
        } else {
            console.log('❌ Still showing Streamlit - deployment did not work');
            console.log('🔧 Railway is still using the old configuration or deployment failed');
        }
        
        // Take screenshot
        await page.screenshot({ path: './actual_deployment_test.png', fullPage: true });
        console.log('📸 Screenshot saved: actual_deployment_test.png');
        
    } catch (error) {
        console.log(`❌ Error: ${error.message}`);
    }
    
    await browser.close();
}

realTest().catch(console.error);