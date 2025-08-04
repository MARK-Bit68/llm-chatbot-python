import streamlit as st

# Page Config - MUST be called first
st.set_page_config("FMCG RAG Chatbot", page_icon=":chart_with_upwards_trend:")

print("🔍 DEBUG: bot.py starting...")

from utils import write_message
from solutions.agent import generate_response
from graph import get_graph_instance

print("🔍 DEBUG: All imports completed successfully")

# Set up Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I'm your FMCG S&OP RAG Chatbot! I can help you analyze your supply chain data. How can I assist you today?"},
    ]

# Initialize sample questions in session state
if "sample_questions" not in st.session_state:
    st.session_state.sample_questions = []

# Initialize selected question in session state
if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

print("🔍 DEBUG: Session state initialized")

# Default sample questions for new users
default_questions = [
    # Basic SKU Information
    "What SKUs are in the Master Data?",
    "Tell me about SKU001",
    "What is the category of SKU001?",
    "Which countries are our products from?",
    
    # Financial Analysis
    "What is the price range of our products?",
    "Show me products with highest profit margins",
    "Which products have the lowest unit costs?",
    "What is the average profit margin across all products?",
    "Show me products with profit margins above 50%",
    
    # Supply Chain Analysis
    "What is the inventory plan for SKU001?",
    "Show me the demand plan for SKU001",
    "What are the financial details for SKU001?",
    "Tell me about our supply chain operations",
    "Which products have the longest lead times?",
    "What is the average lead time across all products?",
    
    # Category and Market Analysis
    "What categories of products do we have?",
    "How many products are in each category?",
    "Which category has the highest average price?",
    "Show me products by country",
    "What is the price distribution by category?",
    
    # Advanced Analytics
    "Show me products with the best cost-to-price ratio",
    "Which products have the highest revenue potential?",
    "What is the total value of our inventory?",
    "Show me products with lead times over 20 days",
    "Which products have the highest and lowest profit margins?",
    
    # Specific Product Analysis
    "Tell me about SKU003",
    "What are the financial metrics for SKU005?",
    "Show me all details for SKU004",
    "What is the supply chain plan for SKU002?",
    
    # Comparative Analysis
    "Compare SKU001 and SKU003",
    "Show me the top 5 most profitable products",
    "Which products have similar pricing strategies?",
    "What is the price difference between highest and lowest priced products?"
]

# Check Neo4j status
print("🔍 DEBUG: Checking Neo4j availability...")
neo4j_available = get_graph_instance() is not None
print(f"🔍 DEBUG: Neo4j available: {neo4j_available}")

def check_data_available():
    """Check if there's data in the database to query"""
    print("🔍 DEBUG: check_data_available() called")
    if not neo4j_available:
        print("⚠️ DEBUG: Neo4j not available")
        return False
    
    try:
        # Check if there are any SKU nodes in the database
        graph = get_graph_instance()
        if graph is None:
            print("⚠️ DEBUG: Graph instance is None")
            return False
        result = graph.query("MATCH (sku:SKU) RETURN count(sku) as count")
        count = result[0]['count'] if result else 0
        print(f"🔍 DEBUG: Found {count} SKU nodes in database")
        return count > 0
    except Exception as e:
        print(f"❌ DEBUG: Error checking data availability: {e}")
        return False

# Check if data is available
print("🔍 DEBUG: Checking data availability...")
data_available = check_data_available()
print(f"🔍 DEBUG: Data available: {data_available}")

# Sidebar for data upload
with st.sidebar:
    st.header("📊 Data Management")
    
    if neo4j_available:
        # Data status indicator
        st.subheader("📊 Data Status")
        if data_available:
            try:
                result = get_graph_instance().query("MATCH (sku:SKU) RETURN count(sku) as count")
                count = result[0]['count'] if result else 0
                st.success(f"✅ Data available: {count} SKUs loaded")
            except Exception as e:
                st.error(f"❌ Error checking data: {e}")
        else:
            st.warning("⚠️ No data available")
            st.info("Process data to enable chat functionality")
        
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
        
        # Display clickable sample questions if available
        if st.session_state.sample_questions:
            st.subheader("📋 Sample Questions to Try")
            if data_available:
                st.info("💡 Click any question below to automatically ask it:")
                
                for i, question in enumerate(st.session_state.sample_questions[:10], 1):
                    # Create a button for each question with better styling
                    if st.button(f"❓ {question}", key=f"question_{i}", help=f"Click to ask: {question}", use_container_width=True):
                        st.session_state.selected_question = question
                        st.rerun()
            else:
                st.warning("⚠️ No data available. Process some data first to enable questions.")
                st.info("Use the 'Quick Test' or 'Process Full Dataset' buttons above to load data.")
        else:
            # Show default questions for new users
            st.subheader("📋 Try These Questions")
            if data_available:
                st.info("💡 Click any question below to automatically ask it:")
                
                for i, question in enumerate(default_questions, 1):
                    # Create a button for each default question with better styling
                    if st.button(f"❓ {question}", key=f"default_question_{i}", help=f"Click to ask: {question}", use_container_width=True):
                        st.session_state.selected_question = question
                        st.rerun()
            else:
                st.warning("⚠️ No data available. Process some data first to enable questions.")
                st.info("Use the 'Quick Test' or 'Process Full Dataset' buttons above to load data.")
        
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
        
        # Try to get existing index
        try:
            neo4jvector = Neo4jVector.from_existing_index(
                embeddings,
                graph=get_graph_instance(),
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
        except ValueError as e:
            if "does not exist" in str(e):
                st.warning("Vector index not available. Please load data and create the vector index first.")
                return []
            else:
                raise e
        
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
        
        results = get_graph_instance().query(cypher_query, {'query': query})
        return results
    except Exception as e:
        st.error(f"Cypher search error: {e}")
        return []

# Submit handler

def handle_submit(message):
    """
    Handle user message submission
    """
    print(f"🔍 DEBUG: handle_submit() called with message: {message[:50]}...")
    
    try:
        print("🔍 DEBUG: Calling generate_response...")
        response = generate_response(message)
        print(f"🔍 DEBUG: generate_response returned: {response[:100]}...")
        return response
    except Exception as e:
        print(f"❌ DEBUG: Error in handle_submit: {e}")
        return f"Error: {str(e)}"

# Display messages in Session State
for message in st.session_state.messages:
    write_message(message['role'], message['content'], save=False)

# Handle any user input
if question := st.chat_input("Ask about your FMCG data..."):
    # Clear the selected question after it's used
    st.session_state.selected_question = ""
    
    # Check if data is available before processing
    if not data_available:
        write_message('assistant', "⚠️ No data available to query. Please process some data first using the sidebar options.")
    else:
        # Display user message in chat message container
        write_message('user', question)

        # Generate a response and display it
        response = handle_submit(question)
        write_message('assistant', response)

# Handle selected question from sidebar
if st.session_state.selected_question:
    # Check if data is available before processing
    if not data_available:
        write_message('assistant', "⚠️ No data available to query. Please process some data first using the sidebar options.")
    else:
        # Display user message in chat message container
        write_message('user', st.session_state.selected_question)

        # Generate a response and display it
        response = handle_submit(st.session_state.selected_question)
        write_message('assistant', response)
    
    # Clear the selected question after it's used
    st.session_state.selected_question = ""
