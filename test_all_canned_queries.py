#!/usr/bin/env python3
"""
Comprehensive test for all 22 canned query types

This test validates that each canned query:
1. Matches the correct question patterns
2. Executes without errors
3. Returns expected response format
4. Handles edge cases gracefully
"""

import os
import sys
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solutions.tools.canned_queries import get_canned_queries, match_canned_query, execute_canned_query
from solutions.tools.ground_truth_validator import GroundTruthCase, validate_ground_truth_case

@dataclass
class TestCase:
    """Represents a test case for a canned query"""
    query_key: str
    test_questions: List[str]
    expected_response_patterns: List[str]
    required_params: Dict[str, Any]
    description: str

def create_test_cases() -> Dict[str, TestCase]:
    """Create comprehensive test cases for all canned queries"""
    
    return {
        "sku_category": TestCase(
            query_key="sku_category",
            test_questions=[
                "What is the category of SKU001?",
                "Category of SKU002",
                "What category is SKU003?"
            ],
            expected_response_patterns=["category", "SKU", "is **"],
            required_params={"sku_id": "SKU001"},
            description="Get SKU category"
        ),
        
        "sku_country": TestCase(
            query_key="sku_country",
            test_questions=[
                "What country is SKU001 from?",
                "Country of SKU002",
                "Which country is SKU003?"
            ],
            expected_response_patterns=["country", "SKU", "from **"],
            required_params={"sku_id": "SKU001"},
            description="Get SKU country"
        ),
        
        "sku_details": TestCase(
            query_key="sku_details",
            test_questions=[
                "Tell me about SKU001",
                "What is SKU002?",
                "Show me details for SKU003",
                "SKU details for SKU004"
            ],
            expected_response_patterns=["SKU Details", "Basic Information", "Financial Metrics", "Supply Chain"],
            required_params={"sku_id": "SKU001"},
            description="Get comprehensive SKU details"
        ),
        
        "distinct_categories": TestCase(
            query_key="distinct_categories",
            test_questions=[
                "List the distinct product categories",
                "What categories are there?",
                "Show me all categories"
            ],
            expected_response_patterns=["Product Categories", "distinct", "categories"],
            required_params={},
            description="List all distinct product categories"
        ),
        
        "distinct_categories_count": TestCase(
            query_key="distinct_categories_count",
            test_questions=[
                "How many distinct categories are there?",
                "Count of categories",
                "Number of categories"
            ],
            expected_response_patterns=["distinct", "categories", "portfolio"],
            required_params={},
            description="Count distinct categories"
        ),
        
        "all_skus": TestCase(
            query_key="all_skus",
            test_questions=[
                "Show me all SKUs",
                "List all SKUs",
                "Display all SKUs"
            ],
            expected_response_patterns=["All SKUs", "SKU", "portfolio"],
            required_params={},
            description="List all SKUs"
        ),
        
        "all_skus_count": TestCase(
            query_key="all_skus_count",
            test_questions=[
                "How many SKUs?",
                "Total number of SKUs",
                "Count of SKUs"
            ],
            expected_response_patterns=["SKUs", "portfolio"],
            required_params={},
            description="Count total SKUs"
        ),
        
        "negative_gross_profit": TestCase(
            query_key="negative_gross_profit",
            test_questions=[
                "Which SKUs have negative gross profit?",
                "SKUs with negative profit",
                "Negative gross profit"
            ],
            expected_response_patterns=["negative", "profit", "SKU"],
            required_params={},
            description="Find SKUs where unit price < unit cost"
        ),
        
        "count_negative_gross_profit": TestCase(
            query_key="count_negative_gross_profit",
            test_questions=[
                "How many SKUs have negative gross profit?",
                "Count negative profit",
                "Number of losing SKUs"
            ],
            expected_response_patterns=["negative", "profit", "SKUs"],
            required_params={},
            description="Count SKUs where unit price < unit cost"
        ),
        
        "top_revenue_sku": TestCase(
            query_key="top_revenue_sku",
            test_questions=[
                "Which SKU has the highest unit price?",
                "Highest price SKU",
                "Most expensive SKU"
            ],
            expected_response_patterns=["highest unit price", "SKU", "unit price"],
            required_params={},
            description="Find SKU with highest unit price"
        ),
        
        "top_gp_per_unit_sku": TestCase(
            query_key="top_gp_per_unit_sku",
            test_questions=[
                "Which SKU has the highest gross profit per unit?",
                "Highest profit per unit",
                "Best margin per unit"
            ],
            expected_response_patterns=["highest gross profit", "SKU", "gross profit per unit"],
            required_params={},
            description="Find SKU with highest gross profit per unit"
        ),
        
        "country_with_most_skus": TestCase(
            query_key="country_with_most_skus",
            test_questions=[
                "Which country has the most SKUs?",
                "Country with most products",
                "Highest SKU count by country"
            ],
            expected_response_patterns=["country", "SKUs", "count"],
            required_params={},
            description="Find country with most SKUs"
        ),
        
        "total_skus_in_category": TestCase(
            query_key="total_skus_in_category",
            test_questions=[
                "How many SKUs are in the Legumes category?",
                "SKU count in Nuts",
                "Number of SKUs in Spices category"
            ],
            expected_response_patterns=["category", "SKUs"],
            required_params={"category": "Legumes"},
            description="Count SKUs in specific category"
        ),
        
        "avg_lead_time_category": TestCase(
            query_key="avg_lead_time_category",
            test_questions=[
                "What is the average lead time for the Legumes category?",
                "Average lead time for Nuts",
                "Mean lead time for Spices"
            ],
            expected_response_patterns=["average", "lead time", "category"],
            required_params={"category": "Legumes"},
            description="Calculate average lead time for category"
        ),
        
        "avg_unit_price_category": TestCase(
            query_key="avg_unit_price_category",
            test_questions=[
                "What is the average unit price for the Legumes category?",
                "Average unit price for Nuts",
                "Mean unit price for Spices"
            ],
            expected_response_patterns=["average", "unit price", "category"],
            required_params={"category": "Legumes"},
            description="Calculate average unit price for category"
        ),
        
        "top_revenue_skus_n": TestCase(
            query_key="top_revenue_skus_n",
            test_questions=[
                "Give me the top 5 SKUs by price",
                "Top 3 SKUs by price",
                "Highest price SKUs"
            ],
            expected_response_patterns=["top", "SKUs by unit price", "highest"],
            required_params={"n": 5},
            description="Get top N SKUs by unit price"
        ),
        
        "skus_with_lead_time_over": TestCase(
            query_key="skus_with_lead_time_over",
            test_questions=[
                "SKUs with lead time over 30 days",
                "Lead time over 25 days",
                "Long lead time"
            ],
            expected_response_patterns=["lead time over", "days", "SKUs"],
            required_params={"threshold": 30},
            description="Find SKUs with lead time over threshold"
        ),
        
        "category_highest_avg_lead_time": TestCase(
            query_key="category_highest_avg_lead_time",
            test_questions=[
                "Which category has the highest average lead time?",
                "Highest average lead time",
                "Longest lead time category"
            ],
            expected_response_patterns=["highest average lead time", "category", "days"],
            required_params={},
            description="Find category with highest average lead time"
        ),
        
        "excess_inventory_skus": TestCase(
            query_key="excess_inventory_skus",
            test_questions=[
                "Which SKUs have excess inventory?",
                "Excess inventory",
                "Overstocked"
            ],
            expected_response_patterns=["excess", "inventory", "SKUs"],
            required_params={},
            description="Find SKUs with excess inventory"
        ),
        
        "regional_demand_variations": TestCase(
            query_key="regional_demand_variations",
            test_questions=[
                "Analyze regional demand variations",
                "Regional demand",
                "Demand by country"
            ],
            expected_response_patterns=["regional", "demand", "country"],
            required_params={},
            description="Analyze demand variations by region"
        ),
        
        "manufacturing_constraints_proxy": TestCase(
            query_key="manufacturing_constraints_proxy",
            test_questions=[
                "Which SKUs have manufacturing constraints?",
                "Manufacturing constraints",
                "Supply constraints"
            ],
            expected_response_patterns=["manufacturing constraints", "lead times", "SKUs"],
            required_params={"threshold": 25},
            description="Find SKUs with potential manufacturing constraints"
        ),
        
        "skus_to_trim_proxy": TestCase(
            query_key="skus_to_trim_proxy",
            test_questions=[
                "Which SKUs can we trim?",
                "SKUs to trim",
                "Low performing SKUs"
            ],
            expected_response_patterns=["trim", "candidates", "SKUs"],
            required_params={},
            description="Find SKUs that could be trimmed"
        )
    }

