# 🚀 Railway Deployment Guide - FMCG Supply Chain App

This guide will help you deploy your modern React UI + Streamlit backend to Railway.

## 📋 **Prerequisites**

1. **GitHub Account**: Your code should be in a GitHub repository
2. **Railway Account**: Sign up at [railway.app](https://railway.app)
3. **Railway CLI**: Install for easier deployment management
4. **OpenAI API Key**: For the AI chatbot functionality
5. **Neo4j Database**: External database for supply chain data

## 🏗️ **Architecture Overview**

Your app consists of two main components:

### **Frontend (React)**
- Modern React 18 application with Vite
- Professional UI with dark theme
- 5 main pages: Dashboard, Chat, Analytics, SKU Explorer, Settings
- Connects to backend via API

### **Backend (Streamlit)**
- Streamlit application with AI chatbot
- Neo4j database integration
- Supply chain analytics and insights
- API endpoints for frontend consumption

## 🚀 **Deployment Strategy**

### **Option 1: Automated Deployment (Recommended)**

Use the provided deployment script:

```bash
# Make the script executable
chmod +x deploy-railway.sh

# Run the deployment
./deploy-railway.sh
```

### **Option 2: Manual Deployment**

#### **Step 1: Deploy Backend Service**

1. **Create new Railway service** for backend
2. **Connect to GitHub** repository
3. **Set root directory** to `/` (root of repository)
4. **Use configuration**: `railway-backend.toml`
5. **Set environment variables**:
   ```
   OPENAI_API_KEY=your_openai_key
   NEO4J_URI=your_neo4j_connection_string
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   ```

#### **Step 2: Deploy Frontend Service**

1. **Create new Railway service** for frontend
2. **Connect to GitHub** repository
3. **Set root directory** to `/` (root of repository)
4. **Use configuration**: `railway-ui.toml`
5. **Set environment variables**:
   ```
   VITE_API_URL=https://your-backend-service.railway.app
   NODE_ENV=production
   VITE_APP_NAME=FMCG Supply Chain Assistant
   ```

## 📁 **Configuration Files**

### **railway-backend.toml** (Streamlit Backend)
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "streamlit run bot_supplygraph.py --server.port=$PORT --server.address=0.0.0.0"
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10
```

### **railway-ui.toml** (React Frontend)
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "npm run build && npm run preview -- --host 0.0.0.0 --port $PORT"
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10
```

## 🔧 **Environment Variables**

### **Backend Service Variables**
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# Neo4j Database
NEO4J_URI=neo4j+s://your-database.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-database-password

# Streamlit Configuration
STREAMLIT_SERVER_PORT=$PORT
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### **Frontend Service Variables**
```bash
# API Configuration
VITE_API_URL=https://your-backend-service.railway.app

# App Configuration
NODE_ENV=production
VITE_APP_NAME=FMCG Supply Chain Assistant
```

## 🧪 **Testing Your Deployment**

### **Backend Testing**
1. Visit your backend URL
2. Should see Streamlit interface
3. Test chat functionality
4. Verify database connections

### **Frontend Testing**
1. Visit your frontend URL
2. Should see modern React UI
3. Test navigation between pages
4. Verify API connectivity

### **Integration Testing**
1. Test chat from React frontend
2. Verify data flows between services
3. Check all pages load correctly
4. Test responsive design

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Build Failures**
- Check `requirements.txt` for missing dependencies
- Verify Node.js version compatibility
- Check for syntax errors in code

#### **Connection Issues**
- Verify environment variables are set correctly
- Check CORS configuration
- Ensure services can communicate

#### **Database Issues**
- Verify Neo4j connection string
- Check database credentials
- Ensure database is accessible from Railway

### **Debugging Commands**
```bash
# Check Railway logs
railway logs --service backend
railway logs --service frontend

# Check service status
railway status

# View environment variables
railway variables --service backend
railway variables --service frontend
```

## 📊 **Monitoring & Maintenance**

### **Health Checks**
- Backend: `https://your-backend.railway.app/`
- Frontend: `https://your-frontend.railway.app/`

### **Performance Monitoring**
- Monitor Railway dashboard for resource usage
- Check response times and error rates
- Monitor database connection health

### **Updates & Maintenance**
- Update dependencies regularly
- Monitor for security patches
- Backup database regularly

## 🎯 **Next Steps**

1. **Deploy both services** using the provided scripts
2. **Test all functionality** thoroughly
3. **Set up monitoring** and alerts
4. **Configure custom domains** if needed
5. **Set up CI/CD** for automated deployments

## 📞 **Support**

If you encounter issues:
1. Check Railway documentation
2. Review service logs
3. Verify configuration files
4. Test locally first
5. Contact Railway support if needed

---

**Happy Deploying! 🚀**
