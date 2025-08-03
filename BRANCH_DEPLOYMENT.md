# 🌿 Branch-Based Deployment Guide

This guide explains how to deploy your FMCG RAG Chatbot from specific GitHub branches using Railway.

## 🎯 **Branch Deployment Options**

### **Option 1: Deploy from Main Branch (Recommended for Production)**
```bash
# Your main branch contains stable, tested code
git checkout main
git push origin main
# Railway will deploy from main branch
```

### **Option 2: Deploy from Development Branch**
```bash
# Create a development branch for testing
git checkout -b develop
git push origin develop
# Configure Railway to deploy from develop branch
```

### **Option 3: Deploy from Feature Branch**
```bash
# Create a feature branch for specific features
git checkout -b feature/deployment-test
git push origin feature/deployment-test
# Configure Railway to deploy from this branch
```

## 🚀 **Setting Up Branch Deployment**

### **Step 1: Choose Your Deployment Branch**

When setting up Railway:

1. **During Initial Setup:**
   - Railway will show you all available branches
   - Select your preferred branch (e.g., `main`, `develop`, `deployment`)
   - This becomes your default deployment branch

2. **After Setup (Changing Branch):**
   - Go to your Railway project dashboard
   - Navigate to **Settings** → **Source**
   - Click **Change branch**
   - Select your desired branch
   - Railway will redeploy from the new branch

### **Step 2: Branch-Specific Configuration**

You can have different configurations per branch:

#### **Main Branch (Production)**
```bash
# Environment variables for production
OPENAI_MODEL=gpt-4o-mini
NEO4J_URI=neo4j+s://production-db.databases.neo4j.io:7687
```

#### **Develop Branch (Testing)**
```bash
# Environment variables for testing
OPENAI_MODEL=gpt-4o-mini
NEO4J_URI=neo4j+s://test-db.databases.neo4j.io:7687
```

## 🔄 **Workflow Examples**

### **Production Workflow**
```bash
# 1. Develop on feature branch
git checkout -b feature/new-feature
# ... make changes ...
git push origin feature/new-feature

# 2. Create pull request to main
# ... review and merge ...

# 3. Deploy from main
git checkout main
git pull origin main
# Railway automatically deploys from main
```

### **Testing Workflow**
```bash
# 1. Push to develop branch for testing
git checkout develop
git merge feature/new-feature
git push origin develop

# 2. Configure Railway to deploy from develop
# Railway dashboard → Settings → Source → Change branch → develop

# 3. Test the deployment
# ... test your app ...

# 4. If tests pass, merge to main
git checkout main
git merge develop
git push origin main
```

## 📋 **Branch Deployment Checklist**

### **Before Deploying from a Branch:**

- [ ] **Branch is up to date** with latest changes
- [ ] **All tests pass** locally
- [ ] **Dependencies are correct** in `requirements.txt`
- [ ] **Configuration files** are present (`railway.toml`, `Procfile`)
- [ ] **Environment variables** are set in Railway
- [ ] **Neo4j connection** is configured for the branch
- [ ] **OpenAI API key** is valid

### **After Deploying from a Branch:**

- [ ] **App loads** without errors
- [ ] **Neo4j connection** works
- [ ] **OpenAI API** calls succeed
- [ ] **Data processing** works (if applicable)
- [ ] **Chat functionality** works
- [ ] **Sample questions** load correctly

## 🛠️ **Railway Branch Management**

### **Viewing Current Branch:**
1. Go to Railway dashboard
2. Click on your project
3. Go to **Settings** → **Source**
4. See current deployment branch

### **Changing Deployment Branch:**
1. Go to **Settings** → **Source**
2. Click **Change branch**
3. Select new branch
4. Railway will redeploy automatically

### **Manual Deployment from Branch:**
1. Go to **Deployments** tab
2. Click **Deploy** button
3. Select branch to deploy from
4. Railway will build and deploy

## 🔍 **Troubleshooting Branch Deployments**

### **Common Issues:**

1. **Branch not found:**
   - Ensure branch exists on GitHub
   - Check branch name spelling
   - Push branch to remote if needed

2. **Build failures on specific branch:**
   - Check `requirements.txt` in that branch
   - Verify all dependencies are listed
   - Check for syntax errors in code

3. **Environment variables not working:**
   - Verify variables are set in Railway
   - Check variable names match your code
   - Ensure no typos in variable names

### **Debugging Commands:**
```bash
# Check current branch
git branch

# List all remote branches
git branch -r

# Switch to deployment branch
git checkout your-deployment-branch

# Push branch to remote
git push origin your-deployment-branch
```

## 💡 **Best Practices**

### **Branch Naming:**
- `main` - Production deployment
- `develop` - Development/testing
- `feature/xyz` - Feature-specific testing
- `hotfix/xyz` - Emergency fixes

### **Deployment Strategy:**
- **Main branch**: Always stable, tested code
- **Develop branch**: Integration testing
- **Feature branches**: Individual feature testing

### **Environment Management:**
- Use different Neo4j databases for different environments
- Set appropriate OpenAI spending limits per environment
- Monitor usage separately for each deployment

## 🎉 **Success!**

Your app is now deployed from your chosen branch. Railway will automatically redeploy whenever you push changes to that branch, making it easy to maintain different versions of your app for different purposes. 