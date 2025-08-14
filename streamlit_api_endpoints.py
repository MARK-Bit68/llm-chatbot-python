# Add this to your bot.py to create API endpoints for React

import streamlit as st
from streamlit.web import cli as stcli
import sys
import json
from urllib.parse import urlparse, parse_qs

# API endpoint handler for React frontend
def handle_api_request():
    """Handle API requests from React frontend"""
    
    # Get query parameters from URL
    query_params = st.experimental_get_query_params()
    
    # Check if this is an API request
    if 'api' in query_params:
        api_endpoint = query_params['api'][0]
        
        if api_endpoint == 'chat':
            # Handle chat API request
            message = query_params.get('message', [''])[0]
            if message:
                from solutions.agent import generate_response
                response = generate_response(message)
                
                # Return JSON response
                st.json({
                    "response": response,
                    "timestamp": str(datetime.now()),
                    "status": "success"
                })
                return True
                
        elif api_endpoint == 'dashboard':
            # Handle dashboard data request
            from dashboard_component import generate_dashboard_response
            dashboard_data = generate_dashboard_response()
            
            st.json({
                "data": dashboard_data,
                "timestamp": str(datetime.now()),
                "status": "success"
            })
            return True
            
        elif api_endpoint == 'health':
            # Health check endpoint
            st.json({
                "status": "healthy",
                "timestamp": str(datetime.now()),
                "services": {
                    "neo4j": st.session_state.get('neo4j_available', False),
                    "data": st.session_state.get('data_available', False)
                }
            })
            return True
    
    return False

# Add this at the top of your main app logic in bot.py
if handle_api_request():
    st.stop()  # Stop normal Streamlit rendering for API requests

# Rest of your existing bot.py code continues normally...