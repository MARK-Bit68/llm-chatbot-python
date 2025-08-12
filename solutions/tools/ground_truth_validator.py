"""
Ground Truth Validator for Left Nav Questions

This module provides validation and testing capabilities for all left nav questions
to ensure they return correct, consistent responses and prevent regressions.
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from solutions.graph import get_graph
from solutions.tools.canned_queries import get_canned_queries, execute_canned_query, match_canned_query
from monitoring import record_event, timeit

@dataclass
class GroundTruthCase:
    """Represents a ground truth test case"""
    question: str
    expected_patterns: List[str]  # Patterns that should appear in the response
    expected_absence: List[str] = None  # Patterns that should NOT appear
    expected_count: Optional[int] = None  # Expected number of results
    expected_fields: List[str] = None  # Expected fields in response
    description: str = ""

@dataclass
class ValidationResult:
    """Result of a ground truth validation"""
    question: str
    success: bool
    response: str
    errors: List[str]
    warnings: List[str]
    execution_time: float
    cache_hit: bool = False

def get_left_nav_ground_truth_cases() -> Dict[str, GroundTruthCase]:
    """Get all ground truth cases for left nav questions"""
    
    return {
        # Basic SKU Information
        "sku_category_001": GroundTruthCase(
            question="What is the category of SKU001?",
            expected_patterns=["category", "SKU001"],
            expected_absence=["Unknown", "Error", "❌"],
            description="SKU category lookup"
        ),
        
        "sku_country_001": GroundTruthCase(
            question="What country is SKU001 from?",
            expected_patterns=["country", "SKU001"],
            expected_absence=["Unknown", "Error", "❌"],
            description="SKU country lookup"
        ),
        
        "sku_details_001": GroundTruthCase(
            question="Tell me about SKU001",
            expected_patterns=["SKU001", "category", "country", "unit_price", "unit_cost"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Comprehensive SKU details"
        ),
        
        # Aggregation Queries
        "distinct_categories": GroundTruthCase(
            question="List the distinct product categories",
            expected_patterns=["categories", "Legumes", "Nuts", "Spices", "Grains"],
            expected_absence=["Unknown", "Error", "❌"],
            expected_count=5,  # Should have 5 categories
            description="List all product categories"
        ),
        
        "distinct_categories_count": GroundTruthCase(
            question="How many distinct categories are there?",
            expected_patterns=["5", "categories"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Count distinct categories"
        ),
        
        "all_skus": GroundTruthCase(
            question="Show me all SKUs",
            expected_patterns=["SKU", "All SKUs", "portfolio"],
            expected_absence=["Unknown", "Error", "❌"],
            expected_count=50,  # Should show up to 50 SKUs
            description="List all SKUs"
        ),
        
        "all_skus_count": GroundTruthCase(
            question="How many SKUs are there?",
            expected_patterns=["SKU", "count"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Count total SKUs"
        ),
        
        # Financial Analysis
        "negative_gross_profit": GroundTruthCase(
            question="Which SKUs have negative gross profit?",
            expected_patterns=["No data found", "negative", "gross profit"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Find SKUs with negative profit (may return no data if none exist)"
        ),
        
        "count_negative_gross_profit": GroundTruthCase(
            question="How many SKUs have negative gross profit?",
            expected_patterns=["SKU", "negative", "gross profit"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Count SKUs with negative profit"
        ),
        
        "top_revenue_sku": GroundTruthCase(
            question="Which SKU has the highest unit price?",
            expected_patterns=["highest", "unit price", "SKU"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Find highest unit price SKU"
        ),
        
        "top_gp_per_unit_sku": GroundTruthCase(
            question="Which SKU has the highest gross profit per unit?",
            expected_patterns=["highest", "gross profit", "unit", "SKU"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Find SKU with highest profit per unit"
        ),
        
        # Country Analysis
        "country_with_most_skus": GroundTruthCase(
            question="Which country has the most SKUs?",
            expected_patterns=["country", "most", "SKU"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Find country with most SKUs"
        ),
        
        # Category Analysis
        "total_skus_in_category": GroundTruthCase(
            question="How many SKUs are in the Legumes category?",
            expected_patterns=["Legumes", "SKU", "count"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Count SKUs in specific category"
        ),
        
        "avg_lead_time_category": GroundTruthCase(
            question="What is the average lead time for the Nuts category?",
            expected_patterns=["Nuts", "average", "lead time"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Calculate average lead time for category"
        ),
        
        "avg_unit_price_category": GroundTruthCase(
            question="What is the average unit price for the Spices category?",
            expected_patterns=["Spices", "average", "unit price"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Calculate average unit price for category"
        ),
        
        # Top N Queries
        "top_revenue_skus_n": GroundTruthCase(
            question="Give me the top 3 SKUs by total revenue",
            expected_patterns=["top", "3", "SKU", "revenue"],
            expected_absence=["Unknown", "Error", "❌"],
            expected_count=3,
            description="Get top N SKUs by revenue"
        ),
        
        # Lead Time Analysis
        "skus_with_lead_time_over": GroundTruthCase(
            question="List up to 5 SKUs with lead time over 25 days",
            expected_patterns=["lead time", "25", "days", "SKU"],
            expected_absence=["Unknown", "Error", "❌"],
            expected_count=5,
            description="Find SKUs with lead time over threshold"
        ),
        
        "category_highest_avg_lead_time": GroundTruthCase(
            question="Which category has the highest average lead time?",
            expected_patterns=["category", "highest", "average", "lead time"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Find category with highest average lead time"
        ),
        
        # S&OP Analytical Queries
        "excess_inventory_skus": GroundTruthCase(
            question="Which SKUs have excess inventory that we can promote next month?",
            expected_patterns=["excess", "inventory", "SKU", "promotion"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Find SKUs with excess inventory"
        ),
        
        "regional_demand_variations": GroundTruthCase(
            question="Analyze regional demand variations",
            expected_patterns=["regional", "demand", "country", "analysis"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Analyze demand by region"
        ),
        
        "manufacturing_constraints_proxy": GroundTruthCase(
            question="Which SKUs have manufacturing constraints?",
            expected_patterns=["manufacturing", "constraints", "SKU", "lead time"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Find SKUs with manufacturing constraints"
        ),
        
        "skus_to_trim_proxy": GroundTruthCase(
            question="Which SKUs can we trim to fit within capacity limits?",
            expected_patterns=["trim", "SKU", "capacity", "profit"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Find SKUs to trim"
        ),
        
        # Dashboard Query
        "show_dashboard": GroundTruthCase(
            question="Show me the dashboard",
            expected_patterns=["dashboard", "analytics", "charts", "KPIs"],
            expected_absence=["Unknown", "Error", "❌"],
            description="Dashboard request"
        )
    }

def validate_ground_truth_case(case: GroundTruthCase) -> ValidationResult:
    """Validate a single ground truth case"""
    
    import time
    
    start_time = time.time()
    errors = []
    warnings = []
    
    try:
        # Check if this is a canned query
        canned_match = match_canned_query(case.question)
        
        if canned_match:
            # Use canned query
            query_key, canned_query, params = canned_match
            response = execute_canned_query(canned_query, params)
            cache_hit = "cache_hit" in response.lower()  # Simple cache detection
        else:
            # This should not happen for left nav questions
            response = "❌ No canned query found for this question"
            cache_hit = False
            errors.append("No canned query match found")
        
        execution_time = time.time() - start_time
        
        # Validate response
        success = True
        
        # Check expected patterns
        for pattern in case.expected_patterns:
            if pattern.lower() not in response.lower():
                errors.append(f"Expected pattern '{pattern}' not found in response")
                success = False
        
        # Check expected absence
        if case.expected_absence:
            for pattern in case.expected_absence:
                if pattern.lower() in response.lower():
                    errors.append(f"Unexpected pattern '{pattern}' found in response")
                    success = False
        
        # Check expected count (if specified)
        if case.expected_count:
            # Count lines that look like SKU entries
            sku_lines = len([line for line in response.split('\n') if 'SKU' in line])
            if sku_lines != case.expected_count:
                warnings.append(f"Expected {case.expected_count} results, found {sku_lines}")
        
        # Check for error indicators
        if any(error_indicator in response.lower() for error_indicator in ["error", "❌", "failed", "exception"]):
            errors.append("Response contains error indicators")
            success = False
        
        # Check for empty or very short responses
        if len(response.strip()) < 10:
            errors.append("Response is too short")
            success = False
        
        return ValidationResult(
            question=case.question,
            success=success,
            response=response,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            cache_hit=cache_hit
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        return ValidationResult(
            question=case.question,
            success=False,
            response=f"Exception: {str(e)}",
            errors=[f"Exception occurred: {str(e)}"],
            warnings=[],
            execution_time=execution_time,
            cache_hit=False
        )

def run_ground_truth_validation() -> Dict[str, ValidationResult]:
    """Run validation for all ground truth cases"""
    
    print("🧪 Running Ground Truth Validation...")
    print("=" * 60)
    
    cases = get_left_nav_ground_truth_cases()
    results = {}
    
    total_cases = len(cases)
    successful_cases = 0
    
    for case_key, case in cases.items():
        print(f"\n🔍 Testing: {case.description}")
        print(f"Question: {case.question}")
        
        result = validate_ground_truth_case(case)
        results[case_key] = result
        
        if result.success:
            print(f"✅ PASS - {result.execution_time:.2f}s")
            successful_cases += 1
        else:
            print(f"❌ FAIL - {result.execution_time:.2f}s")
            for error in result.errors:
                print(f"   Error: {error}")
        
        if result.warnings:
            for warning in result.warnings:
                print(f"   Warning: {warning}")
        
        if result.cache_hit:
            print("   📦 Cache hit")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 VALIDATION SUMMARY")
    print(f"Total Cases: {total_cases}")
    print(f"Successful: {successful_cases}")
    print(f"Failed: {total_cases - successful_cases}")
    print(f"Success Rate: {(successful_cases/total_cases)*100:.1f}%")
    
    # Record metrics
    record_event("ground_truth.validation", {
        "total_cases": total_cases,
        "successful_cases": successful_cases,
        "success_rate": (successful_cases/total_cases)*100
    })
    
    return results

def validate_specific_question(question: str) -> ValidationResult:
    """Validate a specific question against ground truth"""
    
    # Find matching case
    cases = get_left_nav_ground_truth_cases()
    matching_case = None
    
    for case_key, case in cases.items():
        if case.question.lower() == question.lower():
            matching_case = case
            break
    
    if not matching_case:
        # Create a basic case for unknown questions
        matching_case = GroundTruthCase(
            question=question,
            expected_patterns=["SKU", "data"],
            expected_absence=["Error", "❌", "Unknown"],
            description="Custom question validation"
        )
    
    return validate_ground_truth_case(matching_case)

def generate_ground_truth_report(results: Dict[str, ValidationResult]) -> str:
    """Generate a comprehensive report of ground truth validation results"""
    
    total_cases = len(results)
    successful_cases = sum(1 for r in results.values() if r.success)
    failed_cases = total_cases - successful_cases
    
    report = f"""
