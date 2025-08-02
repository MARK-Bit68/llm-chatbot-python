# FMCG RAG Chatbot - Local Setup

A complete local RAG (Retrieval-Augmented Generation) chatbot system that processes FMCG (Fast-Moving Consumer Goods) supply chain data using Neo4j graph database and Ollama for local LLM inference.

## 🚀 Quick Start

### 1. Setup Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements_local.txt
```

### 2. Install and Start Services

#### Install Neo4j (macOS)
```bash
brew install neo4j
brew services start neo4j
```

#### Install Ollama
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2
ollama serve &
```

### 3. Configure Neo4j
1. Open http://localhost:7474
2. Login with `neo4j` / `neo4j`
3. Change password to `password` when prompted

### 4. Run the Chatbot
```bash
./run_chatbot.sh
# Or manually:
source .venv/bin/activate
streamlit run bot.py
```

Visit http://localhost:8501 to use the chatbot!

## 📊 Data Processing

### Quick Test (2 SKUs)
```bash
python quick_ingestion_2_skus.py
```

### Full Dataset
```bash
python excel_ingestion.py
```

### Create Vector Index
```bash
python create_vector_index.py
```

## 🏗️ Architecture

- **LLM**: Ollama with llama2 model (local)
- **Embeddings**: Ollama embeddings (local)
- **Database**: Neo4j Community Edition
- **UI**: Streamlit
- **Data**: FMCG S&OP Excel files

## 📁 Key Files

- `bot.py` - Main Streamlit chatbot application
- `llm.py` - Local LLM configuration (Ollama)
- `graph.py` - Neo4j connection with error handling
- `excel_ingestion.py` - Process Excel data into Neo4j
- `quick_ingestion_2_skus.py` - Quick test with 2 SKUs
- `create_vector_index.py` - Create Neo4j vector index
- `run_chatbot.sh` - Convenient startup script

## 🔧 Configuration

### Streamlit Secrets (`.streamlit/secrets.toml`)
```toml
OPENAI_API_KEY = "local"
OPENAI_MODEL = "llama2"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"
```

## 🧪 Testing

### Sample Questions to Try
- "What is the category of SKU001?"
- "What country is SKU001 from?"
- "Tell me about SKU001"
- "What are the supply chain details for SKU001?"
- "Show me the demand plan for SKU001"

## 🎯 Features

- ✅ **Local LLM**: No external API dependencies
- ✅ **Vector Search**: Similarity-based retrieval
- ✅ **Cypher Queries**: Structured graph queries
- ✅ **Excel Processing**: Upload and process FMCG data
- ✅ **Real-time Chat**: Interactive chatbot interface
- ✅ **Hybrid RAG**: Combines vector and structured search

## 🐛 Troubleshooting

### Neo4j Issues
- Check if Neo4j is running: `brew services list | grep neo4j`
- Restart: `brew services restart neo4j`
- Check logs: `tail -f /usr/local/var/log/neo4j/neo4j.log`

### Ollama Issues
- Check if Ollama is running: `curl http://localhost:11434/api/tags`
- Restart: `pkill ollama && ollama serve &`
- Pull model: `ollama pull llama2`

### Python Issues
- Activate virtual environment: `source .venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements_local.txt`

## 📈 Performance

- **Embedding Generation**: ~3 minutes per SKU (Ollama)
- **Vector Search**: Real-time similarity search
- **Chatbot Response**: 5-10 seconds per query
- **Data Processing**: ~30 seconds for 2 SKUs

## 🔄 Development Workflow

1. **Data Ingestion**: Process Excel files into Neo4j
2. **Vector Index**: Create embeddings for similarity search
3. **Chatbot**: Query data using natural language
4. **RAG**: Combine vector search with structured queries

## 📝 License

This project extends the original graph-based RAG system for FMCG supply chain analysis. 