import streamlit as st
from utils import write_message
from llm import llm, embeddings
from graph import graph
import json

# Page Config
st.set_page_config("FMCG RAG Chatbot", page_icon=":chart_with_upwards_trend:")

# Set up Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I'm your FMCG S&OP RAG Chatbot! I can help you analyze your supply chain data. How can I assist you today?"},
    ]

# Check Neo4j status
neo4j_available = graph is not None

# Sidebar for data upload
with st.sidebar:
    st.header("📊 Data Management")
    
    if neo4j_available:
        # Excel upload section
        st.subheader("Upload FMCG Data")
        try:
            from excel_ingestion import upload_fmcg_excel
            upload_fmcg_excel()
        except Exception as e:
            st.error(f"Excel upload error: {e}")
        
        # Manual data processing
        st.subheader("Process Existing File")
        
        # Quick test with 2 SKUs
        if st.button("🚀 Quick Test (2 SKUs)"):
            with st.spinner("Processing 2 SKUs for quick test..."):
                try:
                    from quick_ingestion_2_skus import quick_ingestion_2_skus
                    results = quick_ingestion_2_skus("FMCG S&OP Working Excel.xlsx", max_skus=2)
                    if 'sample_questions' in results:
                        st.success(f"✅ Processed {results['nodes_created']} SKUs with embeddings")
                        st.info("📝 Sample questions generated! Try asking about the uploaded data.")
                        # Show sample questions
                        with st.expander("📋 Sample Questions to Try"):
                            for i, question in enumerate(results['sample_questions'][:10], 1):
                                st.write(f"{i}. {question}")
                    else:
                        st.error(f"Error: {results.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Full dataset processing
        if st.button("📊 Process Full Dataset"):
            with st.spinner("Processing full Excel file..."):
                try:
                    from excel_ingestion import extract_fmcg_data
                    results = extract_fmcg_data("FMCG S&OP Working Excel.xlsx")
                    st.success(f"✅ Processed {results['nodes_created']} products from {results['total_rows']} rows")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Vector index creation
        st.subheader("Setup Vector Index")
        if st.button("Create Vector Index"):
            with st.spinner("Creating vector index..."):
                try:
                    from create_vector_index import create_vector_index
                    create_vector_index()
                    st.success("✅ Vector index created successfully!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.warning("⚠️ Neo4j not available")
        st.info("Install Neo4j to enable data processing and RAG capabilities")

def vector_search(query, top_k=5):
    """Perform vector similarity search using Neo4jVector"""
    if not neo4j_available:
        return []
    
    try:
        from langchain_neo4j import Neo4jVector
        
        # Create Neo4jVector retriever
        neo4jvector = Neo4jVector.from_existing_index(
            embeddings,
            graph=graph,
            index_name="moviePlots",
            node_label="Movie",
            text_node_property="plot",
            embedding_node_property="plotEmbedding",
            retrieval_query="""
RETURN
    node.plot AS text,
    score,
    {
        title: node.title,
        sku_id: node.sku_id,
        tmdbId: node.tmdbId,
        data_type: node.data_type
    } AS metadata
"""
        )
        
        retriever = neo4jvector.as_retriever(search_kwargs={"k": top_k})
        results = retriever.invoke(query)
        
        # Convert to our expected format
        formatted_results = []
        for doc in results:
            formatted_results.append({
                'm.title': doc.metadata.get('title', 'Unknown'),
                'm.plot': doc.page_content,
                'm.sku_id': doc.metadata.get('sku_id', 'Unknown'),
                'score': doc.metadata.get('score', 0.0)
            })
        
        # Debug: Print what we found
        st.info(f"🔍 Vector search found {len(formatted_results)} results for query: '{query}'")
        for i, result in enumerate(formatted_results):
            st.info(f"Result {i+1}: SKU={result.get('m.sku_id')}, Title={result.get('m.title')}")
        
        return formatted_results
    except Exception as e:
        st.error(f"Vector search error: {e}")
        return []

def cypher_search(query):
    """Generate and execute Cypher queries"""
    if not neo4j_available:
        return []
    
    try:
        # Simple keyword-based search
        cypher_query = """
        MATCH (m:Movie)
        WHERE toLower(m.title) CONTAINS toLower($query) 
           OR toLower(m.plot) CONTAINS toLower($query)
        RETURN m.title, m.plot, m.sku_id
        LIMIT 10
        """
        
        results = graph.query(cypher_query, {'query': query})
        return results
    except Exception as e:
        st.error(f"Cypher search error: {e}")
        return []

def generate_response(user_query, context_results):
    """Generate response using local LLM with context"""
    
    if not neo4j_available:
        # Fallback response when Neo4j is not available
        prompt = f"""You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant.
        
User Question: {user_query}

Note: The database is not currently available, so I cannot provide specific data-driven responses.

Please provide a helpful response about FMCG supply chain concepts, but note that I cannot access specific data at the moment.

Response:"""
    else:
        # Prepare context
        context_parts = []
        for result in context_results:
            if isinstance(result, dict):
                title = result.get('m.title', result.get('title', 'Unknown'))
                plot = result.get('m.plot', result.get('plot', ''))
                sku = result.get('m.sku_id', result.get('sku_id', ''))
                context_parts.append(f"Product: {title}\nSKU: {sku}\nDetails: {plot}\n")
        
        context = "\n".join(context_parts) if context_parts else "No relevant data found."
        
        # Debug: Show what context we're sending to LLM
        st.info(f"📤 Sending context to LLM: {len(context)} characters")
        with st.expander("🔍 Debug: Context being sent to LLM"):
            st.text(context)
        
        # Create prompt
        prompt = f"""Answer this FMCG question based on the data:

Q: {user_query}

Data: {context}

A:"""
    
    try:
        # Generate response using local LLM
        response = llm.invoke(prompt)
        return response
    except Exception as e:
        return f"I apologize, but I encountered an error generating a response: {str(e)}"

# Submit handler
def handle_submit(message):
    """
    Submit handler with RAG implementation
    """
    with st.spinner('Analyzing your data...'):
        if neo4j_available:
            # Perform vector search
            vector_results = vector_search(message, top_k=2)
            
            # Perform Cypher search
            cypher_results = cypher_search(message)
            
            # Combine results (prioritize vector results)
            all_results = vector_results + cypher_results
        else:
            all_results = []
        
        # Generate response
        response = generate_response(message, all_results)
        
        # Display response
        write_message('assistant', response)

# Display messages in Session State
for message in st.session_state.messages:
    write_message(message['role'], message['content'], save=False)

# Handle any user input
if question := st.chat_input("Ask about your FMCG data..."):
    # Display user message in chat message container
    write_message('user', question)

    # Generate a response
    handle_submit(question)
