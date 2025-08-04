#!/usr/bin/env python3
"""
Comprehensive test battery for the hybrid query detection fix.
Tests all query types to ensure NO REGRESSION.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from solutions.tools.cypher import generate_dynamic_cypher_query

def test_query_detection():
    """Test all query types to ensure no regression"""
    
    print("🧪 TESTING HYBRID QUERY DETECTION - NO REGRESSION CHECK")
    print("=" * 60)
    
    # Test cases with expected behavior
    test_cases = [
        # 1. SPECIFIC SKU QUERIES (should work as before)
        {
            "query": "Tell me about SKU001",
            "expected": "specific_sku",
            "description": "Single SKU detection"
        },
        {
            "query": "What is the price of SKU002?",
            "expected": "specific_sku", 
            "description": "Single SKU with question"
        },
        {
            "query": "Show me SKU003 and SKU004",
            "expected": "multi_sku",
            "description": "Multiple SKUs"
        },
        
        # 2. ALL SKUS QUERIES (should now be detected)
        {
            "query": "What SKUs are in the Master Data?",
            "expected": "all_skus",
            "description": "All SKUs - direct"
        },
        {
            "query": "Show me all SKUs",
            "expected": "all_skus", 
            "description": "All SKUs - show me"
        },
        {
            "query": "List all products",
            "expected": "all_skus",
            "description": "All SKUs - list products"
        },
        {
            "query": "Display every SKU",
            "expected": "all_skus",
            "description": "All SKUs - display every"
        },
        {
            "query": "Which SKUs do we have?",
            "expected": "all_skus",
            "description": "All SKUs - which"
        },
        
        # 3. ANALYTICAL QUERIES (should still use LLM)
        {
            "query": "What if we increase the price of SKU001 by 10%?",
            "expected": "analytical",
            "description": "WHAT IF analysis"
        },
        {
            "query": "Which SKUs have negative gross profit?",
            "expected": "analytical",
            "description": "Analytical query"
        },
        {
            "query": "Show me the top 3 most profitable SKUs",
            "expected": "analytical", 
            "description": "Analytical ranking"
        },
        {
            "query": "What is the average lead time by category?",
            "expected": "analytical",
            "description": "Analytical aggregation"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        print(f"\n🔍 Test {i}: {description}")
        print(f"   Query: '{query}'")
        
        try:
            # Generate the Cypher query
            cypher_query = generate_dynamic_cypher_query(query)
            
            # Determine actual behavior based on query characteristics
            if "WHERE toUpper(sku.sku_id) = '" in cypher_query:
                actual = "specific_sku"
            elif "WHERE toUpper(sku.sku_id) IN [" in cypher_query:
                actual = "multi_sku"
            elif "ORDER BY sku.sku_id" in cypher_query and "category" in cypher_query:
                actual = "all_skus"
            else:
                actual = "analytical"
            
            # Check if behavior matches expectation
            if actual == expected:
                print(f"   ✅ PASS: Expected {expected}, got {actual}")
                print(f"   Query: {cypher_query}")
                passed += 1
            else:
                print(f"   ❌ FAIL: Expected {expected}, got {actual}")
                print(f"   Query: {cypher_query}")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - NO REGRESSION!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - POTENTIAL REGRESSION!")
        return False

if __name__ == "__main__":
    success = test_query_detection()
    sys.exit(0 if success else 1) 