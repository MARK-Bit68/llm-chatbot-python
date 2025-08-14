# 🔧 Railway Environment Variables Setup

Your FastAPI backend + React frontend requires these environment variables to be set in Railway:

## 📋 **Required Environment Variables**

### **OpenAI Configuration**
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

### **Neo4j Database Configuration**
```bash
NEO4J_URI=neo4j+s://your-database.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-database-password
```

### **FastAPI Configuration**
```bash
PORT=$PORT
```

## 🚀 **How to Set Environment Variables in Railway**

### **Option 1: Railway Dashboard**
1. Go to your Railway project dashboard
2. Select your service
3. Go to "Variables" tab
4. Add each variable with its value

### **Option 2: Railway CLI**
```bash
# Set OpenAI variables
railway variables set OPENAI_API_KEY="sk-your-openai-api-key-here"
railway variables set OPENAI_MODEL="gpt-4o-mini"

# Set Neo4j variables
railway variables set NEO4J_URI="neo4j+s://your-database.neo4j.io:7687"
railway variables set NEO4J_USERNAME="neo4j"
railway variables set NEO4J_PASSWORD="your-database-password"

# Set FastAPI variables
railway variables set PORT="$PORT"
```

## 🔍 **Testing Environment Variables**

After setting the variables, you can test them by:

1. **Check Railway logs** for any missing variable errors
2. **Visit your app URL** to see if it loads properly
3. **Test the chat functionality** to verify OpenAI connection
4. **Check database connectivity** through the app

## ⚠️ **Common Issues**

### **Missing OPENAI_API_KEY**
- Error: "OPENAI_API_KEY not found!"
- Solution: Set the OpenAI API key in Railway variables

### **Missing Neo4j Variables**
- Error: Database connection failures
- Solution: Set all Neo4j connection variables

### **Port Configuration**
- Error: App not accessible
- Solution: Ensure `$PORT` is used (Railway sets this automatically)

## 📞 **Getting Your API Keys**

### **OpenAI API Key**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Go to "API Keys" section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### **Neo4j Database**
1. Go to [neo4j.com/cloud/platform/aura-graph-database](https://neo4j.com/cloud/platform/aura-graph-database)
2. Sign up for free tier
3. Create a new database
4. Copy the connection details

---

**After setting these variables, redeploy your app and it should work correctly! 🚀**
