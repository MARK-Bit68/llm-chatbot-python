# 🚀 FMCG Supply Chain UI - Deployment Guide

## Overview

This guide covers deploying both the **Streamlit backend** and **React frontend** to Railway.app, creating a robust, modern FMCG supply chain assistant.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │────│  Streamlit API  │────│   Neo4j Aura   │
│  (Frontend)     │    │   (Backend)     │    │   (Database)    │
│  Port: 3000     │    │  Port: 8501     │    │   Cloud DB      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Deployment Options

### Option 1: Full Stack Deployment (Recommended)

Deploy both frontend and backend as separate Railway services:

#### 1. Deploy Streamlit Backend

```bash
# Use existing railway.toml
railway up
```

#### 2. Deploy React Frontend

```bash
# Create new Railway service for frontend
railway login
railway init
cp railway-ui.toml railway.toml
railway up
```

#### 3. Configure Environment Variables

**Backend Service:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `NEO4J_URI`: Neo4j Aura connection string
- `NEO4J_USERNAME`: Database username  
- `NEO4J_PASSWORD`: Database password
- `STREAMLIT_CONFIG`: .streamlit/config.toml

**Frontend Service:**
- `VITE_API_URL`: URL of your deployed Streamlit service
- `NODE_ENV`: production

### Option 2: Integrated Deployment

Serve React build from Streamlit:

#### 1. Build React App

```bash
npm run build
```

#### 2. Update Streamlit to Serve Static Files

```python
# Add to bot.py
import streamlit.components.v1 as components
import os

# Serve React build
if os.path.exists('./dist/index.html'):
    with open('./dist/index.html', 'r') as f:
        components.html(f.read(), height=800)
```

#### 3. Deploy Single Service

```bash
railway up
```

## Local Development

### Start Full Stack Locally

```bash
# Terminal 1: Start Streamlit backend
streamlit run bot.py --server.port=8501

# Terminal 2: Start React frontend  
npm run dev

# Terminal 3: Run tests
./start-and-test.sh
```

### Environment Setup

1. **Copy secrets:**
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Add your API keys and database credentials
```

2. **Install dependencies:**
```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies  
npm install
```

## Testing

### Automated Tests

```bash
# Run UI tests
# Test files have been migrated to use Playwright MCP server

# Run integrated test
./start-and-test.sh

# Test Streamlit backend
python -m pytest test_*.py
```

### Manual Testing Checklist

- [ ] **Navigation**: All sidebar links work
- [ ] **Chat**: Chat interface loads and responds
- [ ] **Dashboard**: Metrics and charts display
- [ ] **SKU Explorer**: Data loads and filters work
- [ ] **Analytics**: Charts render correctly
- [ ] **Settings**: Configuration saves
- [ ] **Responsive**: Works on mobile/tablet
- [ ] **Performance**: Fast loading times
- [ ] **Database**: Neo4j connection works
- [ ] **AI**: OpenAI responses work

## Configuration

### React Environment Variables

```env
# .env.production
VITE_API_URL=https://your-streamlit-service.railway.app
VITE_APP_NAME=FMCG Supply Chain Assistant
VITE_APP_VERSION=1.0.0
```

### Streamlit Configuration

```toml
# .streamlit/config.toml
[server]
port = 8501
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
base = "dark"
primaryColor = "#7C4DFF"
backgroundColor = "#0B1020"
secondaryBackgroundColor = "#121A2B"
textColor = "#E6E6F0"
font = "Inter"
```

## Performance Optimization

### Frontend Optimizations

1. **Code Splitting**: Routes are automatically split
2. **Tree Shaking**: Unused code is eliminated  
3. **Asset Optimization**: Images and fonts are optimized
4. **Caching**: React Query provides intelligent caching

### Backend Optimizations

1. **Connection Pooling**: Neo4j driver uses connection pooling
2. **Response Caching**: LangChain tools cache responses
3. **Query Optimization**: Cypher queries are optimized
4. **Memory Management**: Streamlit session state is optimized

## Monitoring

### Health Checks

```bash
# Frontend health check
curl https://your-frontend.railway.app/

# Backend health check  
curl https://your-backend.railway.app/_stcore/health
```

### Performance Monitoring

- **Frontend**: Built-in React DevTools and Lighthouse
- **Backend**: Streamlit built-in metrics and custom monitoring
- **Database**: Neo4j Aura monitoring dashboard

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure `enableCORS = false` in Streamlit config
2. **API Connection**: Verify `VITE_API_URL` points to correct backend
3. **Database Connection**: Check Neo4j credentials and network access
4. **Build Failures**: Ensure all dependencies are properly specified

### Debug Mode

```bash
# Enable debug logging
export DEBUG=1
streamlit run bot.py --logger.level=debug

# Enable React DevTools
export NODE_ENV=development
npm run dev
```

## Security

### Environment Variables

- Never commit API keys or passwords
- Use Railway's environment variable management
- Rotate credentials regularly

### HTTPS

- Railway provides automatic HTTPS
- Ensure all API calls use HTTPS in production
- Set secure headers in Streamlit

## Scaling

### Horizontal Scaling

- Frontend: Can be deployed to CDN
- Backend: Can run multiple Streamlit instances
- Database: Neo4j Aura auto-scales

### Vertical Scaling

- Increase Railway service resources as needed
- Monitor memory usage and response times
- Optimize database queries for performance

## Success Metrics

After deployment, verify:

- [ ] **Uptime**: > 99.9%
- [ ] **Response Time**: < 2 seconds
- [ ] **Error Rate**: < 1%
- [ ] **User Experience**: Smooth interactions
- [ ] **Data Accuracy**: Correct query results
- [ ] **Mobile Experience**: Responsive design works