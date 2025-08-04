# FMCG Supply Chain RAG System

> **A sophisticated Retrieval-Augmented Generation (RAG) system for FMCG supply chain analysis, evolved from a simple LLM chatbot to a production-ready cloud application.**

[![Railway Deploy](https://railway.app/button.svg)](https://railway.app)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-AuraDB-green.svg)](https://neo4j.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-purple.svg)](https://openai.com)

## 🚀 Overview

This project represents a **complete evolution** from a basic Neo4j-backed chatbot to a sophisticated FMCG (Fast-Moving Consumer Goods) supply chain analysis system. What started as a simple LLM chatbot has grown into a production-ready RAG application that processes complex supply chain data, provides intelligent insights, and runs seamlessly in the cloud.

### 🎯 What This System Does

- **Processes FMCG supply chain data** from Excel files into a rich graph database
- **Provides intelligent querying** of supply chain metrics using natural language
- **Generates actionable insights** for inventory, demand, supply, and financial planning
- **Runs both locally** (for development) and **in the cloud** (for production)
- **Combines vector search** with structured graph queries for comprehensive analysis

## 🏗️ Architecture Evolution

### Phase 1: Local Development (Open Source Stack)
- **LLM**: Ollama with local models (Llama2, Mistral)
- **Database**: Neo4j Community Edition
- **UI**: Streamlit
- **Deployment**: Local development environment

### Phase 2: Cloud Migration (Production Stack)
- **LLM**: OpenAI GPT-4o-mini (enhanced performance)
- **Database**: Neo4j AuraDB (managed cloud database)
- **UI**: Streamlit (cloud-hosted)
- **Deployment**: Railway (automatic deployments)
- **Vector Search**: OpenAI embeddings with Neo4j vector indexes

## 🛠️ Technology Stack

### Core Components
- **Language Model**: OpenAI GPT-4o-mini for natural language processing
- **Vector Database**: Neo4j AuraDB with vector indexes
- **Embeddings**: OpenAI embeddings (1536 dimensions)
- **Web Framework**: Streamlit for interactive UI
- **Cloud Platform**: Railway for automated deployment
- **Data Processing**: Custom Excel ingestion pipeline

### Advanced Features
- **Hybrid RAG**: Combines vector similarity search with structured Cypher queries
- **Dynamic Query Generation**: LLM-powered Cypher query generation with schema awareness
- **Multi-Modal Retrieval**: Vector search + graph traversal + analytical queries
- **Real-time Processing**: Live data ingestion and analysis
- **Production Monitoring**: Comprehensive logging and error handling

## 📊 Data Model

The system transforms FMCG supply chain data into a rich graph structure:

```
(SKU)-[:BELONGS_TO_CATEGORY]->(Category)
(SKU)-[:HAS_DEMAND_PLAN]->(DemandPlan)
(SKU)-[:HAS_SUPPLY_PLAN]->(SupplyPlan)
(SKU)-[:HAS_INVENTORY_PLAN]->(InventoryPlan)
(SKU)-[:HAS_FINANCIAL_PLAN]->(FinancialPlan)
(SKU)-[:HAS_LOGISTICS_PLAN]->(LogisticsPlan)
```

Each SKU node contains:
- **Basic Info**: SKU ID, name, category, country, unit of measure
- **Financial Data**: Unit price, cost, revenue, COGS, gross profit
- **Supply Chain**: Lead time, safety stock, forecasted volume
- **Monthly Plans**: Demand, supply, and inventory plans for each month
- **Logistics**: Warehouse, distribution cost, initial inventory

## 🚀 Quick Start

### Option 1: Cloud Deployment (Recommended)

The system is **automatically deployed** to Railway when you push to the `poc1` branch:

1. **Fork this repository**
2. **Set up Railway integration** with your GitHub account
3. **Configure environment variables** in Railway:
   ```
   OPENAI_API_KEY=your-openai-api-key
   NEO4J_URI=your-aura-db-uri
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-aura-db-password
   ```
4. **Push to `poc1` branch** - Railway will automatically deploy
5. **Access your application** at the Railway-provided URL

### Option 2: Local Development

#### Prerequisites
- Python 3.8+
- Neo4j Community Edition (local)
- OpenAI API key

#### Setup Steps

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd llm-chatbot-python
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements_local.txt
   ```

2. **Install Neo4j locally**:
   ```bash
   # macOS
   brew install neo4j
   brew services start neo4j
   
   # Or download from https://neo4j.com/download/
   ```

3. **Configure Neo4j**:
   - Open http://localhost:7474
   - Login with `neo4j` / `neo4j`
   - Change password to `password`

4. **Setup configuration**:
   Create `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "your-openai-api-key-here"
   OPENAI_MODEL = "gpt-4o-mini"
   NEO4J_URI = "bolt://localhost:7687"
   NEO4J_USERNAME = "neo4j"
   NEO4J_PASSWORD = "password"
   ```

5. **Run the application**:
   ```bash
   streamlit run bot.py
   ```

6. **Access the application** at http://localhost:8501

## 📊 Data Processing

### Quick Test (10 SKUs)
```bash
# Run the quick ingestion script
python quick_ingestion_2_skus.py
```

### Full Dataset Processing
```bash
# Process the complete Excel dataset
python excel_ingestion.py
```

### Create Vector Index
```bash
# Create Neo4j vector index for similarity search
python create_vector_index.py
```

## 🧪 Testing

### Comprehensive Test Suite

Run the full test suite to validate the system:

```bash
# Run comprehensive tests
python test_stack.py
```

This tests:
- ✅ **Simple factual lookups** (e.g., "What country is SKU001 from?")
- ✅ **Data extraction and formatting** (e.g., "What is the inventory plan for SKU001?")
- ✅ **Analytical queries** (e.g., "What if we increase demand by 10X?")

### Sample Questions to Try

**Basic Queries:**
- "What is the category of SKU001?"
- "What country is SKU001 from?"
- "Tell me about SKU001"

**Supply Chain Analysis:**
- "What are the supply chain details for SKU001?"
- "Show me the demand plan for SKU001"
- "What is the inventory plan for SKU001?"

**Financial Analysis:**
- "Give me the financial details for SKU001"
- "What's the revenue for SKU001?"
- "Show me the cost structure for SKU001"

**Advanced Analytics:**
- "Which SKUs have the highest revenue?"
- "Show me all products in the Legumes category"
- "What's the average lead time across all SKUs?"
- "Which products have negative gross profit?"

## 🔧 Configuration Details

### OpenAI Configuration
- **Model**: `gpt-4o-mini` (cost-effective, high-performance)
- **Embeddings**: OpenAI embeddings (1536 dimensions)
- **API Key**: Required in `.streamlit/secrets.toml`

### Neo4j Configuration
- **Local**: Community Edition (port 7687)
- **Cloud**: AuraDB (managed service)
- **Vector Index**: `skuPlots` (1536 dimensions, cosine similarity)
- **Credentials**: Configured via environment variables

### Vector Search Configuration
- **Dimensions**: 1536 (matches OpenAI embeddings)
- **Similarity**: Cosine similarity
- **Index**: `skuPlots` on `plotEmbedding` property
- **Retrieval**: Top-k similarity search with SKU prioritization

## 🏗️ Development Journey

### The Evolution Story

This project began as a **simple LLM chatbot** based on the Neo4j GraphAcademy course, but quickly evolved into something much more sophisticated. Here's the journey:

#### Phase 1: Local Development with Open Source Tools
- **Started with**: Basic LLM chatbot using Ollama and local Neo4j
- **Challenges**: Limited model performance, local deployment complexity
- **Solutions**: Implemented robust error handling, comprehensive testing

#### Phase 2: Cloud Migration and Production Hardening
- **Pivot to cloud**: Migrated from local Ollama to OpenAI GPT-4o-mini
- **Database upgrade**: Moved from local Neo4j to AuraDB
- **Deployment automation**: Railway integration with automatic deployments
- **Robustness improvements**: Enhanced error handling, better logging, production monitoring

#### Phase 3: Advanced RAG Implementation
- **Hybrid retrieval**: Combined vector search with structured graph queries
- **Dynamic query generation**: LLM-powered Cypher query generation with schema awareness
- **Multi-modal analysis**: Support for complex analytical queries
- **Production optimization**: Performance tuning, caching, error recovery

### Key Technical Achievements

1. **Schema-Aware Query Generation**: The LLM receives comprehensive schema information, enabling precise Cypher query generation
2. **Hybrid RAG Pipeline**: Combines vector similarity search with structured graph queries for comprehensive analysis
3. **Production-Ready Architecture**: Robust error handling, comprehensive logging, and cloud-native deployment
4. **Multi-Environment Support**: Works seamlessly both locally and in the cloud
5. **Comprehensive Testing**: Full test suite covering all major functionality

## 📁 Project Structure

```
llm-chatbot-python/
├── bot.py                          # Main Streamlit application
├── llm.py                          # OpenAI LLM configuration
├── graph.py                        # Neo4j connection management
├── excel_ingestion.py              # Excel data processing pipeline
├── quick_ingestion_2_skus.py      # Quick test ingestion
├── create_vector_index.py          # Vector index creation
├── test_stack.py                   # Comprehensive test suite
├── solutions/
│   ├── agent.py                    # LangChain agent implementation
│   └── tools/
│       ├── cypher.py              # Cypher query generation
│       ├── vector.py              # Vector similarity search
│       └── data_parser.py         # Data parsing utilities
├── railway.toml                    # Railway deployment configuration
├── requirements.txt                # Production dependencies
├── requirements_local.txt          # Local development dependencies
└── .streamlit/
    └── secrets.toml               # Configuration (not in repo)
```

## 🎯 Features

### Core RAG Capabilities
- ✅ **Hybrid Retrieval**: Vector similarity + structured graph queries
- ✅ **Dynamic Query Generation**: LLM-powered Cypher with schema awareness
- ✅ **Multi-Modal Analysis**: Support for complex analytical queries
- ✅ **Real-time Processing**: Live data ingestion and analysis

### Production Features
- ✅ **Cloud Deployment**: Automatic Railway deployment
- ✅ **Error Handling**: Comprehensive error recovery and logging
- ✅ **Performance Optimization**: Caching, query optimization, response time monitoring
- ✅ **Multi-Environment Support**: Local development + cloud production

### Data Processing
- ✅ **Excel Integration**: Process FMCG S&OP Excel files
- ✅ **Graph Transformation**: Convert tabular data to rich graph structure
- ✅ **Vector Embeddings**: Generate and store embeddings for similarity search
- ✅ **Real-time Updates**: Live data processing and indexing

## 🐛 Troubleshooting

### Common Issues

**Neo4j Connection Issues:**
```bash
# Check if Neo4j is running (local)
brew services list | grep neo4j

# Restart Neo4j (local)
brew services restart neo4j

# Check logs (local)
tail -f /usr/local/var/log/neo4j/neo4j.log
```

**OpenAI API Issues:**
- Verify API key in `.streamlit/secrets.toml`
- Check OpenAI account for usage limits
- Ensure model name is correct: `gpt-4o-mini`

**Python Environment Issues:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version
```

**Railway Deployment Issues:**
- Check Railway logs for deployment errors
- Verify environment variables are set correctly
- Ensure the `poc1` branch is being deployed

## 📈 Performance Metrics

- **Embedding Generation**: ~0.2-0.5 seconds per SKU
- **Vector Search**: Real-time similarity search
- **Chatbot Response**: 2-5 seconds per query
- **Data Processing**: ~30 seconds for 10 SKUs
- **Cloud Deployment**: Automatic deployment in ~2 minutes

## 🔄 Development Workflow

### Local Development
1. **Setup environment**: Virtual environment + local Neo4j
2. **Data ingestion**: Process Excel files into graph schema
3. **Vector index**: Create embeddings for similarity search
4. **Testing**: Run comprehensive test suite
5. **Development**: Iterate on features and improvements

### Cloud Deployment
1. **Push to `poc1`**: Triggers automatic Railway deployment
2. **Monitor deployment**: Check Railway logs for any issues
3. **Test production**: Verify functionality in cloud environment
4. **Monitor performance**: Track response times and error rates

## 💡 Advanced Usage

### Custom Analytical Queries
The system can handle complex supply chain analysis:
- **Demand Planning**: Analyze demand vs supply gaps
- **Financial Analysis**: Revenue, cost, and profit optimization
- **Inventory Management**: Safety stock and inventory planning
- **Logistics Optimization**: Warehouse and distribution analysis

### Extending the System
- **New Data Sources**: Add support for additional data formats
- **Advanced Analytics**: Implement more sophisticated analytical queries
- **Custom Tools**: Add new LangChain tools for specific use cases
- **UI Enhancements**: Extend the Streamlit interface with new features

## 📝 License

This project extends the original graph-based RAG system for FMCG supply chain analysis, providing both local development and cloud production capabilities.

---

## 🎉 Press Release

### **Retired Chemist Revolutionizes Supply Chain Analysis with AI-Powered RAG System**

*Erbil, Iraq - A retired chemist has successfully developed a cutting-edge supply chain analysis system that combines the power of artificial intelligence with graph database technology to revolutionize how companies analyze their FMCG (Fast-Moving Consumer Goods) supply chains.*

**Kosar Jaff**, a retired chemist from Erbil, has created a sophisticated Retrieval-Augmented Generation (RAG) system that transforms complex supply chain data into actionable insights using natural language queries.

> *"When I started this project, it was just a simple chatbot,"* says Jaff. *"But as I dove deeper into the challenges of supply chain analysis, I realized we needed something much more powerful. The combination of vector search, graph databases, and large language models creates a system that can understand complex supply chain questions and provide detailed, actionable answers."*

The system, which began as a local development project using open-source tools, has evolved into a production-ready cloud application that can process FMCG supply chain data from Excel files and provide intelligent analysis of inventory, demand, supply, and financial planning.

> *"The journey from local development to cloud deployment was challenging but incredibly rewarding,"* Jaff explains. *"We had to completely reengineer some components that weren't robust enough for production use. The pivot from local Ollama models to OpenAI's GPT-4o-mini, and from local Neo4j to AuraDB, required significant architectural changes. But the result is a system that's both powerful and reliable."*

**Key Technical Achievements:**

- **Hybrid RAG Pipeline**: Combines vector similarity search with structured graph queries
- **Schema-Aware Query Generation**: LLM-powered Cypher query generation with comprehensive schema information
- **Multi-Environment Support**: Works seamlessly both locally and in the cloud
- **Production-Ready Architecture**: Robust error handling, comprehensive logging, and cloud-native deployment
- **Comprehensive Testing**: Full test suite covering all major functionality

> *"What makes this system special is its ability to understand the context of supply chain data,"* says Jaff. *"It's not just about retrieving information - it's about understanding relationships between different aspects of the supply chain and providing insights that can drive real business decisions."*

The system is now deployed on Railway with automatic deployments triggered by code pushes, making it a true production-ready application that can scale with business needs.

> *"As a retired chemist, I never expected to be working on cutting-edge AI systems,"* Jaff reflects. *"But the analytical thinking I developed in chemistry - understanding complex systems, identifying patterns, and solving problems - has been incredibly valuable in building this system. It's proof that the skills we develop in one field can be applied to completely different domains."*

The project represents a significant advancement in the application of AI to supply chain analysis, demonstrating how modern technologies can be combined to create powerful, user-friendly tools for complex business problems.

*For more information about the FMCG Supply Chain RAG System, visit the project repository or contact Kosar Jaff directly.*

---

*"The best systems are those that make complex problems simple to understand and solve."* - Kosar Jaff 