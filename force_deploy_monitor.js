#!/usr/bin/env node
/**
 * Monitor Railway to see if it actually deploys the new configuration
 */

const puppeteer = require('puppeteer');

async function monitorForceDeploy() {
    console.log('🚀 Monitoring Force Deploy - Railway Configuration Change');
    console.log('========================================================');
    console.log('⏱️ Checking every minute for up to 10 minutes');
    console.log('🎯 Looking for: Python main.py server instead of Streamlit\n');
    
    const browser = await puppeteer.launch({ headless: false });
    
    for (let attempt = 1; attempt <= 10; attempt++) {
        console.log(`🔍 Check ${attempt}/10 - ${new Date().toLocaleTimeString()}`);
        
        const page = await browser.newPage();
        
        try {
            await page.goto('https://llm-chatbot-python-production-d789.up.railway.app', {
                waitUntil: 'networkidle2',
                timeout: 30000
            });
            
            const title = await page.title();
            console.log(`   📄 Title: ${title}`);
            
            // Check what's actually running
            const appType = await page.evaluate(() => {
                const content = document.body.textContent;
                
                // Clear indicators of Streamlit
                const isStreamlit = content.includes('UI theme') && 
                                  content.includes('Enable monitoring') &&
                                  content.includes('FMCG Supply Chain Assistant');
                
                // Clear indicators of React + FastAPI
                const isReactApp = document.querySelector('#root') !== null ||
                                 content.includes('SupplyGraph Analytics Platform') ||
                                 content.includes('Product Explorer') ||
                                 document.querySelector('.min-h-screen') !== null;
                
                return {
                    isStreamlit,
                    isReactApp,
                    hasHealthEndpoint: false // We'll test this separately
                };
            });
            
            // Test health endpoint - this is KEY indicator
            let healthWorks = false;
            try {
                await page.goto('https://llm-chatbot-python-production-d789.up.railway.app/health');
                const healthContent = await page.evaluate(() => document.body.textContent);
                
                if (healthContent.includes('healthy') && healthContent.includes('services')) {
                    healthWorks = true;
                    console.log('   💚 Health endpoint works - FastAPI is running!');
                } else {
                    console.log('   ⚠️ Health endpoint exists but unexpected content');
                }
            } catch (error) {
                console.log('   ❌ Health endpoint not working - still Streamlit');
            }
            
            // Final determination
            if (healthWorks && !appType.isStreamlit) {
                console.log('\n🎉 SUCCESS! Railway deployed the new configuration!');
                console.log('✅ Python main.py server is running');
                console.log('✅ FastAPI backend operational');
                console.log('✅ React UI should be loading');
                
                // Go back to main page to see React UI
                await page.goto('https://llm-chatbot-python-production-d789.up.railway.app');
                await page.screenshot({ path: './successful_deployment.png', fullPage: true });
                console.log('📸 Success screenshot saved');
                
                await page.close();
                await browser.close();
                return;
                
            } else if (appType.isStreamlit) {
                console.log(`   🔄 Still Streamlit - Railway hasn't rebuilt yet`);
                
            } else {
                console.log(`   ❓ Unknown state - investigating...`);
                const bodyText = await page.evaluate(() => document.body.innerText);
                console.log(`   📝 Content: ${bodyText.substring(0, 150)}...`);
            }
            
        } catch (error) {
            console.log(`   ❌ Error: ${error.message}`);
        }
        
        await page.close();
        
        if (attempt < 10) {
            console.log('   ⏳ Waiting 1 minute...\n');
            await new Promise(resolve => setTimeout(resolve, 60000));
        }
    }
    
    console.log('\n⏰ 10 minutes elapsed - Railway may need manual intervention');
    console.log('❌ Automatic deployment unsuccessful');
    console.log('\n🛠️ Manual steps needed:');
    console.log('1. Check Railway dashboard service settings');
    console.log('2. Verify start command is: python main.py');
    console.log('3. Check if railway.toml is being recognized');
    console.log('4. Look at Railway build/deploy logs');
    
    await browser.close();
}

monitorForceDeploy().catch(console.error);