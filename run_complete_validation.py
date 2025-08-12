#!/usr/bin/env python3
"""
Complete Left Nav Validation Runner

This script loads secrets from .streamlit/secrets.toml and runs all validation tests
to ensure 100% pass rate for the left nav validation system.
"""

import os
import sys
import subprocess
import time

def load_secrets():
    """Load secrets from .streamlit/secrets.toml and set as environment variables"""
    print("🔧 Loading secrets from .streamlit/secrets.toml...")
    
    secrets_path = ".streamlit/secrets.toml"
    if not os.path.exists(secrets_path):
        print(f"❌ Secrets file not found: {secrets_path}")
        return False
    
    try:
        with open(secrets_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Set as environment variable
                    os.environ[key] = value
                    print(f"✅ Loaded: {key}")
        
        # Verify critical secrets are loaded
        required_secrets = ['OPENAI_API_KEY', 'NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD']
        missing_secrets = []
        
        for secret in required_secrets:
            if not os.getenv(secret):
                missing_secrets.append(secret)
        
        if missing_secrets:
            print(f"❌ Missing required secrets: {missing_secrets}")
            return False
        
        print("✅ All required secrets loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return False

def run_test_script(script_path, description):
    """Run a test script and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {description}")
    print(f"Script: {script_path}")
    print(f"{'='*60}")
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        if success:
            print(f"✅ {description}: PASSED")
        else:
            print(f"❌ {description}: FAILED (exit code: {result.returncode})")
        
        return success
        
    except subprocess.TimeoutExpired:
        print(f"❌ {description}: TIMEOUT (exceeded 5 minutes)")
        return False
    except Exception as e:
        print(f"❌ {description}: ERROR - {e}")
        return False

def run_individual_tests():
    """Run individual test functions to validate specific components"""
    print(f"\n{'='*60}")
    print("🧪 Running Individual Component Tests")
    print(f"{'='*60}")
    
    # Import test functions
    try:
        from test_left_nav_validation import (
            test_canned_queries_import,
            test_ground_truth_import,
            test_database_connection,
            test_canned_query_execution,
            test_left_nav_questions,
            test_ground_truth_validation,
            test_canned_query_cache
        )
        
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
            print(f"\n🔍 Testing: {test_name}")
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
        
        # Summary
        print(f"\n📊 Individual Tests Summary:")
        print(f"Total: {len(tests)}")
        print(f"Passed: {passed}")
        print(f"Failed: {len(tests) - passed}")
        print(f"Success Rate: {(passed/len(tests))*100:.1f}%")
        
        return passed == len(tests)
        
    except ImportError as e:
        print(f"❌ Could not import test functions: {e}")
        return False

def test_canned_query_system():
    """Test the canned query system directly"""
    print(f"\n{'='*60}")
    print("🧪 Testing Canned Query System Directly")
    print(f"{'='*60}")
    
    try:
        from solutions.tools.canned_queries import match_canned_query, execute_canned_query
        
        # Test a simple query
        test_question = "What is the category of SKU001?"
        print(f"Testing question: {test_question}")
        
        match = match_canned_query(test_question)
        if match is None:
            print("❌ No canned query match found")
            return False
        
        query_key, canned_query, params = match
        print(f"✅ Matched query: {query_key}")
        print(f"Parameters: {params}")
        
        response = execute_canned_query(canned_query, params)
        print(f"Response: {response[:200]}...")
        
        if response and "❌" not in response:
            print("✅ Canned query system working")
            return True
        else:
            print("❌ Canned query system failed")
            return False
            
    except Exception as e:
        print(f"❌ Canned query test failed: {e}")
        return False

def test_ground_truth_system():
    """Test the ground truth validation system directly"""
    print(f"\n{'='*60}")
    print("🧪 Testing Ground Truth System Directly")
    print(f"{'='*60}")
    
    try:
        from solutions.tools.ground_truth_validator import validate_specific_question
        
        # Test a simple validation
        test_question = "What is the category of SKU001?"
        print(f"Testing question: {test_question}")
        
        result = validate_specific_question(test_question)
        print(f"Success: {result.success}")
        print(f"Response: {result.response[:200]}...")
        
        if result.errors:
            print(f"Errors: {result.errors}")
        
        if result.warnings:
            print(f"Warnings: {result.warnings}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Ground truth test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Complete Left Nav Validation Test Suite")
    print("=" * 60)
    
    # Load secrets
    if not load_secrets():
        print("❌ Failed to load secrets. Exiting.")
        return False
    
    # Test individual components
    print("\n🔧 Testing individual components...")
    individual_success = run_individual_tests()
    
    # Test canned query system directly
    canned_success = test_canned_query_system()
    
    # Test ground truth system directly
    ground_truth_success = test_ground_truth_system()
    
    # Run full test scripts
    print("\n🔧 Running full test scripts...")
    
    # Run smoke test
    smoke_success = run_test_script("scripts/smoke_left_nav.py", "Smoke Test")
    
    # Run comprehensive validation
    comprehensive_success = run_test_script("test_left_nav_validation.py", "Comprehensive Validation")
    
    # Run integrated test suite
    integrated_success = run_test_script("test_stack.py", "Integrated Test Suite")
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 FINAL VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    results = [
        ("Individual Components", individual_success),
        ("Canned Query System", canned_success),
        ("Ground Truth System", ground_truth_success),
        ("Smoke Test", smoke_success),
        ("Comprehensive Validation", comprehensive_success),
        ("Integrated Test Suite", integrated_success)
    ]
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Total Test Categories: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    # Final assessment
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("✅ Left nav validation system is working correctly")
        print("✅ No regressions detected")
        print("✅ System is ready for production use")
        print("✅ 100% reliability achieved for left nav questions")
    else:
        print(f"\n⚠️ {total - passed} TEST CATEGORIES FAILED")
        print("🔧 Review failed tests and fix issues")
        print("🧪 Re-run tests after fixes")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
