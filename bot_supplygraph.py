#!/usr/bin/env python3
"""
SupplyGraph Chatbot - Streamlit Application

This is a specialized chatbot for analyzing the SupplyGraph benchmark dataset,
providing comprehensive supply chain planning and analysis capabilities.
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from llm import get_llm
from monitoring import record_event, timeit
from solutions.graph import get_graph
from solutions.tools.cypher_supplygraph import (
    enhanced_cypher_qa, get_dashboard_data, get_product_details,
    get_products_by_group, get_products_by_subgroup, get_products_by_plant,
    get_products_by_storage, get_production_data, get_sales_data,
    get_group_statistics, get_subgroup_statistics, get_plant_statistics,
    get_storage_statistics, get_related_products, search_products
)

# Page configuration
st.set_page_config(
    page_title="SupplyGraph Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"supplygraph_{os.getpid()}_{id(st.session_state)}"

def display_header():
    """Display the main header"""
    st.markdown('<h1 class="main-header">📊 SupplyGraph Analyst</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-powered supply chain analysis using the SupplyGraph benchmark dataset</p>', unsafe_allow_html=True)

def display_dataset_info():
    """Display information about the SupplyGraph dataset"""
    with st.expander("📋 About SupplyGraph Dataset", expanded=False):
        st.markdown("""
        **SupplyGraph** is a comprehensive benchmark dataset for supply chain planning and analysis, featuring:
        
        - **40 Products** with codes like SOS008L02P, POV005L04P, etc.
        - **5 Product Groups** (S, P, A, M, E) for high-level categorization
        - **19 Product Subgroups** (SOS, POV, POP, AT, MAR, etc.) for detailed classification
        - **25 Manufacturing Plants** (1911, 1916, 1917, 1919, 1920, 1921, 2111, 2114, 2116, 2117, 2119, 2120, 2121)
        - **13 Storage Locations** (1130.0, 1430.0, 1630.0, 1730.0, 1930.0, 2030.0, 2130.0)
        - **Time Series Data** including Production, Sales Order, Factory Issue, and Delivery to Distributor (both Unit and Weight measurements)
        
        This dataset enables comprehensive supply chain analysis including production planning, inventory management, demand forecasting, and network optimization.
        """)

def display_quick_actions():
    """Display quick action buttons"""
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Create a comprehensive supply chain dashboard"})
            st.session_state.messages.append({"role": "assistant", "content": "I'll generate a comprehensive dashboard for you..."})
            st.rerun()
    
    with col2:
        if st.button("🏭 Plant Analysis", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Analyze plant utilization and production capacity"})
            st.session_state.messages.append({"role": "assistant", "content": "I'll analyze plant utilization for you..."})
            st.rerun()
    
    with col3:
        if st.button("📦 Product Overview", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Show me an overview of all products and their categorization"})
            st.session_state.messages.append({"role": "assistant", "content": "I'll provide a product overview..."})
            st.rerun()
    
    with col4:
        if st.button("📈 Time Series", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Analyze time series data for production and sales patterns"})
            st.session_state.messages.append({"role": "assistant", "content": "I'll analyze time series patterns..."})
            st.rerun()

def display_sample_queries():
    """Display sample queries for users to try"""
    st.markdown("### 💡 Sample Queries")
    
    sample_queries = [
        "How many products are in Group S?",
        "Which plant produces the most products?",
        "Show me production data for SOS008L02P",
        "What are the storage locations for products in subgroup POV?",
        "Find products related to POV005L04P",
        "Analyze sales patterns across different groups",
        "Which storage location has the highest product diversity?",
        "Show me time series data for production trends"
    ]
    
    cols = st.columns(2)
    for i, query in enumerate(sample_queries):
        col = cols[i % 2]
        if col.button(query, key=f"sample_{i}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()

def process_user_message(message: str) -> str:
    """Process user message and generate response"""
    try:
        with timeit("supplygraph.response", {"message_length": len(message)}):
            # Use the enhanced Cypher Q&A for SupplyGraph
            response = enhanced_cypher_qa(message)
            return response
    except Exception as e:
        record_event("supplygraph.error", {"error": str(e), "message": message})
        return f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your question or ask about a different aspect of the SupplyGraph dataset."

def display_chat_interface():
    """Display the main chat interface"""
    st.markdown("### 💬 SupplyGraph Analysis Chat")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about the SupplyGraph dataset..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing SupplyGraph data..."):
                response = process_user_message(prompt)
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def display_sidebar():
    """Display sidebar with additional information and controls"""
    with st.sidebar:
        st.markdown("### 📊 Dataset Statistics")
        
        # Get basic statistics
        try:
            print("🔍 DEBUG: SupplyGraph bot - checking data availability...")
            product_count = len(get_product_overview())
            group_stats = get_group_statistics()
            plant_stats = get_plant_statistics()
            storage_stats = get_storage_statistics()
            
            print(f"🔍 DEBUG: SupplyGraph bot - Found {product_count} products, {len(group_stats)} groups, {len(plant_stats)} plants, {len(storage_stats)} storage locations")
            
            st.metric("Products", product_count)
            st.metric("Groups", len(group_stats))
            st.metric("Plants", len(plant_stats))
            st.metric("Storage Locations", len(storage_stats))
            
            if product_count > 0:
                st.success(f"✅ SupplyGraph dataset loaded successfully!")
            else:
                st.warning("⚠️ No SupplyGraph data found in database")
            
        except Exception as e:
            print(f"❌ DEBUG: SupplyGraph bot - Error loading statistics: {e}")
            st.error(f"Error loading statistics: {e}")
        
        st.markdown("---")
        
        st.markdown("### 🔧 Tools")
        
        # Quick search
        search_term = st.text_input("Search Products", placeholder="e.g., SOS, POV")
        if search_term:
            try:
                results = search_products(search_term)
                if results:
                    st.markdown("**Search Results:**")
                    for result in results[:5]:  # Show first 5 results
                        st.write(f"- {result['product_code']} ({result['group']}/{result['subgroup']})")
                else:
                    st.write("No products found")
            except Exception as e:
                st.error(f"Search error: {e}")
        
        st.markdown("---")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        # Export chat button
        if st.button("📥 Export Chat", use_container_width=True):
            if st.session_state.messages:
                chat_text = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
                st.download_button(
                    label="Download Chat",
                    data=chat_text,
                    file_name="supplygraph_chat.txt",
                    mime="text/plain"
                )

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Display dataset information
    display_dataset_info()
    
    # Create two columns for layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Display quick actions
        display_quick_actions()
        
        # Display sample queries
        display_sample_queries()
        
        # Display chat interface
        display_chat_interface()
    
    with col2:
        # Display sidebar
        display_sidebar()

if __name__ == "__main__":
    main()
