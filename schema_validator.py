#!/usr/bin/env python3
"""
Schema Validator for Dashboard Compatibility

This module provides schema validation functions that can be integrated into the dashboard
to ensure data compatibility and provide helpful error messages.

USAGE:
    # Basic usage in Python
    from schema_validator import integrate_with_dashboard, get_dashboard_status
    
    # Validate and display in Streamlit
    dashboard_ready = integrate_with_dashboard()
    
    # Get status programmatically
    status = get_dashboard_status()
    print(f"Dashboard ready: {status['dashboard_ready']}")

COMMAND LINE:
    python schema_validator.py  # Test the validator and show current status

INTEGRATION:
    # Add to dashboard startup (dashboard_component.py)
    from schema_validator import integrate_with_dashboard
    
    # Validate schema before loading data
    dashboard_ready = integrate_with_dashboard()
    if not dashboard_ready:
        st.error("Dashboard cannot be displayed due to schema issues")
        st.stop()

FEATURES:
- Real-time schema validation with helpful error messages
- Data summary display in dashboard sidebar
- Automatic recommendations for fixing issues
- Dashboard compatibility checking
- User-friendly error reporting

REQUIREMENTS:
- Neo4j database connection (configured in .streamlit/secrets.toml)
- Streamlit (for dashboard integration)
- Python 3.7+
- langchain_neo4j package

TROUBLESHOOTING:
- If validation fails, check database connection and schema
- If dashboard doesn't load, run migration to fix schema issues
- If errors persist, check .streamlit/secrets.toml credentials
"""

import streamlit as st
from typing import Dict, List, Any, Optional
import sys
import os
sys.path.append('.')
from unified_data_model import validate_dashboard_compatibility, SchemaValidationResult, get_neo4j_config

class DashboardSchemaValidator:
    """
    Schema validator specifically designed for dashboard integration.
    Provides user-friendly error messages and suggestions.
    """
    
    @staticmethod
    def validate_and_display():
        """
        Validate the current database schema and display results in Streamlit.
        This should be called at the start of the dashboard to ensure compatibility.
        """
        st.sidebar.markdown("## 🔍 Schema Validation")
        
        # Run validation
        result = validate_dashboard_compatibility()
        
        if result.is_valid:
            st.sidebar.success("✅ Schema Valid")
            st.sidebar.info(f"📊 {result.node_count} Products")
            st.sidebar.info(f"🔗 {result.relationship_count} Relationships")
            
            if result.warnings:
                st.sidebar.warning("⚠️ Schema Warnings")
                for warning in result.warnings:
                    st.sidebar.text(f"• {warning}")
            
            return True
        else:
            st.sidebar.error("❌ Schema Invalid")
            
            # Display specific errors
            for error in result.errors:
                st.sidebar.error(f"• {error}")
            
            # Provide helpful suggestions
            st.sidebar.markdown("### 🔧 Suggested Fixes:")
            
            if "No Product nodes found" in str(result.errors):
                st.sidebar.markdown("""
                **No Product Data Found:**
                - Use the standardized ingestion script to load data
                - Run: `python standardized_ingestion.py --file your_data.xlsx`
                - Or migrate existing SKU data: `python standardized_ingestion.py --migrate`
                """)
            
            if "Dashboard query failed" in str(result.errors):
                st.sidebar.markdown("""
                **Schema Incompatible:**
                - The database schema doesn't match dashboard expectations
                - Run schema migration: `python standardized_ingestion.py --migrate`
                - Or re-ingest data using the standardized script
                """)
            
            if result.warnings:
                st.sidebar.warning("⚠️ Additional Warnings:")
                for warning in result.warnings:
                    st.sidebar.text(f"• {warning}")
            
            return False
    
    @staticmethod
    def get_validation_status() -> Dict[str, Any]:
        """
        Get validation status without displaying anything.
        Useful for programmatic checks.
        """
        result = validate_dashboard_compatibility()
        
        return {
            'is_valid': result.is_valid,
            'node_count': result.node_count,
            'relationship_count': result.relationship_count,
            'errors': result.errors,
            'warnings': result.warnings,
            'can_display_dashboard': result.is_valid and result.node_count > 0
        }
    
    @staticmethod
    def display_data_summary():
        """
        Display a summary of the current data in the sidebar.
        """
        result = validate_dashboard_compatibility()
        
        if result.is_valid and result.node_count > 0:
            st.sidebar.markdown("## 📊 Data Summary")
            
            # Get additional statistics
            try:
                from solutions.graph import get_graph
                graph = get_graph()
                
                # Get category breakdown
                categories = graph.query("""
                    MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
                    RETURN c.name as category, count(p) as count
                    ORDER BY count DESC
                """)
                
                if categories:
                    st.sidebar.markdown("### 📈 Categories:")
                    for cat in categories[:5]:  # Show top 5
                        st.sidebar.text(f"• {cat['category']}: {cat['count']}")
                
                # Get financial summary
                financial = graph.query("""
                    MATCH (p:Product)
                    WHERE p.annual_revenue IS NOT NULL
                    RETURN 
                        sum(p.annual_revenue) as total_revenue,
                        avg(p.gross_margin_pct) as avg_margin,
                        count(p) as products_with_financials
                """)
                
                if financial and financial[0]['total_revenue']:
                    revenue = financial[0]['total_revenue']
                    margin = financial[0]['avg_margin']
                    st.sidebar.markdown("### 💰 Financial Summary:")
                    st.sidebar.text(f"• Total Revenue: ${revenue:,.0f}")
                    st.sidebar.text(f"• Avg Margin: {margin:.1f}%")
                    st.sidebar.text(f"• Products with Financials: {financial[0]['products_with_financials']}")
                
            except Exception as e:
                st.sidebar.warning(f"Could not load detailed statistics: {e}")
    
    @staticmethod
    def check_dashboard_requirements() -> bool:
        """
        Check if the database meets minimum requirements for dashboard display.
        Returns True if dashboard can be displayed, False otherwise.
        """
        result = validate_dashboard_compatibility()
        
        # Minimum requirements for dashboard
        requirements_met = (
            result.is_valid and 
            result.node_count > 0 and
            not any("No Product nodes found" in error for error in result.errors)
        )
        
        return requirements_met