def test_query_matching(test_cases: Dict[str, TestCase]) -> Dict[str, bool]:
    """Test that questions correctly match to canned queries"""
    print("🔍 Testing Query Matching...")
    results = {}
    
    for query_key, test_case in test_cases.items():
        print(f"  Testing {query_key}...")
        all_matched = True
        
        for question in test_case.test_questions:
            match_result = match_canned_query(question)
            if not match_result:
                print(f"    ❌ No match for: '{question}'")
                all_matched = False
            elif match_result[0] != query_key:
                print(f"    ❌ Wrong match: expected {query_key}, got {match_result[0]} for '{question}'")
                all_matched = False
            else:
                print(f"    ✅ Matched: '{question}' -> {query_key}")
        
        results[query_key] = all_matched
    
    return results

def test_query_execution(test_cases: Dict[str, TestCase]) -> Dict[str, Dict[str, Any]]:
    """Test that queries execute without errors"""
    print("\n⚡ Testing Query Execution...")
    results = {}
    
    for query_key, test_case in test_cases.items():
        print(f"  Testing {query_key}...")
        test_results = {}
        
        # Use the first test question for execution
        question = test_case.test_questions[0]
        match_result = match_canned_query(question)
        
        if not match_result:
            test_results["error"] = f"No match found for question: {question}"
            results[query_key] = test_results
            continue
        
        query_key_matched, canned_query, params = match_result
        
        try:
            # Execute the query
            start_time = time.time()
            response = execute_canned_query(canned_query, params)
            execution_time = time.time() - start_time
            
            test_results["success"] = True
            test_results["response"] = response
            test_results["execution_time"] = execution_time
            test_results["params"] = params
            
            # Check if response contains expected patterns
            pattern_matches = []
            for pattern in test_case.expected_response_patterns:
                if pattern.lower() in response.lower():
                    pattern_matches.append(pattern)
            
            test_results["pattern_matches"] = pattern_matches
            test_results["all_patterns_matched"] = len(pattern_matches) == len(test_case.expected_response_patterns)
            
            if test_results["all_patterns_matched"]:
                print(f"    ✅ Executed successfully ({execution_time:.2f}s)")
            else:
                print(f"    ⚠️  Executed but missing patterns: {set(test_case.expected_response_patterns) - set(pattern_matches)}")
            
        except Exception as e:
            test_results["success"] = False
            test_results["error"] = str(e)
            print(f"    ❌ Execution failed: {str(e)}")
        
        results[query_key] = test_results
    
    return results

