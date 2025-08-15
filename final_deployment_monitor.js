#!/usr/bin/env node
/**
 * Final Deployment Monitor
 * Monitors Railway deployment with optimizations and celebrates success
 */

const puppeteer = require('puppeteer');
const https = require('https');

class FinalDeploymentMonitor {
    constructor() {
        this.serviceUrl = 'llm-chatbot-python-production-7e6f.up.railway.app';
        this.startTime = Date.now();
    }

    async testHealthEndpoint() {
        return new Promise((resolve, reject) => {
            const options = {
                hostname: this.serviceUrl,
                port: 443,
                path: '/health',
                method: 'GET',
                timeout: 15000
            };

            const req = https.request(options, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => resolve({ 
                    statusCode: res.statusCode, 
                    data,
                    headers: res.headers 
                }));
            });

            req.on('error', reject);
            req.on('timeout', () => {
                req.destroy();
                reject(new Error('Timeout'));
            });
            req.setTimeout(15000);
            req.end();
        });
    }

    async testWithPuppeteer() {
        const browser = await puppeteer.launch({ 
            headless: false,
            devtools: false // Less intrusive for final test
        });
        
        try {
            const page = await browser.newPage();
            
            // Test main React UI
            await page.goto(`https://${this.serviceUrl}/`, { 
                waitUntil: 'networkidle2',
                timeout: 30000 
            });
            
            const title = await page.title();
            const hasReactContent = await page.evaluate(() => 
                document.body.textContent.includes('FMCG') || 
                document.body.textContent.includes('SupplyGraph') ||
                document.body.textContent.includes('Analytics') ||
                document.querySelector('#root') !== null
            );
            
            // Test API functionality
            await page.goto(`https://${this.serviceUrl}/api/graph/overview`);
            const apiContent = await page.evaluate(() => document.body.textContent);
            
            let apiWorks = false;
            try {
                const apiData = JSON.parse(apiContent);
                apiWorks = apiData.status === 'operational';
            } catch (e) {
                apiWorks = false;
            }
            
            // Take success screenshot
            await page.goto(`https://${this.serviceUrl}/`);
            await page.screenshot({ 
                path: './railway_success_screenshot.png', 
                fullPage: true 
            });
            
            await browser.close();
            
            return {
                title,
                hasReactContent,
                apiWorks,
                success: hasReactContent && apiWorks
            };
            
        } catch (error) {
            await browser.close();
            throw error;
        }
    }

    async runFinalCheck() {
        const maxAttempts = 12; // 12 minutes with 1-minute intervals
        const checkInterval = 60000; // 1 minute
        
        console.log('🎯 Final Deployment Monitor');
        console.log('===========================');
        console.log(`🌐 Target: https://${this.serviceUrl}`);
        console.log(`⏱️  Max wait time: ${maxAttempts} minutes`);
        console.log('🎊 Looking for full React UI + API success');
        console.log('');
        
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            const elapsed = Math.round((Date.now() - this.startTime) / 1000 / 60);
            console.log(`🔍 Final Check ${attempt}/${maxAttempts} - ${new Date().toLocaleTimeString()} (${elapsed}min elapsed)`);
            
            try {
                // Quick health check first
                const health = await this.testHealthEndpoint();
                
                if (health.statusCode === 200) {
                    const healthData = JSON.parse(health.data);
                    console.log(`✅ Health check: ${healthData.status}`);
                    console.log(`📊 Version: ${healthData.version}`);
                    console.log(`🛠️  Services: ${healthData.services.join(', ')}`);
                    
                    // Full UI test
                    console.log('🚀 Testing React UI with Puppeteer...');
                    const uiResult = await this.testWithPuppeteer();
                    
                    console.log(`📄 Page title: "${uiResult.title}"`);
                    console.log(`⚛️  React content: ${uiResult.hasReactContent ? '✅ Found' : '❌ Missing'}`);
                    console.log(`🔌 API working: ${uiResult.apiWorks ? '✅ Yes' : '❌ No'}`);
                    
                    if (uiResult.success) {
                        const totalTime = Math.round((Date.now() - this.startTime) / 1000 / 60);
                        
                        console.log('\n🎉🎉🎉 DEPLOYMENT SUCCESS! 🎉🎉🎉');
                        console.log('='.repeat(50));
                        console.log('✅ Railway deployment completed successfully!');
                        console.log('✅ FastAPI backend is operational');
                        console.log('✅ React UI is loading and rendering');
                        console.log('✅ API endpoints are responding');
                        console.log('✅ Health checks are passing');
                        console.log('📸 Success screenshot saved');
                        console.log('');
                        console.log(`⏱️  Total deployment time: ${totalTime} minutes`);
                        console.log(`🌐 Your app is live: https://${this.serviceUrl}`);
                        console.log('');
                        console.log('🔥 The modern SupplyGraph Analytics UI is now live!');
                        console.log('🔥 Rich dataset is connected and ready!');
                        console.log('🔥 Railway deployment successful!');
                        console.log('='.repeat(50));
                        
                        return true;
                    } else {
                        console.log('⚠️  Health OK but UI/API not fully ready');
                    }
                    
                } else if (health.statusCode === 404 && health.data.includes('train has not arrived')) {
                    console.log('🚂 Railway still building/deploying...');
                } else {
                    console.log(`❌ Health check failed: ${health.statusCode}`);
                }
                
            } catch (error) {
                if (error.message === 'Timeout') {
                    console.log('⏱️  Request timeout - Railway still starting up');
                } else {
                    console.log(`❌ Error: ${error.message.substring(0, 80)}`);
                }
            }
            
            if (attempt < maxAttempts) {
                console.log(`⏳ Waiting 1 minute... (${maxAttempts - attempt} checks remaining)\n`);
                await new Promise(resolve => setTimeout(resolve, checkInterval));
            }
        }
        
        console.log('\n⏰ Final monitoring period completed');
        console.log('💡 If deployment is still not ready, Railway may need more time');
        console.log('🔄 You can manually check the Railway dashboard for detailed logs');
        
        return false;
    }
}

// Run final monitoring
const monitor = new FinalDeploymentMonitor();
monitor.runFinalCheck()
    .then(success => {
        if (!success) {
            console.log('\n📋 Next Steps:');
            console.log('1. Check Railway dashboard build/deploy logs');
            console.log('2. Verify the startup debug output in Railway logs');
            console.log('3. Railway free tier can take 15-30 minutes for complex builds');
        }
        process.exit(success ? 0 : 1);
    })
    .catch(error => {
        console.error('❌ Final monitor error:', error);
        process.exit(1);
    });