def integrate_with_dashboard():
    """
    Integration function to be called at the start of the dashboard.
    This ensures schema validation and provides helpful feedback.
    """
    # Validate schema
    is_valid = DashboardSchemaValidator.validate_and_display()
    
    # Display data summary if valid
    if is_valid:
        DashboardSchemaValidator.display_data_summary()
    
    # Return whether dashboard can be displayed
    return DashboardSchemaValidator.check_dashboard_requirements()

def get_dashboard_status() -> Dict[str, Any]:
    """
    Get comprehensive dashboard status for programmatic use.
    """
    validation_status = DashboardSchemaValidator.get_validation_status()
    
    return {
        **validation_status,
        'dashboard_ready': validation_status['can_display_dashboard'],
        'recommendations': _get_recommendations(validation_status)
    }

def _get_recommendations(status: Dict[str, Any]) -> List[str]:
    """Get recommendations based on validation status"""
    recommendations = []
    
    if not status['is_valid']:
        if "No Product nodes found" in str(status['errors']):
            recommendations.append("Load data using standardized ingestion script")
            recommendations.append("Run: python standardized_ingestion.py --file your_data.xlsx")
        
        if "Dashboard query failed" in str(status['errors']):
            recommendations.append("Migrate existing data to compatible schema")
            recommendations.append("Run: python standardized_ingestion.py --migrate")
    
    if status['node_count'] == 0:
        recommendations.append("No product data available - load data first")
    
    if status['warnings']:
        recommendations.append("Consider addressing schema warnings for optimal performance")
    
    return recommendations

# Example usage in dashboard
if __name__ == "__main__":
    """
    Test the schema validator and show current database status.
    
    This script will:
    1. Connect to the Neo4j database
    2. Validate the schema for dashboard compatibility
    3. Display detailed status and recommendations
    
    EXPECTED OUTPUT:
        Dashboard Ready: True
        Products: 2000
        Relationships: 8034
        
    If you see errors, check:
    1. .streamlit/secrets.toml file exists and has correct credentials
    2. Neo4j database is accessible
    3. Database contains Product nodes with required fields
    """
    print("🔍 Testing Schema Validator...")
    print("=" * 50)
    
    status = get_dashboard_status()
    print(f"Dashboard Ready: {'✅ Yes' if status['dashboard_ready'] else '❌ No'}")
    print(f"Products: {status['node_count']}")
    print(f"Relationships: {status['relationship_count']}")
    
    if status['errors']:
        print(f"\n❌ Errors found:")
        for error in status['errors']:
            print(f"  - {error}")
    
    if status['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in status['warnings']:
            print(f"  - {warning}")
    
    if status['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in status['recommendations']:
            print(f"  - {rec}")
    
    if status['dashboard_ready']:
        print(f"\n✅ Database is ready for dashboard use!")
    else:
        print(f"\n❌ Database needs attention before dashboard can work properly.")
        print("\nTROUBLESHOOTING:")
        print("1. Run: python standardized_ingestion.py --validate")
        print("2. Run: python standardized_ingestion.py --migrate (if needed)")
        print("3. Check .streamlit/secrets.toml credentials")
        print("4. Verify Neo4j database is accessible")
