# FMCG RAG Chatbot - OpenAI + Neo4j Setup

A complete RAG (Retrieval-Augmented Generation) chatbot system that processes FMCG (Fast-Moving Consumer Goods) supply chain data using Neo4j graph database and OpenAI for LLM inference.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- Neo4j Community Edition
- OpenAI API key

### 2. Setup Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install Neo4j (macOS)
```bash
brew install neo4j
brew services start neo4j
```

### 4. Configure Neo4j
1. Open http://localhost:7474
2. Login with `neo4j` / `neo4j`
3. Change password to `password` when prompted

### 5. Setup Configuration
Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "your-openai-api-key-here"
OPENAI_MODEL = "gpt-4o-mini"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"
```

### 6. Run the Chatbot
```bash
source .venv/bin/activate
streamlit run bot.py
```

Visit http://localhost:8501 to use the chatbot!

## 📊 Data Processing

### Quick Test (10 SKUs)
1. Click "🚀 Quick Test (10 SKUs)" in the sidebar
2. This processes the first 10 SKUs from the Excel file
3. Creates embeddings and stores data in Neo4j

### Full Dataset
1. Click "📊 Process Full Dataset" in the sidebar
2. This processes all SKUs from the Excel file

### Create Vector Index
1. Click "Create Vector Index" in the sidebar
2. This creates the Neo4j vector index for similarity search

## 🏗️ Architecture

### Components
- **LLM**: OpenAI GPT-4o-mini for natural language processing
- **Embeddings**: OpenAI embeddings (1536 dimensions) for vector similarity
- **Database**: Neo4j Community Edition with vector indexes
- **UI**: Streamlit for interactive chatbot interface
- **Data**: FMCG S&OP Excel files with supply chain data

### Graph Schema
The system transforms Excel data into a rich graph structure:

```
(SKU)-[:BELONGS_TO_CATEGORY]->(Category)
(SKU)-[:HAS_DEMAND_PLAN]->(DemandPlan)
(SKU)-[:HAS_SUPPLY_PLAN]->(SupplyPlan)
(SKU)-[:HAS_INVENTORY]->(Inventory)
```

### RAG Pipeline
1. **Data Ingestion**: Excel files → Neo4j graph nodes
2. **Vector Embeddings**: Text data → OpenAI embeddings → Neo4j vector index
3. **Query Processing**: User question → Vector similarity search + Cypher queries
4. **Response Generation**: Retrieved context + OpenAI LLM → Detailed response

## 📁 Key Files

- `bot.py` - Main Streamlit chatbot application
- `llm.py` - OpenAI LLM and embedding configuration
- `graph.py` - Neo4j connection with error handling
- `excel_ingestion.py` - Process Excel data into Neo4j graph schema
- `quick_ingestion_2_skus.py` - Quick test with configurable SKU count
- `create_vector_index.py` - Create Neo4j vector index
- `solutions/agent.py` - LangChain agent for conversational AI
- `solutions/tools/vector.py` - Vector similarity search tool
- `solutions/tools/cypher.py` - Cypher query generation tool

## 🔧 Configuration Details

### OpenAI Setup
- **Model**: `gpt-4o-mini` (cost-effective, high-performance)
- **Embeddings**: OpenAI embeddings (1536 dimensions)
- **API Key**: Required in `.streamlit/secrets.toml`

### Neo4j Setup
- **Database**: Community Edition
- **Port**: 7687 (Bolt), 7474 (Browser)
- **Credentials**: neo4j/password
- **Vector Index**: `moviePlots` (1536 dimensions, cosine similarity)

### Vector Search
- **Dimensions**: 1536 (matches OpenAI embeddings)
- **Similarity**: Cosine similarity
- **Index**: `moviePlots` on `plotEmbedding` property
- **Retrieval**: Top-k similarity search with SKU prioritization

## 🧪 Testing

### Sample Questions to Try
- "What is the category of SKU001?"
- "What country is SKU001 from?"
- "Tell me about SKU001"
- "What are the supply chain details for SKU001?"
- "Show me the demand plan for SKU001"
- "What is the inventory plan for SKU001?"
- "Give me the financial details for SKU001"
- "What are the logistics details for SKU001?"

### Expected Responses
The chatbot provides detailed, structured responses including:
- **Basic Info**: Category, country, unit of measure, lead time
- **Monthly Plans**: Demand, supply, and inventory plans for each month
- **Financial Data**: Unit price, cost, revenue, COGS, gross profit
- **Logistics**: Warehouse, distribution cost, safety stock

## 🎯 Features

- ✅ **OpenAI Integration**: GPT-4o-mini for high-quality responses
- ✅ **Vector Search**: Similarity-based retrieval with SKU prioritization
- ✅ **Cypher Queries**: Structured graph queries for precise data access
- ✅ **Excel Processing**: Upload and process FMCG S&OP data
- ✅ **Real-time Chat**: Interactive chatbot interface
- ✅ **Hybrid RAG**: Combines vector and structured search
- ✅ **Graph Schema**: Rich relationship model for supply chain data
- ✅ **Agent Architecture**: Conversational AI with tool selection

## 🐛 Troubleshooting

### Neo4j Issues
- Check if Neo4j is running: `brew services list | grep neo4j`
- Restart: `brew services restart neo4j`
- Check logs: `tail -f /usr/local/var/log/neo4j/neo4j.log`

### OpenAI Issues
- Verify API key in `.streamlit/secrets.toml`
- Check OpenAI account for usage limits
- Ensure model name is correct: `gpt-4o-mini`

### Python Issues
- Activate virtual environment: `source .venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version`

### Data Issues
- Verify Excel file exists: `FMCG S&OP Working Excel.xlsx`
- Check Neo4j browser: http://localhost:7474
- Run vector index creation if needed

## 📈 Performance

- **Embedding Generation**: ~0.2-0.5 seconds per SKU (OpenAI)
- **Vector Search**: Real-time similarity search
- **Chatbot Response**: 2-5 seconds per query
- **Data Processing**: ~30 seconds for 10 SKUs

## 🔄 Development Workflow

1. **Data Ingestion**: Process Excel files into Neo4j graph schema
2. **Vector Index**: Create embeddings for similarity search
3. **Chatbot**: Query data using natural language
4. **RAG**: Combine vector search with structured queries

## 💡 Advanced Usage

### Custom Questions
The system can handle complex queries like:
- "Which SKUs have the highest revenue?"
- "Show me all products in the Legumes category"
- "What's the average lead time across all SKUs?"
- "Which products have negative gross profit?"

### Data Analysis
- **Supply Chain Optimization**: Analyze demand vs supply gaps
- **Financial Analysis**: Revenue, cost, and profit analysis
- **Inventory Management**: Safety stock and inventory planning
- **Logistics Planning**: Warehouse and distribution optimization

## 📝 License

This project extends the original graph-based RAG system for FMCG supply chain analysis, providing a complete local setup with OpenAI integration. 