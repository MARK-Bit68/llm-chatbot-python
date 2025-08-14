#!/usr/bin/env node
/**
 * Puppeteer UI Testing Script
 * Automated testing of the SupplyGraph Modern UI
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Test configuration
const CONFIG = {
    // Try both local and deployed URLs
    urls: [
        'http://localhost:8000',
        'https://llm-chatbot-python-production-d789.up.railway.app'
    ],
    headless: false, // Set to true for CI/CD
    timeout: 30000,
    screenshots: true,
    screenshotDir: './test_screenshots'
};

class UITester {
    constructor() {
        this.browser = null;
        this.page = null;
        this.testResults = [];
    }

    async init() {
        console.log('🚀 Starting Puppeteer UI Testing');
        
        // Create screenshots directory
        if (CONFIG.screenshots && !fs.existsSync(CONFIG.screenshotDir)) {
            fs.mkdirSync(CONFIG.screenshotDir, { recursive: true });
        }

        // Launch browser
        this.browser = await puppeteer.launch({
            headless: CONFIG.headless,
            defaultViewport: { width: 1920, height: 1080 },
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        this.page = await this.browser.newPage();
        
        // Set up request/response logging
        this.page.on('console', msg => {
            console.log(`🌐 Console: ${msg.text()}`);
        });

        this.page.on('requestfailed', request => {
            console.log(`❌ Request failed: ${request.url()} - ${request.failure().errorText}`);
        });
    }

    async takeScreenshot(name) {
        if (CONFIG.screenshots) {
            const filename = `${name}_${new Date().toISOString().replace(/[:.]/g, '-')}.png`;
            const filepath = path.join(CONFIG.screenshotDir, filename);
            await this.page.screenshot({ path: filepath, fullPage: true });
            console.log(`📸 Screenshot saved: ${filepath}`);
        }
    }

    async testURL(url) {
        console.log(`\n🔍 Testing URL: ${url}`);
        
        try {
            // Navigate to the URL
            const response = await this.page.goto(url, { 
                waitUntil: 'networkidle2', 
                timeout: CONFIG.timeout 
            });

            if (!response.ok()) {
                throw new Error(`HTTP ${response.status()}: ${response.statusText()}`);
            }

            console.log(`✅ Page loaded successfully (${response.status()})`);
            await this.takeScreenshot(`${url.replace(/[^a-zA-Z0-9]/g, '_')}_loaded`);

            // Test 1: Check if React app loaded
            await this.testReactAppLoaded();

            // Test 2: Check navigation
            await this.testNavigation();

            // Test 3: Check API endpoints
            await this.testAPIEndpoints(url);

            // Test 4: Test Product Explorer
            await this.testProductExplorer();

            // Test 5: Test Advanced Chat
            await this.testAdvancedChat();

            return true;

        } catch (error) {
            console.log(`❌ Failed to test ${url}: ${error.message}`);
            await this.takeScreenshot(`${url.replace(/[^a-zA-Z0-9]/g, '_')}_error`);
            return false;
        }
    }

    async testReactAppLoaded() {
        console.log('🔍 Testing if React app loaded...');
        
        try {
            // Wait for React app to mount
            await this.page.waitForSelector('[data-testid="app"], .min-h-screen, #root', { timeout: 5000 });
            
            // Check for React-specific elements
            const reactElements = await this.page.$$eval('*', elements => 
                elements.some(el => 
                    el.textContent && 
                    (el.textContent.includes('SupplyGraph') || 
                     el.textContent.includes('Product Explorer') ||
                     el.textContent.includes('Advanced Dashboard'))
                )
            );

            if (reactElements) {
                console.log('✅ React app loaded successfully');
                this.testResults.push({ test: 'React App Load', status: 'PASS' });
            } else {
                throw new Error('React app elements not found');
            }
            
        } catch (error) {
            console.log(`❌ React app test failed: ${error.message}`);
            this.testResults.push({ test: 'React App Load', status: 'FAIL', error: error.message });
        }
    }

    async testNavigation() {
        console.log('🔍 Testing navigation...');
        
        try {
            // Look for navigation elements
            const navExists = await this.page.$('nav, .sidebar, [role="navigation"]') !== null;
            
            if (navExists) {
                console.log('✅ Navigation elements found');
                
                // Try to click on navigation items
                const navLinks = await this.page.$$('a, button');
                console.log(`📋 Found ${navLinks.length} clickable elements`);
                
                this.testResults.push({ test: 'Navigation', status: 'PASS' });
            } else {
                throw new Error('Navigation elements not found');
            }
            
        } catch (error) {
            console.log(`❌ Navigation test failed: ${error.message}`);
            this.testResults.push({ test: 'Navigation', status: 'FAIL', error: error.message });
        }
    }

    async testAPIEndpoints(baseUrl) {
        console.log('🔍 Testing API endpoints...');
        
        const endpoints = ['/health', '/api/health', '/docs'];
        
        for (const endpoint of endpoints) {
            try {
                const url = `${baseUrl}${endpoint}`;
                const response = await this.page.goto(url, { waitUntil: 'networkidle2', timeout: 10000 });
                
                if (response.ok()) {
                    console.log(`✅ ${endpoint} - ${response.status()}`);
                    this.testResults.push({ test: `API ${endpoint}`, status: 'PASS' });
                } else {
                    console.log(`⚠️  ${endpoint} - ${response.status()}`);
                    this.testResults.push({ test: `API ${endpoint}`, status: 'WARN', status_code: response.status() });
                }
                
            } catch (error) {
                console.log(`❌ ${endpoint} failed: ${error.message}`);
                this.testResults.push({ test: `API ${endpoint}`, status: 'FAIL', error: error.message });
            }
        }
    }

    async testProductExplorer() {
        console.log('🔍 Testing Product Explorer...');
        
        try {
            // Go back to main page
            await this.page.goto(CONFIG.urls[CONFIG.urls.length - 1], { waitUntil: 'networkidle2' });
            
            // Look for Product Explorer link or page
            const productExplorerExists = await this.page.evaluate(() => {
                return document.body.textContent.includes('Product Explorer') ||
                       document.body.textContent.includes('Products') ||
                       document.querySelector('[href*="product"]') !== null;
            });

            if (productExplorerExists) {
                console.log('✅ Product Explorer elements found');
                this.testResults.push({ test: 'Product Explorer', status: 'PASS' });
            } else {
                throw new Error('Product Explorer not found');
            }
            
        } catch (error) {
            console.log(`❌ Product Explorer test failed: ${error.message}`);
            this.testResults.push({ test: 'Product Explorer', status: 'FAIL', error: error.message });
        }
    }

    async testAdvancedChat() {
        console.log('🔍 Testing Advanced Chat...');
        
        try {
            // Look for chat elements
            const chatExists = await this.page.evaluate(() => {
                return document.body.textContent.includes('Chat') ||
                       document.body.textContent.includes('AI Assistant') ||
                       document.querySelector('input[placeholder*="chat"], textarea[placeholder*="chat"]') !== null;
            });

            if (chatExists) {
                console.log('✅ Chat elements found');
                this.testResults.push({ test: 'Advanced Chat', status: 'PASS' });
            } else {
                console.log('⚠️  Chat elements not clearly visible');
                this.testResults.push({ test: 'Advanced Chat', status: 'WARN' });
            }
            
        } catch (error) {
            console.log(`❌ Advanced Chat test failed: ${error.message}`);
            this.testResults.push({ test: 'Advanced Chat', status: 'FAIL', error: error.message });
        }
    }

    async generateReport() {
        console.log('\n📊 Test Results Summary');
        console.log('========================');
        
        const passed = this.testResults.filter(r => r.status === 'PASS').length;
        const failed = this.testResults.filter(r => r.status === 'FAIL').length;
        const warnings = this.testResults.filter(r => r.status === 'WARN').length;
        
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`⚠️  Warnings: ${warnings}`);
        console.log(`📊 Total: ${this.testResults.length}`);
        
        console.log('\n📋 Detailed Results:');
        this.testResults.forEach(result => {
            const icon = result.status === 'PASS' ? '✅' : result.status === 'FAIL' ? '❌' : '⚠️';
            console.log(`${icon} ${result.test}: ${result.status}`);
            if (result.error) {
                console.log(`   Error: ${result.error}`);
            }
            if (result.status_code) {
                console.log(`   Status Code: ${result.status_code}`);
            }
        });

        // Save results to JSON
        const reportPath = path.join(CONFIG.screenshotDir, `test_report_${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
        fs.writeFileSync(reportPath, JSON.stringify({
            timestamp: new Date().toISOString(),
            summary: { passed, failed, warnings, total: this.testResults.length },
            results: this.testResults
        }, null, 2));
        
        console.log(`\n📄 Full report saved: ${reportPath}`);
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
        console.log('🧹 Cleanup completed');
    }

    async run() {
        try {
            await this.init();
            
            let successfulUrl = null;
            
            // Test each URL until one works
            for (const url of CONFIG.urls) {
                if (await this.testURL(url)) {
                    successfulUrl = url;
                    break;
                }
            }
            
            if (!successfulUrl) {
                console.log('❌ All URLs failed to load');
            } else {
                console.log(`✅ Successfully tested: ${successfulUrl}`);
            }
            
            await this.generateReport();
            
        } catch (error) {
            console.error('💥 Test runner error:', error);
        } finally {
            await this.cleanup();
        }
    }
}

// Run the tests
if (require.main === module) {
    const tester = new UITester();
    tester.run().catch(console.error);
}

module.exports = UITester;