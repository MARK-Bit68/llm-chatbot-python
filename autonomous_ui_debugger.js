#!/usr/bin/env node
/**
 * Autonomous UI Debugger using Puppeteer
 * Tests deployment and automatically fixes issues
 */

const puppeteer = require('puppeteer');
const fs = require('fs');

class AutonomousUIDebugger {
    constructor() {
        this.serviceUrl = 'llm-chatbot-python-production-7e6f.up.railway.app';
        this.browser = null;
        this.issues = [];
        this.fixes = [];
    }

    async launchBrowser() {
        console.log('🚀 Launching browser for debugging...');
        this.browser = await puppeteer.launch({ 
            headless: false,
            devtools: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
    }

    async testHealthEndpoint() {
        console.log('🏥 Testing health endpoint...');
        
        const page = await this.browser.newPage();
        
        try {
            await page.goto(`https://${this.serviceUrl}/health`, { 
                waitUntil: 'networkidle2',
                timeout: 30000 
            });
            
            const content = await page.evaluate(() => document.body.textContent);
            console.log(`📊 Health response: ${content}`);
            
            try {
                const healthData = JSON.parse(content);
                if (healthData.status === 'healthy') {
                    console.log('✅ Health endpoint working!');
                    console.log(`📋 Version: ${healthData.version}`);
                    console.log(`🛠️  Services: ${healthData.services.join(', ')}`);
                    return true;
                } else {
                    this.issues.push('Health endpoint returned non-healthy status');
                    return false;
                }
            } catch (parseError) {
                this.issues.push('Health endpoint returned invalid JSON');
                console.log('❌ Invalid JSON response from health endpoint');
                return false;
            }
            
        } catch (error) {
            if (error.message.includes('404')) {
                this.issues.push('Service not found - likely still deploying');
                console.log('❌ 404 - Service not found (still deploying?)');
            } else if (error.message.includes('502')) {
                this.issues.push('502 Bad Gateway - application not responding');
                console.log('❌ 502 - Application not responding');
            } else {
                this.issues.push(`Health check failed: ${error.message}`);
                console.log(`❌ Health check error: ${error.message}`);
            }
            return false;
        } finally {
            await page.close();
        }
    }

    async testReactUI() {
        console.log('⚛️  Testing React UI...');
        
        const page = await this.browser.newPage();
        
        // Monitor console logs and errors
        page.on('console', msg => {
            console.log(`🔍 Console: ${msg.text()}`);
        });
        
        page.on('pageerror', error => {
            console.log(`❌ Page Error: ${error.message}`);
            this.issues.push(`React error: ${error.message}`);
        });
        
        page.on('response', response => {
            if (response.status() >= 400) {
                console.log(`🔴 HTTP Error: ${response.status()} ${response.url()}`);
                this.issues.push(`HTTP ${response.status()}: ${response.url()}`);
            }
        });
        
        try {
            await page.goto(`https://${this.serviceUrl}/`, { 
                waitUntil: 'networkidle2',
                timeout: 30000 
            });
            
            // Take screenshot for manual inspection
            await page.screenshot({ 
                path: './current_ui_state.png', 
                fullPage: true 
            });
            console.log('📸 Screenshot saved: current_ui_state.png');
            
            // Analyze page content
            const title = await page.title();
            const hasReactRoot = await page.$('#root') !== null;
            const bodyText = await page.evaluate(() => document.body.textContent);
            
            console.log(`📄 Page title: "${title}"`);
            console.log(`🏗️  React root element: ${hasReactRoot ? 'Found' : 'Missing'}`);
            
            // Check for specific content
            const hasSupplyChainContent = bodyText.includes('FMCG') || 
                                        bodyText.includes('SupplyGraph') || 
                                        bodyText.includes('Analytics') ||
                                        bodyText.includes('Supply Chain');
            
            const hasErrorContent = bodyText.includes('404') || 
                                   bodyText.includes('502') || 
                                   bodyText.includes('Application failed');
            
            console.log(`📊 Supply chain content: ${hasSupplyChainContent ? 'Found' : 'Missing'}`);
            console.log(`❌ Error content: ${hasErrorContent ? 'Found' : 'None'}`);
            
            if (hasErrorContent) {
                this.issues.push('Page showing error content');
                console.log(`🔍 Error details: ${bodyText.substring(0, 200)}...`);
            }
            
            if (!hasSupplyChainContent && !hasErrorContent) {
                // Check if it's serving something else
                console.log(`🔍 Unexpected content: ${bodyText.substring(0, 300)}...`);
                this.issues.push('Page not showing expected React content');
            }
            
            // Test API endpoints if UI is loading
            if (hasSupplyChainContent) {
                await this.testAPIEndpoints(page);
            }
            
            return hasSupplyChainContent && !hasErrorContent;
            
        } catch (error) {
            this.issues.push(`React UI test failed: ${error.message}`);
            console.log(`❌ React UI test error: ${error.message}`);
            return false;
        } finally {
            await page.close();
        }
    }

    async testAPIEndpoints(page) {
        console.log('🔌 Testing API endpoints...');
        
        try {
            // Test graph overview endpoint
            await page.goto(`https://${this.serviceUrl}/api/graph/overview`, {
                timeout: 15000
            });
            
            const apiContent = await page.evaluate(() => document.body.textContent);
            
            try {
                const apiData = JSON.parse(apiContent);
                console.log('✅ API endpoint working!');
                console.log(`📊 Products: ${apiData.node_statistics?.products || 'N/A'}`);
                console.log(`📈 Status: ${apiData.status || 'N/A'}`);
            } catch (parseError) {
                console.log('❌ API returned invalid JSON');
                this.issues.push('API endpoint returning invalid JSON');
            }
            
        } catch (error) {
            console.log(`❌ API test failed: ${error.message}`);
            this.issues.push(`API test failed: ${error.message}`);
        }
    }

    async identifyIssues() {
        console.log('\n🔍 Analyzing Issues...');
        console.log('='.repeat(30));
        
        if (this.issues.length === 0) {
            console.log('✅ No issues detected!');
            return;
        }
        
        this.issues.forEach((issue, index) => {
            console.log(`${index + 1}. ${issue}`);
        });
        
        // Analyze common patterns
        const hasDeploymentIssues = this.issues.some(issue => 
            issue.includes('404') || 
            issue.includes('not found') || 
            issue.includes('still deploying')
        );
        
        const hasApplicationIssues = this.issues.some(issue =>
            issue.includes('502') ||
            issue.includes('not responding') ||
            issue.includes('health')
        );
        
        const hasReactIssues = this.issues.some(issue =>
            issue.includes('React') ||
            issue.includes('content') ||
            issue.includes('root')
        );
        
        console.log('\n💡 Issue Analysis:');
        if (hasDeploymentIssues) {
            console.log('🏗️  Deployment still in progress - need to wait longer');
            this.fixes.push('Wait for Railway deployment to complete (10-20 minutes on free tier)');
        }
        
        if (hasApplicationIssues) {
            console.log('🐛 Application startup issues - check main.py and requirements');
            this.fixes.push('Review FastAPI startup and dependencies');
        }
        
        if (hasReactIssues) {
            console.log('⚛️  React UI issues - check build and static file serving');
            this.fixes.push('Check React build output and static file configuration');
        }
    }

    async runFullDiagnostic() {
        console.log('🔧 Starting Autonomous UI Diagnostic');
        console.log('===================================');
        console.log(`🌐 Target: https://${this.serviceUrl}`);
        console.log('');
        
        await this.launchBrowser();
        
        try {
            // Test health endpoint
            const healthOk = await this.testHealthEndpoint();
            
            // Test React UI regardless of health status
            const uiOk = await this.testReactUI();
            
            // Analyze issues and suggest fixes
            await this.identifyIssues();
            
            console.log('\n📋 Summary:');
            console.log('='.repeat(20));
            console.log(`🏥 Health endpoint: ${healthOk ? '✅ Working' : '❌ Failed'}`);
            console.log(`⚛️  React UI: ${uiOk ? '✅ Working' : '❌ Failed'}`);
            
            if (this.fixes.length > 0) {
                console.log('\n🛠️  Suggested Fixes:');
                this.fixes.forEach((fix, index) => {
                    console.log(`${index + 1}. ${fix}`);
                });
            }
            
            if (healthOk && uiOk) {
                console.log('\n🎉 DEPLOYMENT SUCCESSFUL!');
                console.log(`🌐 Your app is live: https://${this.serviceUrl}`);
                return true;
            } else {
                console.log('\n⏳ Deployment needs more time or has issues');
                return false;
            }
            
        } finally {
            if (this.browser) {
                await this.browser.close();
            }
        }
    }
}

// Auto-retry logic
async function runWithRetries() {
    const maxRetries = 5;
    const retryDelay = 120000; // 2 minutes
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        console.log(`\n🔄 Diagnostic Attempt ${attempt}/${maxRetries}`);
        console.log('='.repeat(50));
        
        const uiDebugger = new AutonomousUIDebugger();
        const success = await uiDebugger.runFullDiagnostic();
        
        if (success) {
            console.log('\n✅ Deployment verified successfully!');
            break;
        } else if (attempt < maxRetries) {
            console.log(`\n⏳ Waiting ${retryDelay/1000} seconds before retry...`);
            await new Promise(resolve => setTimeout(resolve, retryDelay));
        } else {
            console.log('\n❌ Max retries reached. Manual intervention may be needed.');
        }
    }
}

runWithRetries().catch(console.error);