import streamlit as st

# Page Config - MUST be called first
st.set_page_config(
    page_title="FMCG Supply Chain Assistant",
    page_icon="📊",
    layout="wide"
)

from solutions.agent import generate_response, reset_agent
from solutions.graph import get_graph
from dashboard_component import render_dashboard, generate_dashboard_response
import os

print("🔍 DEBUG: bot.py starting...")

# Import all required modules
try:
    from solutions.tools.cypher import enhanced_cypher_qa
    from solutions.tools.vector import get_sku_data
    from solutions.tools.data_parser import parse_sku_data
    print("🔍 DEBUG: All imports completed successfully")
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "neo4j_available" not in st.session_state:
    st.session_state.neo4j_available = False
if "data_available" not in st.session_state:
    st.session_state.data_available = False
if "message_count" not in st.session_state:
    st.session_state.message_count = 0

print("🔍 DEBUG: Session state initialized")

# Title and description
st.title("🤖 FMCG Supply Chain Assistant")
st.markdown("""
This AI assistant helps you analyze FMCG (Fast Moving Consumer Goods) supply chain data, 
including SKU information, inventory levels, demand forecasts, and financial metrics.
""")

# Sidebar for controls
with st.sidebar:
    st.header("🔧 Controls")
    
    # Check Neo4j availability
    print("🔍 DEBUG: Checking Neo4j availability...")
    try:
        graph = get_graph()
        neo4j_available = graph is not None
        print(f"🔍 DEBUG: Neo4j available: {neo4j_available}")
        st.session_state.neo4j_available = neo4j_available
    except Exception as e:
        print(f"❌ DEBUG: Neo4j connection error: {e}")
        neo4j_available = False
        st.session_state.neo4j_available = False
    
    if neo4j_available:
        st.success("✅ Neo4j Database Connected")
        
        # Check data availability
        print("🔍 DEBUG: check_data_available() called")
        try:
            result = graph.query("MATCH (sku:SKU) RETURN count(sku) as count")
            count = result[0]['count'] if result else 0
            print(f"🔍 DEBUG: Found {count} SKU nodes in database")
            
            data_available = count > 0
            print(f"🔍 DEBUG: Data available: {data_available}")
            st.session_state.data_available = data_available
            
            if data_available:
                st.success(f"✅ {count} SKU records available")
            else:
                st.warning("⚠️ No SKU data found in database")
        except Exception as e:
            print(f"❌ DEBUG: Data check error: {e}")
            st.error(f"❌ Error checking data: {e}")
            data_available = False
            st.session_state.data_available = False
    else:
        st.error("❌ Neo4j Database Not Available")
        st.info("Please check your database connection settings.")
    
    # Reset button
    if st.button("🔄 Reset Agent"):
        reset_agent()
        st.success("Agent reset successfully!")
        st.rerun()  # Force a complete page reload to clear all caches
    
    # Example queries
    st.header("💡 Example Queries")
    st.markdown("""
    Try these example queries:
    
    **Dashboard & Analytics:**
    - "Show me a dashboard"
    - "Generate a report"
    - "Create charts and graphs"
    - "Display analytics"
    - "Show me KPIs"
    
    **SKU Information:**
    - "Tell me about SKU001"
    - "What SKUs are in the Master Data?"
    - "Show me all SKUs"
    
    **Analytics:**
    - "Which categories do we have?"
    - "What is our demand plan for SKU001?"
    - "Show me products with highest revenue"
    
    **Inventory:**
    - "What is the inventory level for SKU001?"
    - "Which SKUs have negative gross profit?"
    
    **Enhanced Data (100 SKUs):**
    - "Show me supply chain gaps"
    - "Which SKUs have supply issues?"
    - "Display inventory trends"
    - "Analyze seasonal patterns"
    """)

# Main chat interface
st.header("💬 Chat with the Assistant")

# Force agent reset on first load to ensure we use the updated agent
if "agent_initialized" not in st.session_state:
    reset_agent()
    st.session_state.agent_initialized = True
    print("🔍 DEBUG: Agent initialized for first time")

# Display chat messages
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Re-render dashboard if this was a dashboard message
        if (message["role"] == "assistant" and 
            st.session_state.get('show_dashboard', False) and
            st.session_state.get('dashboard_data', {}).get('timestamp') == i):
            render_dashboard()

# Chat input
if prompt := st.chat_input("Ask about your FMCG supply chain data..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.message_count += 1
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Check if we have the required infrastructure
        if not st.session_state.neo4j_available:
            message_placeholder.error("❌ Database connection not available. Please check your configuration.")
        elif not st.session_state.data_available:
            message_placeholder.warning("⚠️ No data available in the database. Please check your data ingestion.")
        else:
            try:
                print(f"🔍 DEBUG: handle_submit() called with message: {prompt[:50]}...")
                
                # Check if user is requesting a dashboard
                dashboard_keywords = ['dashboard', 'chart', 'graph', 'visualization', 'report', 'analytics', 'metrics', 'kpi']
                is_dashboard_request = any(keyword in prompt.lower() for keyword in dashboard_keywords)
                
                if is_dashboard_request:
                    print("🔍 DEBUG: Dashboard request detected")
                    
                    # Generate dashboard response text
                    dashboard_text = generate_dashboard_response()
                    message_placeholder.markdown(dashboard_text)
                    
                    # Store dashboard state in session
                    st.session_state.show_dashboard = True
                    st.session_state.dashboard_data = {
                        'text': dashboard_text,
                        'timestamp': st.session_state.get('message_count', 0)
                    }
                    
                    # Render the interactive dashboard
                    render_dashboard()
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": dashboard_text})
                    st.session_state.message_count += 1
                    
                else:
                    # SUPERVISOR: Suggest query improvements if needed
                    try:
                        from solutions.supervisor import supervisor
                        query_suggestion = supervisor.suggest_query_improvements(prompt)
                        if query_suggestion:
                            st.info(f"💡 **Query Suggestion**: {query_suggestion}")
                    except Exception as e:
                        print(f"🔍 DEBUG: Query suggestion failed: {e}")
                    
                    print("🔍 DEBUG: Calling generate_response...")
                    response = generate_response(prompt)
                    print(f"🔍 DEBUG: generate_response returned: {response[:100]}...")
                    
                    # Display the response
                    message_placeholder.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.message_count += 1
                
            except Exception as e:
                error_msg = f"❌ Error processing your request: {str(e)}"
                message_placeholder.error(error_msg)
                print(f"❌ DEBUG: Error in chat: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Built with Streamlit, LangChain, and Neo4j</p>
</div>
""", unsafe_allow_html=True)
