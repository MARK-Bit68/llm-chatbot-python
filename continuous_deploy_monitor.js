#!/usr/bin/env node
/**
 * Continuous Railway Deployment Monitor
 * Keeps checking until modern UI is fully deployed
 */

const puppeteer = require('puppeteer');
const { spawn } = require('child_process');
const fs = require('fs');

class DeploymentMonitor {
    constructor() {
        this.url = 'https://llm-chatbot-python-production-d789.up.railway.app';
        this.maxAttempts = 20; // 20 minutes max
        this.interval = 60000; // 1 minute
        this.browser = null;
        this.success = false;
    }

    async init() {
        console.log('🚀 Starting Continuous Railway Deployment Monitor');
        console.log(`⏱️ Checking every minute, max ${this.maxAttempts} attempts`);
        console.log(`🌐 Monitoring: ${this.url}`);
        console.log('==========================================\n');

        this.browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
    }

    async checkDeployment(attempt) {
        console.log(`🔍 Attempt ${attempt}/${this.maxAttempts} - ${new Date().toLocaleTimeString()}`);
        
        const page = await this.browser.newPage();
        
        try {
            // Set timeout for page load
            page.setDefaultTimeout(30000);
            
            const response = await page.goto(this.url, { 
                waitUntil: 'networkidle0', 
                timeout: 30000 
            });

            const statusCode = response.status();
            console.log(`   📡 HTTP Status: ${statusCode}`);

            if (statusCode !== 200) {
                console.log(`   ⚠️ Non-200 response - Railway may be deploying`);
                await page.close();
                return false;
            }

            // Get page title and content
            const title = await page.title();
            const bodyText = await page.evaluate(() => document.body.innerText);
            
            console.log(`   📄 Title: ${title}`);

            // Check if it's the new React app
            const isModernUI = await page.evaluate(() => {
                const content = document.body.textContent || document.body.innerText;
                return content.includes('SupplyGraph') ||
                       content.includes('Product Explorer') ||
                       content.includes('Advanced Dashboard') ||
                       content.includes('Modern Analytics') ||
                       document.querySelector('[data-testid="app"], .min-h-screen, #root') !== null;
            });

            // Check if it's still Streamlit
            const isStreamlit = await page.evaluate(() => {
                const content = document.body.textContent || document.body.innerText;
                return content.includes('FMCG Supply Chain Assistant') &&
                       (content.includes('UI theme') || content.includes('Enable monitoring'));
            });

            if (isModernUI) {
                console.log('   🎉 SUCCESS: Modern React UI detected!');
                
                // Test health endpoint
                try {
                    await page.goto(`${this.url}/health`, { waitUntil: 'networkidle0' });
                    const healthContent = await page.evaluate(() => document.body.textContent);
                    
                    if (healthContent.includes('healthy')) {
                        console.log('   💚 Health check: PASSED');
                    } else {
                        console.log('   ⚠️ Health check: Unexpected response');
                    }
                } catch (healthError) {
                    console.log('   ⚠️ Health check: Failed to load');
                }

                // Test API endpoint
                try {
                    await page.goto(`${this.url}/api/health`, { waitUntil: 'networkidle0' });
                    console.log('   🔌 API endpoint: Accessible');
                } catch (apiError) {
                    console.log('   ⚠️ API endpoint: Not accessible');
                }

                // Take success screenshot
                await page.goto(this.url, { waitUntil: 'networkidle0' });
                await page.screenshot({ 
                    path: `./success_deployment_${Date.now()}.png`, 
                    fullPage: true 
                });
                console.log('   📸 Success screenshot saved');

                await page.close();
                return true;

            } else if (isStreamlit) {
                console.log('   🔄 Still showing Streamlit - Railway hasn\'t deployed new version yet');
                console.log('   📊 Page content preview:', bodyText.substring(0, 150) + '...');
                
                // Check if we need to force a redeploy
                if (attempt > 10) {
                    console.log('   🔧 Deployment taking too long - considering force redeploy');
                }

            } else {
                console.log('   ❓ Unknown content detected');
                console.log('   📊 Content preview:', bodyText.substring(0, 200) + '...');
                
                // Take debug screenshot
                await page.screenshot({ 
                    path: `./debug_deployment_${attempt}.png`, 
                    fullPage: true 
                });
                console.log('   📸 Debug screenshot saved');
            }

            await page.close();
            return false;

        } catch (error) {
            console.log(`   ❌ Error: ${error.message}`);
            
            // Take error screenshot
            try {
                await page.screenshot({ 
                    path: `./error_deployment_${attempt}.png`, 
                    fullPage: true 
                });
                console.log('   📸 Error screenshot saved');
            } catch (screenshotError) {
                console.log('   📸 Could not take screenshot');
            }
            
            await page.close();
            return false;
        }
    }

