import streamlit as st
from utils import write_message
from solutions.agent import generate_response
from graph import graph
from llm import embeddings

# Page Config
st.set_page_config("FMCG RAG Chatbot", page_icon=":chart_with_upwards_trend:")

# Set up Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I'm your FMCG S&OP RAG Chatbot! I can help you analyze your supply chain data. How can I assist you today?"},
    ]

# Initialize sample questions in session state
if "sample_questions" not in st.session_state:
    st.session_state.sample_questions = []

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
        
        # Quick test with configurable SKU count
        col1, col2 = st.columns([1, 2])
        with col1:
            quick_test_skus = st.number_input(
                "Number of SKUs for Quick Test",
                min_value=1,
                max_value=50,
                value=10,
                help="Number of SKUs to process for quick testing"
            )
        with col2:
            if st.button(f"🚀 Quick Test ({quick_test_skus} SKUs)"):
                with st.spinner(f"Processing {quick_test_skus} SKUs for quick test..."):
                    try:
                        from quick_ingestion_2_skus import quick_ingestion_2_skus
                        results = quick_ingestion_2_skus("FMCG S&OP Working Excel.xlsx", max_skus=quick_test_skus)
                        if 'sample_questions' in results:
                            st.success(f"✅ Processed {results['nodes_created']} SKUs with embeddings")
                            st.info("📝 Sample questions generated! Try asking about the uploaded data.")
                            # Store sample questions in session state
                            st.session_state.sample_questions = results['sample_questions']
                        else:
                            st.error(f"Error: {results.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        # Display sample questions if available
        if st.session_state.sample_questions:
            with st.expander("📋 Sample Questions to Try", expanded=True):
                for i, question in enumerate(st.session_state.sample_questions[:10], 1):
                    st.write(f"{i}. {question}")
        
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
            index_name="skuPlots",
            node_label="SKU",
            text_node_property="plot",
            embedding_node_property="plotEmbedding",
            retrieval_query="""
RETURN
    node.plot AS text,
    score,
    {
        title: node.name,
        sku_id: node.sku_id,
        tmdbId: node.sku_id,
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
                'sku.title': doc.metadata.get('title', 'Unknown'),
                'sku.plot': doc.page_content,
                'sku.sku_id': doc.metadata.get('sku_id', 'Unknown'),
                'score': doc.metadata.get('score', 0.0)
            })
        
        # Condensed debug output
        found_skus = [result.get('sku.sku_id') for result in formatted_results]
        st.info(f"🔍 Found {len(formatted_results)} results: {', '.join(found_skus)}")
        
        # Prioritize exact SKU match if query contains a specific SKU
        query_lower = query.lower()
        if 'sku' in query_lower:
            # Extract SKU number from query (e.g., "sku002" -> "SKU002")
            import re
            sku_match = re.search(r'sku(\d+)', query_lower)
            if sku_match:
                target_sku = f"SKU{sku_match.group(1).upper()}"
                # Move matching SKU to front
                exact_matches = [r for r in formatted_results if r.get('sku.sku_id') == target_sku]
                other_results = [r for r in formatted_results if r.get('sku.sku_id') != target_sku]
                formatted_results = exact_matches + other_results
                if exact_matches:
                    st.info(f"🎯 Prioritized: {target_sku}")
        
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
        MATCH (sku:SKU)
        WHERE toLower(sku.name) CONTAINS toLower($query) 
           OR toLower(sku.plot) CONTAINS toLower($query)
        RETURN sku.name, sku.plot, sku.sku_id
        LIMIT 10
        """
        
        results = graph.query(cypher_query, {'query': query})
        return results
    except Exception as e:
        st.error(f"Cypher search error: {e}")
        return []

# Submit handler

def handle_submit(message):
    """
    Submit handler with RAG implementation
    """
    with st.spinner('Analyzing your data...'):
        if neo4j_available:
            # Perform vector search
            vector_results = vector_search(message, top_k=5)
            
            # Perform Cypher search
            cypher_results = cypher_search(message)
            
            # Combine results (prioritize vector results)
            all_results = vector_results + cypher_results
        else:
            all_results = []
        
        # Generate response
        response = generate_response(message)
        
        # Debug: Print the response before displaying
        print(f"DEBUG: Final response to display: '{response}'")
        print(f"DEBUG: Response type: {type(response)}")
        print(f"DEBUG: Response length: {len(response) if response else 0}")
        
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
