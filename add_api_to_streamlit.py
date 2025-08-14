# Add this to the TOP of your bot.py file to create API endpoints

import streamlit as st
import json
from datetime import datetime
import urllib.parse

def handle_api_requests():
    """Handle API requests from React frontend"""
    
    # Check if this is an API request by looking at query parameters
    query_params = st.experimental_get_query_params()
    
    # Set CORS headers for all responses
    st.set_page_config(
        page_title="FMCG Supply Chain Assistant",
        page_icon="📊",
        layout="wide"
    )
    
    # Handle different API endpoints
    if 'api' in query_params:
        api_endpoint = query_params['api'][0]
        
        if api_endpoint == 'chat':
            # Handle chat API request
            message = query_params.get('message', [''])[0]
            if message:
                try:
                    # Use your existing generate_response function
                    from solutions.agent import generate_response
                    response = generate_response(urllib.parse.unquote(message))
                    
                    # Return JSON response
                    api_response = {
                        "response": response,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "source": "neo4j"
                    }
                    
                    # Display as JSON (React will parse this)
                    st.json(api_response)
                    return True
                    
                except Exception as e:
                    error_response = {
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                        "status": "error"
                    }
                    st.json(error_response)
                    return True
        
        elif api_endpoint == 'health':
            # Health check endpoint
            try:
                from solutions.graph import get_graph
                graph = get_graph()
                neo4j_available = graph is not None
                
                if neo4j_available:
                    # Test database connection
                    result = graph.query("MATCH (sku:SKU) RETURN count(sku) as count LIMIT 1")
                    sku_count = result[0]['count'] if result else 0
                    data_available = sku_count > 0
                else:
                    sku_count = 0
                    data_available = False
                
                health_response = {
                    "status": "healthy" if neo4j_available and data_available else "degraded",
                    "timestamp": datetime.now().isoformat(),
                    "services": {
                        "neo4j": neo4j_available,
                        "data": data_available,
                        "sku_count": sku_count
                    }
                }
                st.json(health_response)
                return True
                
            except Exception as e:
                error_response = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                st.json(error_response)
                return True
        
        elif api_endpoint == 'dashboard':
            # Dashboard data endpoint
            try:
                from solutions.graph import get_graph
                graph = get_graph()
                
                if graph:
                    # Get real data from Neo4j
                    sku_count_result = graph.query("MATCH (sku:SKU) RETURN count(sku) as count")
                    total_skus = sku_count_result[0]['count'] if sku_count_result else 0
                    
                    # Get categories
                    categories_result = graph.query("MATCH (sku:SKU) RETURN DISTINCT sku.category as category")
                    categories = [r['category'] for r in categories_result if r['category']]
                    
                    dashboard_response = {
                        "totalSKUs": total_skus,
                        "totalCategories": len(categories),
                        "categories": categories,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "source": "neo4j"
                    }
                else:
                    dashboard_response = {
                        "error": "Database not available",
                        "timestamp": datetime.now().isoformat(),
                        "status": "error"
                    }
                
                st.json(dashboard_response)
                return True
                
            except Exception as e:
                error_response = {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "status": "error"
                }
                st.json(error_response)
                return True
    
    return False

# Add this line to the very beginning of your bot.py main code:
# if handle_api_requests():
#     st.stop()  # Stop rendering normal Streamlit UI for API requests