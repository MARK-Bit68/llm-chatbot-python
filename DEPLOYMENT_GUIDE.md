# 🚀 Deployment Guide: FMCG RAG Chatbot

This guide will help you deploy your Streamlit app with Neo4j to Railway for a private trial with friends.

## 🎯 **Recommended Platform: Railway + External Neo4j**

Railway is excellent for Streamlit deployment, but we need to use an external Neo4j service. Here are the best options:

## 📋 **Prerequisites**

1. **GitHub Account**: Your code should be in a GitHub repository
2. **Railway Account**: Sign up at [railway.app](https://railway.app)
3. **OpenAI API Key**: Get one from [platform.openai.com](https://platform.openai.com)
4. **Neo4j AuraDB Account**: Free tier available at [neo4j.com/cloud/platform/aura-graph-database](https://neo4j.com/cloud/platform/aura-graph-database)

## 🛠️ **Step 1: Prepare Your Repository**

### 1.1 Create Railway Configuration

Create a `railway.toml` file in your repository root:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "streamlit run bot.py --server.port=$PORT --server.address=0.0.0.0"
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
```

### 1.2 Create Procfile (Alternative)

Create a `Procfile` in your repository root:

```
web: streamlit run bot.py --server.port=$PORT --server.address=0.0.0.0
```

### 1.3 Update Requirements

Ensure your `requirements.txt` includes all dependencies:

```txt
tenacity!=8.4.0
langchain==0.3.9
openai==1.56.0
langchain-openai==0.2.10
neo4j==5.27.0
streamlit==1.35.0
langchainhub==0.1.21
langchain-neo4j==0.1.1
pandas>=2.1.0
openpyxl>=3.1.2
requests>=2.31.0
```

### 1.4 Create Runtime Configuration

Create a `.streamlit/config.toml` file:

```toml
[server]
port = 8501
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

## 🗄️ **Step 2: Set Up Neo4j (External Service Required)**

### 2.1 Option A: Neo4j AuraDB (Recommended)

**Why this is best:**
- ✅ **Free tier** available (50K nodes)
- ✅ **Managed service** - no server maintenance
- ✅ **Reliable** - 99.9% uptime SLA
- ✅ **Easy setup** - zero configuration

**Setup:**
1. Go to [neo4j.com/cloud/platform/aura-graph-database](https://neo4j.com/cloud/platform/aura-graph-database)
2. Sign up for a free account
3. Create a new database instance
4. Choose the free tier (50,000 nodes, 175,000 relationships)
5. Note down your connection details:
   - Database URI (e.g., `neo4j+s://xxxxx.databases.neo4j.io:7687`)
   - Username (usually `neo4j`)
   - Password (you set this)

### 2.2 Option B: DigitalOcean + Neo4j (Self-Hosted)

**For advanced users who want full control:**
- ✅ **Full control** over the database
- ✅ **Predictable costs** ($5-10/month)
- ✅ **No data limits**
- ❌ **Manual setup** required
- ❌ **Server management** needed

**Setup:**
```bash
# On DigitalOcean droplet
sudo apt update
sudo apt install neo4j
sudo systemctl start neo4j
sudo systemctl enable neo4j
```

1. Go to [neo4j.com/cloud/platform/aura-graph-database](https://neo4j.com/cloud/platform/aura-graph-database)
2. Sign up for a free account
3. Create a new database instance
4. Choose the free tier (50,000 nodes, 175,000 relationships)
5. Note down your connection details:
   - Database URI (e.g., `neo4j+s://xxxxx.databases.neo4j.io:7687`)
   - Username (usually `neo4j`)
   - Password (you set this)

### 2.3 Test Neo4j Connection

You can test the connection locally first:

```bash
python -c "
from langchain_neo4j import Neo4jGraph
graph = Neo4jGraph(
    url='your-neo4j-uri',
    username='neo4j',
    password='your-password'
)
result = graph.query('RETURN 1 as test')
print('✅ Neo4j connection successful:', result)
"
```

## 🚀 **Step 3: Deploy to Railway**

### 3.1 Connect Repository to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account
5. Select your repository
6. **Choose your branch**: Railway will show you a list of available branches
   - Select your desired branch (e.g., `main`, `develop`, `deployment`)
   - You can change this later in the project settings

### 3.2 Configure Environment Variables

In your Railway project dashboard, go to the "Variables" tab and add:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

**For Neo4j AuraDB (Recommended):**
```bash
NEO4J_URI=neo4j+s://your-aura-instance.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-aura-password
```

**For DigitalOcean + Neo4j:**
```bash
NEO4J_URI=bolt://your-droplet-ip:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

### 3.3 Deploy

1. Railway will automatically detect your Streamlit app
2. Click "Deploy" to start the deployment
3. Wait for the build to complete (usually 2-5 minutes)

## 📊 **Step 4: Initialize Data**

### 4.1 Access Your Deployed App

Once deployed, Railway will provide you with a URL like:
`https://your-app-name.railway.app`

### 4.2 Load Initial Data

1. Open your deployed app
2. In the sidebar, click "🚀 Quick Test (10 SKUs)"
3. This will process your Excel file and create the initial 10 SKUs
4. Click "Create Vector Index" to enable similarity search

## 🔒 **Step 5: Security & Access Control**

### 5.1 Set Up Authentication (Optional)

For a private trial, you can add basic authentication:

Create a `streamlit_auth.py` file:

```python
import streamlit as st
import hmac

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password.
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False
```

Add to your `bot.py`:

```python
from streamlit_auth import check_password

if not check_password():
    st.stop()
```

Add to Railway variables:
```bash
password=your-secure-password
```

### 5.2 API Key Limits

Set up OpenAI API key limits:
1. Go to [platform.openai.com/account/limits](https://platform.openai.com/account/limits)
2. Set spending limits (e.g., $10/month)
3. Set rate limits if needed

## 💰 **Cost Estimation**

### Monthly Costs:

**Option A: Railway + Neo4j AuraDB (Recommended)**
- **Railway**: Free tier (500 hours) or $5/month
- **Neo4j AuraDB**: Free tier (50K nodes) or $0.09/node/month
- **OpenAI API**: ~$1-5/month for small usage
- **Total**: $0-10/month depending on usage

**Option B: Railway + DigitalOcean Neo4j**
- **Railway**: Free tier (500 hours) or $5/month
- **DigitalOcean**: $5-10/month for droplet
- **OpenAI API**: ~$1-5/month for small usage
- **Total**: $6-20/month depending on usage

## 🔧 **Troubleshooting**

### Common Issues:

1. **Build Failures**: Check that all dependencies are in `requirements.txt`
2. **Neo4j Connection**: Verify your AuraDB credentials
3. **OpenAI API**: Check your API key and limits
4. **Memory Issues**: Railway free tier has 512MB RAM limit

### Monitoring:

1. **Railway Dashboard**: Monitor app performance and logs
2. **Neo4j Browser**: Access at your AuraDB URL to check data
3. **OpenAI Usage**: Monitor at [platform.openai.com/usage](https://platform.openai.com/usage)

## 🎉 **Success!**

Your app should now be accessible at your Railway URL. Share this URL with your friends for the private trial!

## 📈 **Scaling Up**

If you need more resources:
1. **Railway**: Upgrade to paid plan ($5/month)
2. **Neo4j**: Upgrade AuraDB plan if you exceed free tier
3. **OpenAI**: Increase spending limits as needed

## 🔄 **Updates**

To update your app:
1. Push changes to your deployment branch on GitHub
2. Railway will automatically redeploy from that branch
3. Your data in Neo4j will persist between deployments

### Branch-Specific Deployment

Railway allows you to:
- **Deploy from any branch**: Select your preferred branch during setup
- **Change deployment branch**: Go to Project Settings → Source → Change branch
- **Auto-deploy**: Railway automatically redeploys when you push to the selected branch
- **Manual deployment**: You can also trigger manual deployments from any branch

### Recommended Branch Strategy:
- **`main`**: Production deployment (stable code)
- **`develop`**: Development/testing deployment
- **`feature/xyz`**: Feature-specific deployments for testing 