    async forceRedeploy() {
        console.log('\n🔧 FORCING REDEPLOY...');
        console.log('   Making small change to trigger Railway redeploy');
        
        // Update a timestamp in troubleshoot.py to force redeploy
        const timestamp = new Date().toISOString();
        const forceDeployContent = `# Force redeploy - ${timestamp}\n# This file triggers Railway to redeploy\nprint("Force redeploy triggered at ${timestamp}")`;
        
        fs.writeFileSync('./force_redeploy.py', forceDeployContent);
        
        // Git commit and push
        return new Promise((resolve) => {
            const gitAdd = spawn('git', ['add', '.'], { stdio: 'pipe' });
            gitAdd.on('close', () => {
                const gitCommit = spawn('git', ['commit', '-m', `🔧 Force redeploy - ${timestamp}`], { stdio: 'pipe' });
                gitCommit.on('close', () => {
                    const gitPush = spawn('git', ['push', 'origin', 'poc1'], { stdio: 'pipe' });
                    gitPush.on('close', (code) => {
                        if (code === 0) {
                            console.log('   ✅ Force redeploy triggered');
                            console.log('   ⏱️ Waiting 2 minutes for Railway to detect changes...\n');
                        } else {
                            console.log('   ⚠️ Git push failed');
                        }
                        resolve();
                    });
                });
            });
        });
    }

    async run() {
        await this.init();
        
        for (let attempt = 1; attempt <= this.maxAttempts; attempt++) {
            const success = await this.checkDeployment(attempt);
            
            if (success) {
                console.log('\n🎉 DEPLOYMENT SUCCESSFUL!');
                console.log(`✅ Modern React UI with SupplyGraph is now live at: ${this.url}`);
                this.success = true;
                break;
            }

            // Force redeploy if taking too long
            if (attempt === 8 && !this.success) {
                await this.forceRedeploy();
                // Add 2 minutes wait after force deploy
                console.log('   ⏱️ Waiting 2 minutes after force redeploy...');
                await new Promise(resolve => setTimeout(resolve, 120000));
                continue;
            }

            if (attempt < this.maxAttempts) {
                console.log(`   ⏳ Waiting 1 minute before next check...\n`);
                await new Promise(resolve => setTimeout(resolve, this.interval));
            }
        }

        if (!this.success) {
            console.log('\n⏰ TIMEOUT: Maximum attempts reached');
            console.log('❌ Modern UI deployment not successful after 20 minutes');
            console.log('\n🔍 Manual troubleshooting needed:');
            console.log('   1. Check Railway dashboard for build errors');
            console.log('   2. Verify main.py is being used as start command');
            console.log('   3. Check if React build completed successfully');
            console.log('   4. Review Railway deployment logs');
        }

        await this.browser.close();
        process.exit(this.success ? 0 : 1);
    }
}

// Handle interruption gracefully
process.on('SIGINT', async () => {
    console.log('\n🛑 Monitoring interrupted by user');
    process.exit(0);
});

// Start monitoring
const monitor = new DeploymentMonitor();
monitor.run().catch(console.error);