#!/usr/bin/env node
/**
 * Railway Optimizer - Apply known Railway best practices
 */

const fs = require('fs');
const { exec } = require('child_process');
const util = require('util');

const execAsync = util.promisify(exec);

async function optimizeForRailway() {
    console.log('🚂 Railway Deployment Optimizer');
    console.log('===============================');
    console.log('🎯 Applying Railway best practices for health checks');
    console.log('');

    // 1. Use python3 directly instead of uvicorn command
    console.log('1. 🐍 Switching to python3 startup command...');
    const railwayToml = `[build]
builder = "nixpacks"

[deploy]
startCommand = "python3 main.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10`;
    
    fs.writeFileSync('./railway.toml', railwayToml);
    console.log('✅ Updated railway.toml to use python3 startup');

    // 2. Add explicit Python startup logging
    console.log('2. 📝 Adding detailed startup logging...');
    const currentMain = fs.readFileSync('./main.py', 'utf8');
    
    // Add startup debug info at the beginning of main
    const optimizedMain = currentMain.replace(
        'if __name__ == "__main__":',
        `if __name__ == "__main__":
    print("=" * 50)
    print("🚀 RAILWAY STARTUP DEBUG")
    print("=" * 50)
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"🐍 Python executable: {sys.executable}")
    print(f"🌐 PORT environment: {os.environ.get('PORT', 'NOT SET')}")
    print(f"📦 FastAPI available: {'✅' if 'fastapi' in str(__import__('fastapi')) else '❌'}")
    print(f"🦄 Uvicorn available: {'✅' if 'uvicorn' in str(__import__('uvicorn')) else '❌'}")
    print("=" * 50)`
    );
    
    // Add import for sys at the top
    const finalMain = optimizedMain.replace(
        'import os',
        `import os
import sys`
    );
    
    fs.writeFileSync('./main.py', finalMain);
    console.log('✅ Added startup debugging to main.py');

    // 3. Create a simple startup test script
    console.log('3. 🧪 Creating Railway startup test...');
    const startupTest = `#!/usr/bin/env python3
"""
Railway Startup Test - Verify environment before main app
"""
import os
import sys

print("🧪 Railway Startup Test")
print("=" * 30)

# Test 1: Python version
print(f"🐍 Python version: {sys.version}")

# Test 2: PORT environment
port = os.environ.get("PORT")
print(f"🌐 PORT env var: {port if port else 'NOT SET'}")

# Test 3: Import dependencies
try:
    import fastapi
    print("✅ FastAPI import: OK")
except ImportError as e:
    print(f"❌ FastAPI import: {e}")

try:
    import uvicorn
    print("✅ Uvicorn import: OK")
except ImportError as e:
    print(f"❌ Uvicorn import: {e}")

# Test 4: Create simple FastAPI app
try:
    from fastapi import FastAPI
    test_app = FastAPI()
    
    @test_app.get("/test")
    def test_endpoint():
        return {"status": "test_ok"}
    
    print("✅ FastAPI app creation: OK")
except Exception as e:
    print(f"❌ FastAPI app creation: {e}")

print("=" * 30)
print("🎯 Starting main application...")

# Import and run main app
if __name__ == "__main__":
    import main
`;
    
    fs.writeFileSync('./railway_test.py', startupTest);
    console.log('✅ Created railway_test.py');

    // 4. Commit and deploy optimizations
    console.log('4. 🚀 Deploying Railway optimizations...');
    
    try {
        await execAsync('git add railway.toml main.py railway_test.py');
        
        const commitMsg = `Railway deployment optimizations

- Switch to python3 startup command for better compatibility
- Add detailed startup logging for debugging
- Create Railway startup test script
- Apply Railway best practices for health check success

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>`;
        
        await execAsync(`git commit -m "${commitMsg}"`);
        await execAsync('git push origin poc1');
        
        console.log('✅ Railway optimizations deployed!');
        
        console.log('\n🎉 OPTIMIZATION COMPLETE!');
        console.log('📋 Applied Changes:');
        console.log('   1. ✅ Use python3 startup instead of uvicorn command');
        console.log('   2. ✅ Added detailed startup logging');
        console.log('   3. ✅ Created Railway environment test');
        console.log('   4. ✅ Applied Railway deployment best practices');
        console.log('');
        console.log('⏳ Railway will rebuild in ~3-5 minutes');
        console.log('🏥 Health check should now pass');
        console.log('🔍 Check Railway logs for detailed startup info');
        
    } catch (error) {
        console.log(`❌ Deployment error: ${error.message}`);
    }
}

optimizeForRailway().catch(console.error);