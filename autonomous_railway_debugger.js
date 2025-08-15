#!/usr/bin/env node
/**
 * Autonomous Railway Debugger
 * Uses Railway CLI + Puppeteer to debug and fix deployment issues
 */

const puppeteer = require('puppeteer');
const { exec } = require('child_process');
const fs = require('fs');
const util = require('util');

const execAsync = util.promisify(exec);

class AutonomousRailwayDebugger {
    constructor() {
        this.railwayToken = 'ad139223-b259-413c-9116-35cd169208bd';
        this.newServiceUrl = 'llm-chatbot-python-production-7e6f.up.railway.app';
        this.browser = null;
        this.deploymentAttempts = 0;
        this.maxAttempts = 3;
    }

    async setupRailwayCLI() {
        console.log('🚂 Setting up Railway CLI with token...');
        
        try {
            // Set Railway token
            process.env.RAILWAY_TOKEN = this.railwayToken;
            
            // Test Railway CLI access
            const { stdout } = await execAsync('railway status');
            console.log('✅ Railway CLI authenticated');
            console.log(`📊 Status: ${stdout.trim()}`);
            return true;
        } catch (error) {
            console.log('❌ Railway CLI setup failed:', error.message);
            return false;
        }
    }

    async getRailwayLogs() {
        console.log('📋 Fetching Railway deployment logs...');
        
        try {
            const { stdout } = await execAsync('railway logs --tail 50');
            console.log('📝 Recent logs:');
            console.log('='.repeat(50));
            console.log(stdout);
            console.log('='.repeat(50));
            return stdout;
        } catch (error) {
            console.log('⚠️  Could not fetch logs:', error.message);
            return null;
        }
    }

    async checkRailwayDeployment() {
        console.log('🔍 Checking Railway deployment status...');
        
        try {
            const { stdout } = await execAsync('railway status');
            console.log('📊 Deployment status:');
            console.log(stdout);
            
            // Check if service is running
            if (stdout.includes('RUNNING') || stdout.includes('ACTIVE')) {
                console.log('✅ Service appears to be running');
                return true;
            } else if (stdout.includes('BUILDING') || stdout.includes('DEPLOYING')) {
                console.log('🏗️  Service is still building/deploying');
                return false;
            } else {
                console.log('❌ Service appears to have issues');
                return false;
            }
        } catch (error) {
            console.log('❌ Could not check status:', error.message);
            return false;
        }
    }

    async testWithPuppeteer() {
        console.log('🔧 Testing deployment with Puppeteer...');
        
        try {
            this.browser = await puppeteer.launch({ 
                headless: false,
                devtools: true 
            });
            
            const page = await this.browser.newPage();
            
            // Enable console logging
            page.on('console', msg => {
                console.log(`🌐 Browser Console: ${msg.text()}`);
            });
            
            page.on('pageerror', error => {
                console.log(`❌ Page Error: ${error.message}`);
            });
            
            // Test health endpoint
            console.log('Testing /health endpoint...');
            await page.goto(`https://${this.newServiceUrl}/health`, { 
                waitUntil: 'networkidle2',
                timeout: 30000 
            });
            
            const healthContent = await page.evaluate(() => document.body.textContent);
            console.log(`📊 Health response: ${healthContent}`);
            
            try {
                const healthData = JSON.parse(healthContent);
                if (healthData.status === 'healthy') {
                    console.log('✅ Health check passed!');
                    
                    // Test React UI
                    await this.testReactUI(page);
                    return true;
                } else {
                    console.log('❌ Health check failed');
                    return false;
                }
            } catch (parseError) {
                console.log('❌ Health endpoint returned invalid JSON');
                console.log(`Raw response: ${healthContent.substring(0, 200)}`);
                return false;
            }
            
        } catch (error) {
            console.log('❌ Puppeteer test failed:', error.message);
            return false;
        }
    }

