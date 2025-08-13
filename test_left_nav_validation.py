#!/usr/bin/env python3
"""
Comprehensive Left Nav Validation Test

This script validates all left nav questions using the ground truth system
to ensure 100% reliability and prevent regressions.
"""

import sys
import os
import time
from typing import Dict, List, Tuple
import pytest

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_test_environment():
    """Setup the test environment similar to Streamlit"""
    print("🔧 Setting up test environment...")
    
    # Try to read secrets from .streamlit/secrets.toml or streamlit/secret.toml
    api_key = None
    
    # First try environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OpenAI API key found in environment variables")
    else:
        # Try reading from secrets-like files (line-based key=value)
        try:
            for secrets_path in [os.path.join(".streamlit", "secrets.toml"), os.path.join("streamlit", "secret.toml")]:
                if not os.path.exists(secrets_path):
                    continue
                with open(secrets_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#') or '=' not in line:
                            continue
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('\"\'')
                        os.environ[key] = value
                        if key == "OPENAI_API_KEY":
                            api_key = value
                            print("✅ OpenAI API key found in secrets file")
                        elif key.startswith("NEO4J_"):
                            print(f"✅ {key} found in secrets file")
                # If we loaded at least API key, stop
                if api_key:
                    break
            if not api_key:
                print("❌ OPENAI_API_KEY not found in secrets files")
        except Exception as e:
            print(f"❌ Error reading secrets files: {e}")
    
    if not api_key:
        print("❌ OpenAI API key not found in secrets or environment variables")
        print("Please ensure you have:")
        print("OPENAI_API_KEY = 'your-api-key-here'")
        print("in your .streamlit/secrets.toml file or as environment variable")
        return False
    
    return True

def test_canned_queries_import():
    """Test that canned queries can be imported and loaded"""
    print("\n🧪 Testing canned queries import...")
    
    try:
        from solutions.tools.canned_queries import get_canned_queries, match_canned_query
        queries = get_canned_queries()
        
        assert len(queries) > 0, "No canned queries found"
        print(f"✅ Successfully loaded {len(queries)} canned queries")
        
        # Test a simple match
        test_question = "What is the category of SKU001?"
        match = match_canned_query(test_question)
        assert match is not None, "Failed to match basic SKU question"
        
        query_key, canned_query, params = match
        assert query_key == "sku_category", f"Expected sku_category, got {query_key}"
        assert "sku_id" in params, "Missing sku_id parameter"
        assert params["sku_id"] == "SKU001", f"Expected SKU001, got {params['sku_id']}"
        
        print("✅ Canned query matching works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Canned queries import failed: {e}")
        return False

def test_ground_truth_import():
    """Test that ground truth validator can be imported and loaded"""
    print("\n🧪 Testing ground truth validator import...")
    
    try:
        from solutions.tools.ground_truth_validator import (
            get_left_nav_ground_truth_cases,
            validate_ground_truth_case,
            run_ground_truth_validation
        )
        
        cases = get_left_nav_ground_truth_cases()
        assert len(cases) > 0, "No ground truth cases found"
        print(f"✅ Successfully loaded {len(cases)} ground truth cases")
        
        # Test a simple validation
        test_case = cases["sku_category_001"]
        result = validate_ground_truth_case(test_case)
        
        assert hasattr(result, 'success'), "Validation result missing success attribute"
        assert hasattr(result, 'response'), "Validation result missing response attribute"
        assert hasattr(result, 'errors'), "Validation result missing errors attribute"
        
        print("✅ Ground truth validation works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Ground truth validator import failed: {e}")
        return False

def test_database_connection():
    """Test database connection for canned queries"""
    print("\n🧪 Testing database connection...")
    
    try:
        from solutions.graph import get_graph
        graph = get_graph()
        
        if graph is None:
            print("❌ Database connection failed")
            return False
        
        # Test a simple query
        result = graph.query("MATCH (sku:SKU) RETURN count(sku) as count LIMIT 1")
        assert result is not None, "Database query returned None"
        
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def test_canned_query_execution():
    """Test execution of canned queries"""
    print("\n🧪 Testing canned query execution...")
    
    try:
        from solutions.tools.canned_queries import match_canned_query, execute_canned_query
        
        # Test a simple query
        test_question = "What is the category of SKU001?"
        match = match_canned_query(test_question)
        
        if match is None:
            print("❌ No canned query match found")
            return False
        
        query_key, canned_query, params = match
        response = execute_canned_query(canned_query, params)
        
        assert response is not None, "Canned query returned None"
        assert len(response) > 0, "Canned query returned empty response"
        assert "❌" not in response, "Canned query returned error"
        
        print(f"✅ Canned query execution successful: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Canned query execution failed: {e}")
        return False

def test_left_nav_questions():
    """Test all left nav questions from bot.py"""
    print("\n🧪 Testing left nav questions...")
    
    # Left nav questions from bot.py
    left_nav_questions = [
        # Verified data-backed basics
        "List the distinct product categories",
        "What is the category of SKU001?",
        "Tell me about SKU001",
        "Which SKU has the highest gross profit per unit?",
        "How many distinct categories are there?",
        "Which country has the most SKUs?",
        
        # Analytical intents (SKU-level proxies)
        "Show me excess inventory for promotions",
        "Analyze regional demand variations",
        "Which SKUs have manufacturing constraints?",
        "Show me lead time planning data",
        "Which SKUs can we trim to fit within capacity limits?",
        
        # Additional common questions
        "Show me all SKUs",
        "Which SKUs have negative gross profit?",
        "What country is SKU001 from?",
        "Give me the top 3 SKUs by total revenue",
        "What is the average lead time for the Nuts category?",
        "Show me the dashboard"
    ]
    
    results = []
    successful = 0
    
    for question in left_nav_questions:
        print(f"\n🔍 Testing: {question}")
        
        try:
            from solutions.agent import generate_response
            
            start_time = time.time()
            response = generate_response(question)
            execution_time = time.time() - start_time
            
            # Basic validation
            success = True
            errors = []
            
            if not response:
                errors.append("Empty response")
                success = False
            elif "❌" in response:
                errors.append("Error in response")
                success = False
            elif len(response.strip()) < 10:
                errors.append("Response too short")
                success = False
            
            results.append({
                "question": question,
                "response": response,
                "success": success,
                "errors": errors,
                "execution_time": execution_time
            })
            
            if success:
                print(f"✅ PASS - {execution_time:.2f}s")
                successful += 1
            else:
                print(f"❌ FAIL - {execution_time:.2f}s")
                for error in errors:
                    print(f"   Error: {error}")
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({
                "question": question,
                "response": f"Exception: {str(e)}",
                "success": False,
                "errors": [f"Exception: {str(e)}"],
                "execution_time": 0
            })
    
    # Summary
    print(f"\n📊 Left Nav Questions Summary:")
    print(f"Total: {len(left_nav_questions)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(left_nav_questions) - successful}")
    print(f"Success Rate: {(successful/len(left_nav_questions))*100:.1f}%")
    
    return successful == len(left_nav_questions)

def test_ground_truth_validation():
    """Run full ground truth validation"""
    print("\n🧪 Running ground truth validation...")
    
    try:
        from solutions.tools.ground_truth_validator import run_ground_truth_validation, generate_ground_truth_report
        
        results = run_ground_truth_validation()
        
        # Generate report
        report = generate_ground_truth_report(results)
        
        # Save report to file
        with open("ground_truth_validation_report.md", "w") as f:
            f.write(report)
        
        print("📁 Ground truth validation report saved to ground_truth_validation_report.md")
        
        # Check success rate
        total_cases = len(results)
        successful_cases = sum(1 for r in results.values() if r.success)
        success_rate = (successful_cases/total_cases)*100
        
        print(f"📊 Ground Truth Success Rate: {success_rate:.1f}%")
        
        return success_rate >= 95.0  # Require 95% success rate
        
    except Exception as e:
        print(f"❌ Ground truth validation failed: {e}")
        return False

def test_canned_query_cache():
    """Test canned query caching functionality"""
    print("\n🧪 Testing canned query cache...")
    
    try:
        from solutions.tools.canned_queries import (
            match_canned_query, 
            execute_canned_query, 
            clear_canned_query_cache,
            get_canned_query_stats
        )
        
        # Clear cache first
        clear_canned_query_cache()
        
        # Test query
        test_question = "What is the category of SKU001?"
        match = match_canned_query(test_question)
        
        if match is None:
            print("❌ No canned query match found")
            return False
        
        query_key, canned_query, params = match
        
        # First execution
        start_time = time.time()
        response1 = execute_canned_query(canned_query, params)
        time1 = time.time() - start_time
        
        # Second execution (should be cached)
        start_time = time.time()
        response2 = execute_canned_query(canned_query, params)
        time2 = time.time() - start_time
        
        # Check that responses are identical
        assert response1 == response2, "Cached response differs from original"
        
        # Check that second execution is faster (cache hit)
        assert time2 < time1, "Cached execution not faster"
        
        # Check cache stats
        stats = get_canned_query_stats()
        assert stats["cache_size"] > 0, "Cache should contain entries"
        
        print(f"✅ Cache test successful - Original: {time1:.3f}s, Cached: {time2:.3f}s")
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Left Nav Validation Test Suite")
    print("=" * 60)
    
    # Setup environment
    if not setup_test_environment():
        print("❌ Environment setup failed")
        return False
    
    # Run tests
    tests = [
        ("Canned Queries Import", test_canned_queries_import),
        ("Ground Truth Import", test_ground_truth_import),
        ("Database Connection", test_database_connection),
        ("Canned Query Execution", test_canned_query_execution),
        ("Left Nav Questions", test_left_nav_questions),
        ("Ground Truth Validation", test_ground_truth_validation),
        ("Canned Query Cache", test_canned_query_cache)
    ]
    
    results = []
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
            results.append((test_name, False))
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 FINAL TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {len(tests) - passed}")
    print(f"Success Rate: {(passed/len(tests))*100:.1f}%")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    # Recommendations
    if passed == len(tests):
        print(f"\n🎉 ALL TESTS PASSED!")
        print("✅ Left nav questions are working correctly")
        print("✅ No regressions detected")
        print("✅ System is ready for production use")
    else:
        print(f"\n⚠️ {len(tests) - passed} TESTS FAILED")
        print("🔧 Review failed tests and fix issues")
        print("🧪 Re-run tests after fixes")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
