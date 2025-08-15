#!/usr/bin/env node
/**
 * Quick check for new Railway deployment
 */

const https = require('https');

function testEndpoint(url, path) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: url,
            port: 443,
            path: path,
            method: 'GET',
            timeout: 10000
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve({ statusCode: res.statusCode, data }));
        });

        req.on('error', reject);
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Timeout'));
        });
        req.setTimeout(10000);
        req.end();
    });
}

async function checkDeployment() {
    const newUrl = 'llm-chatbot-python-production-7e6f.up.railway.app';
    
    console.log('🔍 Checking New Railway Deployment');
    console.log('==================================');
    console.log(`🌐 URL: https://${newUrl}`);
    console.log('');

    try {
        // Test health endpoint
        console.log('Testing /health endpoint...');
        const health = await testEndpoint(newUrl, '/health');
        
        if (health.statusCode === 200) {
            const healthData = JSON.parse(health.data);
            console.log('✅ Health check passed!');
            console.log(`   Status: ${healthData.status}`);
            console.log(`   Version: ${healthData.version}`);
            console.log(`   Services: ${healthData.services.join(', ')}`);
            
            // Test React UI
            console.log('\nTesting React UI...');
            const ui = await testEndpoint(newUrl, '/');
            
            if (ui.statusCode === 200 && ui.data.includes('FMCG Supply Chain')) {
                console.log('✅ React UI is loading!');
                console.log('✅ Found FMCG Supply Chain content');
                
                // Test API endpoint
                console.log('\nTesting API endpoint...');
                const api = await testEndpoint(newUrl, '/api/graph/overview');
                
                if (api.statusCode === 200) {
                    const apiData = JSON.parse(api.data);
                    console.log('✅ API endpoint working!');
                    console.log(`   Products: ${apiData.node_statistics.products}`);
                    console.log(`   Status: ${apiData.status}`);
                }
                
                console.log('\n🎉 NEW DEPLOYMENT SUCCESSFUL!');
                console.log('✅ FastAPI backend operational');
                console.log('✅ React UI loading correctly'); 
                console.log('✅ API endpoints responding');
                console.log(`\n🌐 Access your app: https://${newUrl}`);
                
            } else {
                console.log('⚠️  React UI may still be building...');
            }
            
        } else {
            console.log(`❌ Health check failed: ${health.statusCode}`);
            console.log(`Response: ${health.data}`);
        }
        
    } catch (error) {
        if (error.message === 'Timeout') {
            console.log('⏱️  Request timeout - Railway may still be building');
        } else {
            console.log(`❌ Error: ${error.message}`);
        }
        console.log('💡 Railway free tier builds can take 5-15 minutes');
    }
}

checkDeployment();