# 🧪 Ground Truth Validation Report

## 📊 Summary
- **Total Cases**: {total_cases}
- **Successful**: {successful_cases}
- **Failed**: {failed_cases}
- **Success Rate**: {(successful_cases/total_cases)*100:.1f}%

## ✅ Successful Cases ({successful_cases})
"""
    
    for case_key, result in results.items():
        if result.success:
            report += f"- **{case_key}**: {result.question} ({result.execution_time:.2f}s)\n"
    
    if failed_cases > 0:
        report += f"""
## ❌ Failed Cases ({failed_cases})
"""
        for case_key, result in results.items():
            if not result.success:
                report += f"""
### {case_key}
- **Question**: {result.question}
- **Errors**: {', '.join(result.errors)}
- **Response**: {result.response[:200]}{'...' if len(result.response) > 200 else ''}
"""
    
    # Performance metrics
    avg_time = sum(r.execution_time for r in results.values()) / len(results)
    cache_hits = sum(1 for r in results.values() if r.cache_hit)
    
    report += f"""
## ⏱️ Performance Metrics
- **Average Response Time**: {avg_time:.2f}s
- **Cache Hits**: {cache_hits}/{total_cases} ({(cache_hits/total_cases)*100:.1f}%)

## 🔧 Recommendations
"""
    
    if failed_cases == 0:
        report += "- ✅ All left nav questions are working correctly\n"
        report += "- ✅ No regressions detected\n"
        report += "- ✅ System is ready for production use\n"
    else:
        report += f"- ⚠️ {failed_cases} questions need attention\n"
        report += "- 🔧 Review failed cases and fix underlying issues\n"
        report += "- 🧪 Re-run validation after fixes\n"
    
    return report

def export_ground_truth_cases_to_json(filename: str = "ground_truth_cases.json"):
    """Export ground truth cases to JSON for external validation"""
    
    cases = get_left_nav_ground_truth_cases()
    
    export_data = []
    for case_key, case in cases.items():
        export_data.append({
            "key": case_key,
            "question": case.question,
            "expected_patterns": case.expected_patterns,
            "expected_absence": case.expected_absence or [],
            "expected_count": case.expected_count,
            "expected_fields": case.expected_fields or [],
            "description": case.description
        })
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"📁 Ground truth cases exported to {filename}")
    return filename

def import_ground_truth_cases_from_json(filename: str) -> Dict[str, GroundTruthCase]:
    """Import ground truth cases from JSON"""
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    cases = {}
    for item in data:
        case = GroundTruthCase(
            question=item["question"],
            expected_patterns=item["expected_patterns"],
            expected_absence=item["expected_absence"],
            expected_count=item["expected_count"],
            expected_fields=item["expected_fields"],
            description=item["description"]
        )
        cases[item["key"]] = case
    
    return cases

def get_validation_stats() -> Dict[str, Any]:
    """Get statistics about ground truth validation"""
    
    cases = get_left_nav_ground_truth_cases()
    
    return {
        "total_cases": len(cases),
        "categories": {
            "basic_sku": len([c for c in cases.values() if "sku" in c.question.lower() and "category" in c.question.lower()]),
            "financial": len([c for c in cases.values() if any(term in c.question.lower() for term in ["profit", "revenue", "price"])]),
            "analytical": len([c for c in cases.values() if any(term in c.question.lower() for term in ["analyze", "variations", "constraints"])]),
            "aggregation": len([c for c in cases.values() if any(term in c.question.lower() for term in ["count", "how many", "distinct"])])
        },
        "canned_queries_available": len(get_canned_queries())
    }
