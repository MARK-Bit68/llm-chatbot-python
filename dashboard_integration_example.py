#!/usr/bin/env python3
"""
Dashboard Integration Example

This example shows how to integrate the schema validator into your dashboard
to ensure data compatibility and provide helpful feedback to users.

USAGE:
    # Add this to your dashboard startup code
    from schema_validator import integrate_with_dashboard
    
    # Validate schema before loading data
    dashboard_ready = integrate_with_dashboard()
    if not dashboard_ready:
        st.error("Dashboard cannot be displayed due to schema issues")
        st.stop()

EXAMPLE INTEGRATION:
    # In your dashboard_component.py or main dashboard file
    import streamlit as st
    from schema_validator import integrate_with_dashboard
    
    # Page setup
    st.set_page_config(page_title="FMCG Analytics Dashboard", layout="wide")
    
    # Validate schema first
    dashboard_ready = integrate_with_dashboard()
    if not dashboard_ready:
        st.error("Dashboard cannot be displayed due to schema issues")
        st.stop()
    
    # Continue with dashboard if validation passes
    st.title("FMCG Analytics Dashboard")
    # ... rest of your dashboard code
"""

import streamlit as st
from schema_validator import integrate_with_dashboard, get_dashboard_status

def main():
    """
    Example dashboard with schema validation integration.
    
    This demonstrates how to:
    1. Validate schema before loading dashboard
    2. Display helpful error messages
    3. Show data summary when validation passes
    """
    
    # Page setup
    st.set_page_config(
        page_title="FMCG Analytics Dashboard - Schema Validation Example",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔍 Dashboard Integration Example")
    st.markdown("This example shows how to integrate schema validation into your dashboard.")
    
    # Validate schema first
    st.header("📊 Schema Validation")
    
    with st.spinner("Validating database schema..."):
        dashboard_ready = integrate_with_dashboard()
    
    if not dashboard_ready:
        st.error("❌ Dashboard cannot be displayed due to schema issues")
        st.markdown("""
        **Next Steps:**
        1. Run `python standardized_ingestion.py --validate` to check details
        2. Run `python standardized_ingestion.py --migrate` if needed
        3. Check database connection and credentials
        """)
        st.stop()
    
    # Dashboard content (only shown if validation passes)
    st.success("✅ Schema validation passed! Dashboard is ready.")
    
    st.header("📈 Dashboard Content")
    st.markdown("This content would only be displayed if schema validation passes.")
    
    # Get detailed status for demonstration
    status = get_dashboard_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Products", status['node_count'])
    
    with col2:
        st.metric("Relationships", status['relationship_count'])
    
    with col3:
        st.metric("Dashboard Ready", "✅ Yes" if status['dashboard_ready'] else "❌ No")
    
    # Show recommendations if any
    if status['recommendations']:
        st.header("💡 Recommendations")
        for rec in status['recommendations']:
            st.info(rec)
    
    st.header("🔧 Integration Code")
    st.code("""
# Add this to your dashboard startup
from schema_validator import integrate_with_dashboard

# Validate schema before loading data
dashboard_ready = integrate_with_dashboard()
if not dashboard_ready:
    st.error("Dashboard cannot be displayed due to schema issues")
    st.stop()

# Continue with dashboard if validation passes
st.title("Your Dashboard Title")
# ... rest of your dashboard code
    """, language="python")

if __name__ == "__main__":
    main()

