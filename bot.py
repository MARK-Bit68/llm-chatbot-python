import streamlit as st
from ui_theme import apply_global_theme

# Page Config - MUST be called first
st.set_page_config(
    page_title="FMCG Supply Chain Assistant",
    page_icon="📊",
    layout="wide"
)

# Apply global theme early
apply_global_theme()

from solutions.agent import generate_response, reset_agent
from solutions.graph import get_graph
from dashboard_component import render_dashboard, generate_dashboard_response
import os
from monitoring import enable_monitoring, render_debug_panel, record_event, clear_trace
from llm import get_openai_model

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
st.title("🤖 S&OP Supply Chain Assistant")
st.markdown("""
This AI assistant helps you analyze S&OP (Sales & Operations Planning) supply chain scenarios, 
including manufacturing capacity constraints, customer prioritization, regional demand variations, 
promotional impact, and cross-functional planning between Sales, Demand, and Supply Planning.
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
    
    # Model selection
    available_models = [
        "gpt-4.1-nano",
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-5-nano",
    ]
    current_model = st.session_state.get("selected_model", get_openai_model())
    selected = st.selectbox("Model", options=available_models, index=max(0, available_models.index(current_model)) if current_model in available_models else 0)
    model_changed = selected != st.session_state.get("selected_model")
    if model_changed:
        st.session_state["selected_model"] = selected
        record_event("model.changed", {"model": selected})
        reset_agent()  # ensure new LLM is used
        st.toast(f"Model switched to {selected}")

    # Monitoring toggle
    monitoring_on = st.toggle("Enable monitoring", value=st.session_state.get("monitoring_enabled", False))
    enable_monitoring(monitoring_on)
    if st.button("Clear trace"):
        clear_trace()

    # Reset button
    if st.button("🔄 Reset Agent"):
        reset_agent()
        st.success("Agent reset successfully!")
        st.rerun()  # Force a complete page reload to clear all caches
    
    # Example queries (verified basics + robust analytical intents we support today)
    st.header("💡 Example Queries")
    st.markdown("""
    These prompts are verified by our sanity tests and grounded analytical intents:
    
    **Verified data-backed basics:**
    - "List the distinct product categories"
    - "What is the category of SKU001?"
    - "Tell me about SKU001"
    - "Which SKU has the highest gross profit per unit?"
    - "How many distinct categories are there?"
    - "Which country has the most SKUs?"
    
    **Analytical intents (SKU-level proxies):**
    - "Show me excess inventory for promotions"
    - "Analyze regional demand variations"
    - "Which SKUs have manufacturing constraints?"
    - "Show me lead time planning data"
    - "Which SKUs can we trim to fit within capacity limits?"
    
    Note: Customer orders, plant utilization, and capacity across plants require extending the graph schema and are not listed here yet.
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
        render_debug_panel()
        
        # Check if we have the required infrastructure
        if not st.session_state.neo4j_available:
            message_placeholder.error("❌ Database connection not available. Please check your configuration.")
        elif not st.session_state.data_available:
            message_placeholder.warning("⚠️ No data available in the database. Please check your data ingestion.")
        else:
            try:
                print(f"🔍 DEBUG: handle_submit() called with message: {prompt[:50]}...")
                record_event("user.message", {"text": prompt})
                
                # Check if user is requesting a dashboard
                dashboard_keywords = ['dashboard', 'chart', 'graph', 'visualization', 'report', 'analytics', 'metrics', 'kpi']
                is_dashboard_request = any(keyword in prompt.lower() for keyword in dashboard_keywords)
                
                if is_dashboard_request:
                    print("🔍 DEBUG: Dashboard request detected")
                    record_event("dashboard.request", {"query": prompt})
                    
                    # Generate dashboard response text
                    with st.spinner("Generating dashboard..."):
                        dashboard_text = generate_dashboard_response()
                    record_event("dashboard.response", {"length": len(dashboard_text)})
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
                            # Additional safety check to prevent internal analysis from reaching users
                            internal_analysis_phrases = [
                                'the user query', 'somewhat vague', 'assumes the user', 'does not specify',
                                'suggestions for improvement', 'more specific wording', 'alternative phrasings',
                                'related queries that might', 'clarifying what specific information',
                                'analysis', 'internal', 'debug', 'query analysis'
                            ]
                            
                            is_internal_analysis = any(phrase in query_suggestion.lower() for phrase in internal_analysis_phrases)
                            
                            if not is_internal_analysis:
                                st.info(f"💡 **Query Suggestion**: {query_suggestion}")
                            else:
                                print(f"🔍 DEBUG: Blocked internal analysis from reaching user: {query_suggestion[:50]}...")
                    except Exception as e:
                        print(f"🔍 DEBUG: Query suggestion failed: {e}")
                    
                    print("🔍 DEBUG: Calling generate_response...")
                    with st.spinner("Thinking..."):
                        response = generate_response(prompt)
                    record_event("assistant.response", {"length": len(response)})
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
                record_event("error", {"message": str(e)})

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Built with Streamlit, LangChain, and Neo4j</p>
</div>
""", unsafe_allow_html=True)
