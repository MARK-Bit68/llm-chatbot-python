#!/usr/bin/env python3
"""
Simple test script for new AI Enhanced SOP queries
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_new_queries():
    """Test the new query system"""
    try:
        logger.info("🔍 Testing new AI Enhanced SOP queries...")
        
        # Test basic imports
        from solutions.tools.cypher_ai_enhanced_sop import (
            get_dashboard_data, get_product_overview, get_category_performance
        )
        
        logger.info("✅ Import successful")
        
        # Test dashboard data
        dashboard = get_dashboard_data()
        logger.info(f"📊 Dashboard data: {dashboard}")
        
        # Test product overview
        products = get_product_overview()
        logger.info(f"🛍️ Products: {len(products)} found")
        if products:
            logger.info(f"   Sample: {products[0]}")
        
        # Test category performance
        categories = get_category_performance()
        logger.info(f"📊 Categories: {len(categories)} found")
        if categories:
            logger.info(f"   Sample: {categories[0]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_new_queries()
    if success:
        logger.info("✅ New query system working!")
        sys.exit(0)
    else:
        logger.error("❌ New query system failed!")
        sys.exit(1)