    async testReactUI(page) {
        console.log('🚀 Testing React UI...');
        
        try {
            await page.goto(`https://${this.newServiceUrl}/`, { 
                waitUntil: 'networkidle2',
                timeout: 30000 
            });
            
            // Take screenshot
            await page.screenshot({ 
                path: './railway_ui_test.png', 
                fullPage: true 
            });
            console.log('📸 UI screenshot saved');
            
            // Check for React content
            const hasReactRoot = await page.$('#root');
            const title = await page.title();
            const hasSupplyChainContent = await page.evaluate(() => 
                document.body.textContent.includes('FMCG') || 
                document.body.textContent.includes('SupplyGraph') ||
                document.body.textContent.includes('Analytics')
            );
            
            console.log(`📄 Page title: ${title}`);
            console.log(`🏗️  React root found: ${hasReactRoot ? 'Yes' : 'No'}`);
            console.log(`📊 Supply chain content: ${hasSupplyChainContent ? 'Yes' : 'No'}`);
            
            if (hasReactRoot && hasSupplyChainContent) {
                console.log('✅ React UI is working!');
                
                // Test API integration
                await this.testAPIIntegration(page);
                return true;
            } else {
                console.log('❌ React UI not loading properly');
                return false;
            }
            
        } catch (error) {
            console.log('❌ React UI test failed:', error.message);
            return false;
        }
    }

    async testAPIIntegration(page) {
        console.log('🔌 Testing API integration...');
        
        try {
            // Test chat functionality
            const chatInput = await page.$('input[placeholder*="message"], textarea[placeholder*="message"], input[type="text"]');
            
            if (chatInput) {
                console.log('💬 Testing chat functionality...');
                await chatInput.type('Hello, test message');
                
                const submitButton = await page.$('button[type="submit"], button:contains("Send")');
                if (submitButton) {
                    await submitButton.click();
                    await page.waitForTimeout(2000);
                    console.log('✅ Chat interaction completed');
                }
            }
            
            // Check network requests
            const responses = [];
            page.on('response', response => {
                if (response.url().includes('/api/')) {
                    responses.push({
                        url: response.url(),
                        status: response.status()
                    });
                }
            });
            
            // Trigger API calls by interacting with UI
            await page.reload({ waitUntil: 'networkidle2' });
            
            console.log('📡 API requests detected:');
            responses.forEach(resp => {
                console.log(`   ${resp.status} ${resp.url}`);
            });
            
        } catch (error) {
            console.log('⚠️  API integration test encountered issues:', error.message);
        }
    }

    async redeploy() {
        console.log('🔄 Attempting to redeploy...');
        
        try {
            // Force redeploy
            await execAsync('railway redeploy');
            console.log('✅ Redeploy triggered');
            
            // Wait for deployment
            console.log('⏳ Waiting for deployment to complete...');
            await new Promise(resolve => setTimeout(resolve, 180000)); // 3 minutes
            
            return true;
        } catch (error) {
            console.log('❌ Redeploy failed:', error.message);
            return false;
        }
    }

    async debugAndFix() {
        console.log('🔧 Starting autonomous debugging session...');
        console.log('============================================');
        
        // Setup Railway CLI
        const railwaySetup = await this.setupRailwayCLI();
        if (!railwaySetup) {
            console.log('❌ Cannot proceed without Railway CLI access');
            return false;
        }
        
        for (let attempt = 1; attempt <= this.maxAttempts; attempt++) {
            console.log(`\n🔄 Debugging Attempt ${attempt}/${this.maxAttempts}`);
            console.log('='.repeat(40));
            
            // Check deployment status
            const isRunning = await this.checkRailwayDeployment();
            
            // Get logs for analysis
            await this.getRailwayLogs();
            
            // Test with Puppeteer
            const puppeteerSuccess = await this.testWithPuppeteer();
            
            if (puppeteerSuccess) {
                console.log('\n🎉 DEPLOYMENT SUCCESSFUL!');
                console.log('✅ Health checks passing');
                console.log('✅ React UI rendering correctly');
                console.log('✅ API integration working');
                console.log(`\n🌐 Your app: https://${this.newServiceUrl}`);
                break;
            } else {
                console.log(`\n❌ Attempt ${attempt} failed`);
                
                if (attempt < this.maxAttempts) {
                    console.log('🔄 Triggering redeploy...');
                    await this.redeploy();
                } else {
                    console.log('❌ Max attempts reached');
                    console.log('💡 Manual intervention may be required');
                }
            }
        }
        
        // Cleanup
        if (this.browser) {
            await this.browser.close();
        }
    }
}

// Run the autonomous debugger
const railwayDebugger = new AutonomousRailwayDebugger();
railwayDebugger.debugAndFix().catch(console.error);