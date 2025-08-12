#!/usr/bin/env python3
"""
Smoke Test for Left Nav Questions

Quick validation of left nav questions to ensure they work correctly.
This script runs a subset of critical tests for fast feedback.
"""

import sys
import os
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def quick_smoke_test():
    """Run a quick smoke test of left nav questions"""
    
    print("🚀 Quick Smoke Test - Left Nav Questions")
    print("=" * 50)
    
    # Critical left nav questions to test
    critical_questions = [
        "What is the category of SKU001?",
        "Tell me about SKU001", 
        "List the distinct product categories",
        "Which SKUs have negative gross profit?",
        "Show me the dashboard"
    ]
    
    results = []
    successful = 0
    
    for question in critical_questions:
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
            
            if success:
                print(f"✅ PASS - {execution_time:.2f}s")
                successful += 1
            else:
                print(f"❌ FAIL - {execution_time:.2f}s")
                for error in errors:
                    print(f"   Error: {error}")
            
            results.append({
                "question": question,
                "success": success,
                "execution_time": execution_time,
                "errors": errors
            })
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({
                "question": question,
                "success": False,
                "execution_time": 0,
                "errors": [f"Exception: {str(e)}"]
            })
    
    # Summary
    print(f"\n📊 Smoke Test Summary:")
    print(f"Total: {len(critical_questions)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(critical_questions) - successful}")
    print(f"Success Rate: {(successful/len(critical_questions))*100:.1f}%")
    
    if successful == len(critical_questions):
        print("🎉 All critical questions passed!")
        return True
    else:
        print("⚠️ Some critical questions failed - check the system")
        return False

def test_canned_query_system():
    """Test the canned query system specifically"""
    
    print("\n🧪 Testing Canned Query System...")
    
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
        
        if response and "❌" not in response:
            print("✅ Canned query system working")
            return True
        else:
            print("❌ Canned query system failed")
            return False
            
    except Exception as e:
        print(f"❌ Canned query test failed: {e}")
        return False

def main():
    """Run smoke tests"""
    
    # Test canned query system
    canned_success = test_canned_query_system()
    
    # Test critical questions
    questions_success = quick_smoke_test()
    
    # Overall result
    overall_success = canned_success and questions_success
    
    print(f"\n{'='*50}")
    print("📊 SMOKE TEST RESULTS")
    print(f"{'='*50}")
    print(f"Canned Query System: {'✅ PASS' if canned_success else '❌ FAIL'}")
    print(f"Critical Questions: {'✅ PASS' if questions_success else '❌ FAIL'}")
    print(f"Overall: {'✅ PASS' if overall_success else '❌ FAIL'}")
    
    if overall_success:
        print("\n🎉 Smoke test passed! Left nav questions are working correctly.")
    else:
        print("\n⚠️ Smoke test failed! Check the system for issues.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