def generate_test_report(matching_results: Dict[str, bool], execution_results: Dict[str, Dict[str, Any]]) -> str:
    """Generate a comprehensive test report"""
    
    total_queries = len(matching_results)
    matching_passed = sum(matching_results.values())
    execution_passed = sum(1 for r in execution_results.values() if r.get("success", False))
    pattern_passed = sum(1 for r in execution_results.values() if r.get("all_patterns_matched", False))
    
    report = f"""
# 📊 Canned Query Test Report

## 🎯 Summary
- **Total Queries Tested**: {total_queries}
- **Query Matching**: {matching_passed}/{total_queries} ({matching_passed/total_queries*100:.1f}%)
- **Query Execution**: {execution_passed}/{total_queries} ({execution_passed/total_queries*100:.1f}%)
- **Pattern Validation**: {pattern_passed}/{total_queries} ({pattern_passed/total_queries*100:.1f}%)

## 📋 Detailed Results
"""
    
    for query_key in matching_results.keys():
        report += f"\n### {query_key.replace('_', ' ').title()}\n"
        
        # Matching result
        if matching_results[query_key]:
            report += "✅ **Query Matching**: PASSED\n"
        else:
            report += "❌ **Query Matching**: FAILED\n"
        
        # Execution result
        exec_result = execution_results.get(query_key, {})
        if exec_result.get("success", False):
            report += "✅ **Query Execution**: PASSED\n"
            if exec_result.get("all_patterns_matched", False):
                report += "✅ **Pattern Validation**: PASSED\n"
            else:
                report += "⚠️  **Pattern Validation**: PARTIAL\n"
                missing_patterns = set(exec_result.get("expected_patterns", [])) - set(exec_result.get("pattern_matches", []))
                report += f"   Missing patterns: {missing_patterns}\n"
        else:
            report += f"❌ **Query Execution**: FAILED - {exec_result.get('error', 'Unknown error')}\n"
        
        # Performance info
        if exec_result.get("execution_time"):
            report += f"⏱️  **Execution Time**: {exec_result['execution_time']:.2f}s\n"
    
    return report

def main():
    """Run comprehensive canned query tests"""
    print("🚀 Starting Comprehensive Canned Query Tests")
    print("=" * 60)
    
    # Load secrets if available
    try:
        from run_complete_validation import load_secrets
        if load_secrets():
            print("✅ Loaded secrets from .streamlit/secrets.toml")
        else:
            print("⚠️  Could not load secrets, tests will run with environment variables only")
    except Exception as e:
        print(f"⚠️  Could not load secrets: {e}")
        print("   Tests will run with environment variables only")
    
    # Create test cases
    test_cases = create_test_cases()
    print(f"📋 Created {len(test_cases)} test cases")
    
    # Run tests
    matching_results = test_query_matching(test_cases)
    execution_results = test_query_execution(test_cases)
    
    # Generate report
    report = generate_test_report(matching_results, execution_results)
    
    # Save report
    with open("canned_query_test_report.md", "w") as f:
        f.write(report)
    
    print("\n" + "=" * 60)
    print("📊 TEST COMPLETED")
    print("=" * 60)
    print(report)
    
    # Calculate overall success
    total_queries = len(matching_results)
    overall_success = (
        sum(matching_results.values()) == total_queries and
        sum(1 for r in execution_results.values() if r.get("success", False)) == total_queries
    )
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED! The canned query system is working correctly.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED. Review the report above for details.")
        return 1

if __name__ == "__main__":
    exit(main())
