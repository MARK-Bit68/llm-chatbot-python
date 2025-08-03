#!/usr/bin/env python3
"""
Comprehensive Test Script for FMCG RAG Stack
Tests the full pipeline without requiring Streamlit restart
"""

import sys
import os
import time
from typing import Dict, List, Tuple

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_test_environment():
    """Setup the test environment similar to Streamlit"""
    print("🔧 Setting up test environment...")
    
    # Mock Streamlit secrets (you'll need to set these)
    import streamlit as st
    
    # Check if secrets are available
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        print("✅ OpenAI API key found in secrets")
    except:
        # Try environment variable as fallback
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print("✅ OpenAI API key found in environment variables")
        else:
            print("❌ OpenAI API key not found in secrets or environment variables")
            print("Please ensure you have:")
            print("OPENAI_API_KEY = 'your-api-key-here'")
            print("in your .streamlit/secrets.toml file or as environment variable")
            return False
    
    return True

def test_question(question: str, expected_complexity: str) -> Tuple[bool, str]:
    """
    Test a single question and return success status and response
    """
    print(f"\n🧪 Testing {expected_complexity} question: '{question}'")
    print("=" * 60)
    
    try:
        # Import the generate_response function
        from solutions.agent import generate_response
        
        # Record start time
        start_time = time.time()
        
        # Generate response
        response = generate_response(question)
        
        # Record end time
        end_time = time.time()
        response_time = end_time - start_time
        
        # Analyze response
        success = analyze_response(response, expected_complexity)
        
        print(f"⏱️  Response time: {response_time:.2f}s")
        print(f"📊 Response length: {len(response)} characters")
        print(f"✅ Success: {success}")
        print(f"📝 Response: {response[:200]}{'...' if len(response) > 200 else ''}")
        
        return success, response
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, f"Error: {str(e)}"

def analyze_response(response: str, expected_complexity: str) -> bool:
    """
    Analyze if the response meets expectations for the complexity level
    """
    if not response or response.startswith("Error:"):
        return False
    
    # Basic checks for all responses
    if len(response) < 10:
        return False
    
    # Complexity-specific checks
    if expected_complexity == "LOW":
        # Factual questions should be concise and direct
        return len(response) < 500 and any(keyword in response.lower() for keyword in ["country", "category", "sku"])
    
    elif expected_complexity == "MEDIUM":
        # Extrapolation should include some analysis
        return len(response) > 200 and any(keyword in response.lower() for keyword in ["demand", "inventory", "plan", "monthly"])
    
    elif expected_complexity == "HIGH":
        # What-if scenarios should include calculations and analysis
        return len(response) > 300 and any(keyword in response.lower() for keyword in ["cost", "revenue", "profit", "analysis", "impact"])
    
    return True

def run_comprehensive_test():
    """
    Run comprehensive test with three representative questions
    """
    print("🚀 Starting Comprehensive FMCG RAG Stack Test")
    print("=" * 60)
    
    # Setup test environment
    if not setup_test_environment():
        print("❌ Test environment setup failed")
        return False
    
    # Define test questions with expected complexity
    test_questions = [
        {
            "question": "What country is SKU001 from?",
            "complexity": "LOW",
            "description": "Simple factual lookup"
        },
        {
            "question": "What is the inventory plan for SKU001?",
            "complexity": "MEDIUM", 
            "description": "Data extraction and formatting"
        },
        {
            "question": "What would the unit cost for SKU001 be if we increased demand by 10X?",
            "complexity": "HIGH",
            "description": "What-if scenario with calculations"
        }
    ]
    
    # Run tests
    results = []
    total_start_time = time.time()
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n📋 Test {i}/3: {test['description']}")
        print(f"Question: {test['question']}")
        
        success, response = test_question(test['question'], test['complexity'])
        results.append({
            'test_num': i,
            'question': test['question'],
            'complexity': test['complexity'],
            'description': test['description'],
            'success': success,
            'response': response
        })
        
        # Small delay between tests
        time.sleep(1)
    
    total_time = time.time() - total_start_time
    
    # Print results summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"⏱️  Total time: {total_time:.2f}s")
    print(f"📈 Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Detailed results
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"\n{status} Test {result['test_num']}: {result['description']}")
        print(f"   Question: {result['question']}")
        print(f"   Complexity: {result['complexity']}")
        if not result['success']:
            print(f"   Error: {result['response'][:100]}...")
    
    # Overall assessment
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! The RAG stack is working correctly.")
        print("This means it should work properly in Streamlit as well.")
        return True
    elif passed_tests >= total_tests * 0.66:
        print(f"\n⚠️  MOSTLY WORKING: {passed_tests}/{total_tests} tests passed.")
        print("The system is mostly functional but may have some issues.")
        return True
    else:
        print(f"\n❌ SIGNIFICANT ISSUES: Only {passed_tests}/{total_tests} tests passed.")
        print("The system needs debugging before it will work in Streamlit.")
        return False

def main():
    """Main test runner"""
    print("🧪 FMCG RAG Stack Test Suite")
    print("This script tests the full RAG pipeline without Streamlit")
    print("=" * 60)
    
    try:
        success = run_comprehensive_test()
        if success:
            print("\n🎯 RECOMMENDATION: Ready for Streamlit testing!")
            print("If these tests pass, the system should work in Streamlit chat.")
        else:
            print("\n🔧 RECOMMENDATION: Fix issues before Streamlit testing")
            print("Address the failing tests before using in Streamlit.")
        
        return success
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        print("The test suite itself failed. Check your setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 