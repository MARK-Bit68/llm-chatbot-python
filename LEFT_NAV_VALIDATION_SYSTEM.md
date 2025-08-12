# Left Nav Validation System

## Overview

This document describes the comprehensive left nav validation system that ensures 100% reliability for all questions that appear in the left navigation of the FMCG chatbot. The system uses canned cypher queries with ground truth validation to prevent regressions and maintain consistent, professional responses.

## Architecture

### 1. Canned Query System (`solutions/tools/canned_queries.py`)

The canned query system provides deterministic, pre-tested cypher queries for all left nav questions. This eliminates the error-prone LLM-generated cypher approach for known questions.

#### Key Components:

- **CannedQuery**: Data class representing a canned query with patterns, cypher query, response template, and metadata
- **CannedQueryCache**: In-memory cache with TTL (5 minutes) for query responses
- **Pattern Matching**: Intelligent pattern matching to identify which canned query to use
- **Parameter Extraction**: Automatic extraction of parameters (SKU IDs, categories, thresholds, etc.)

#### Supported Query Types:

1. **Basic SKU Information**
   - SKU category lookup
   - SKU country lookup
   - Comprehensive SKU details

2. **Aggregation Queries**
   - Distinct categories listing
   - Category counts
   - All SKUs listing
   - SKU counts

3. **Financial Analysis**
   - Negative gross profit SKUs
   - Top revenue SKUs
   - Highest profit per unit SKUs

4. **Geographic Analysis**
   - Country with most SKUs
   - Regional demand variations

5. **Category Analysis**
   - SKUs in specific categories
   - Average lead times by category
   - Average unit prices by category

6. **S&OP Analytical Queries**
   - Excess inventory identification
   - Manufacturing constraints
   - SKUs to trim

### 2. Ground Truth Validator (`solutions/tools/ground_truth_validator.py`)

The ground truth validator provides comprehensive testing and validation capabilities to ensure all left nav questions return correct, consistent responses.

#### Key Components:

- **GroundTruthCase**: Data class representing a test case with expected patterns and validation criteria
- **ValidationResult**: Data class containing validation results with success status, errors, and warnings
- **Pattern Validation**: Checks for expected patterns in responses
- **Error Detection**: Identifies error indicators and unexpected content
- **Performance Metrics**: Tracks execution times and cache hits

#### Validation Criteria:

1. **Expected Patterns**: Required content that must appear in responses
2. **Expected Absence**: Content that should NOT appear (error indicators)
3. **Expected Counts**: Number of results expected for list queries
4. **Response Quality**: Length, format, and professional tone checks

### 3. Agent Integration (`solutions/agent.py`)

The agent has been updated to use canned queries as the first priority for left nav questions, falling back to the existing LLM-based approach only for unknown questions.

#### Integration Flow:

1. **Canned Query Pre-dispatch**: Check if question matches any canned query patterns
2. **Parameter Extraction**: Extract required parameters from the question
3. **Query Execution**: Execute the canned cypher query with parameters
4. **Response Formatting**: Format response using the predefined template
5. **Caching**: Cache the response for future use (5-minute TTL)
6. **Fallback**: If no canned query matches, use existing LLM-based approach

## Left Nav Questions Covered

### Verified Data-Backed Basics
- "List the distinct product categories"
- "What is the category of SKU001?"
- "Tell me about SKU001"
- "Which SKU has the highest gross profit per unit?"
- "How many distinct categories are there?"
- "Which country has the most SKUs?"

### Analytical Intents (SKU-level proxies)
- "Show me excess inventory for promotions"
- "Analyze regional demand variations"
- "Which SKUs have manufacturing constraints?"
- "Show me lead time planning data"
- "Which SKUs can we trim to fit within capacity limits?"

### Additional Common Questions
- "Show me all SKUs"
- "Which SKUs have negative gross profit?"
- "What country is SKU001 from?"
- "Give me the top 3 SKUs by total revenue"
- "What is the average lead time for the Nuts category?"
- "Show me the dashboard"

## Testing Infrastructure

### 1. Comprehensive Test Suite (`test_left_nav_validation.py`)

Full test suite that validates all components of the left nav validation system:

- **Canned Queries Import Test**: Verifies canned queries can be loaded
- **Ground Truth Import Test**: Verifies ground truth validator works
- **Database Connection Test**: Ensures database connectivity
- **Canned Query Execution Test**: Tests actual query execution
- **Left Nav Questions Test**: Tests all left nav questions
- **Ground Truth Validation Test**: Runs full ground truth validation
- **Canned Query Cache Test**: Tests caching functionality

### 2. Smoke Test (`scripts/smoke_left_nav.py`)

Quick validation script for fast feedback during development:

- Tests critical left nav questions
- Validates canned query system
- Provides immediate feedback on system health

### 3. Integrated Test Suite (`test_stack.py`)

Updated existing test suite to include left nav validation:

- Added `test_left_nav_question()` function
- Added `run_left_nav_test()` function
- Integrated left nav testing into main test runner

## Usage

### Running Tests

#### Quick Smoke Test
```bash
python scripts/smoke_left_nav.py
```

#### Comprehensive Validation
```bash
python test_left_nav_validation.py
```

#### Integrated Test Suite
```bash
python test_stack.py
```

### Manual Testing

#### Test a Specific Question
```python
from solutions.tools.ground_truth_validator import validate_specific_question

result = validate_specific_question("What is the category of SKU001?")
print(f"Success: {result.success}")
print(f"Response: {result.response}")
```

#### Run Ground Truth Validation
```python
from solutions.tools.ground_truth_validator import run_ground_truth_validation

results = run_ground_truth_validation()
```

#### Check Canned Query Stats
```python
from solutions.tools.canned_queries import get_canned_query_stats

stats = get_canned_query_stats()
print(f"Available queries: {stats['available_queries']}")
print(f"Cache size: {stats['cache_size']}")
```

## Benefits

### 1. Reliability
- **100% Deterministic**: Canned queries always return the same result for the same input
- **No LLM Errors**: Eliminates LLM-generated cypher query errors
- **Consistent Formatting**: Pre-defined response templates ensure professional output

### 2. Performance
- **Fast Response**: Canned queries execute faster than LLM-based approaches
- **Caching**: 5-minute TTL cache reduces database load
- **Reduced API Calls**: Fewer LLM API calls for known questions

### 3. Maintainability
- **Easy to Update**: Add new canned queries by updating the dictionary
- **Version Control**: All queries are version-controlled in code
- **Testing**: Comprehensive test coverage prevents regressions

### 4. User Experience
- **Professional Responses**: Consistent, well-formatted responses
- **No Internal Messages**: Eliminates internal debugging messages
- **Fast Feedback**: Quick responses for common questions

## Monitoring and Metrics

### Event Tracking
The system tracks various events for monitoring:

- `canned_query.matched`: When a canned query is matched
- `canned_query.execution`: Query execution timing
- `canned_query.success`: Successful query execution
- `canned_query.error`: Query execution errors
- `canned_query.cache_hit`: Cache hit events
- `ground_truth.validation`: Ground truth validation results

### Performance Metrics
- **Response Times**: Tracked for all canned queries
- **Cache Hit Rate**: Percentage of requests served from cache
- **Success Rate**: Percentage of successful validations
- **Error Rates**: Tracked by query type and error type

## Future Enhancements

### 1. Dynamic Query Generation
- Use LLM to generate new canned queries based on user patterns
- Automatically add frequently asked questions to canned query set

### 2. Advanced Caching
- Implement Redis-based caching for distributed deployments
- Add cache warming for frequently accessed queries

### 3. A/B Testing
- Compare canned query responses with LLM responses
- Measure user satisfaction and response quality

### 4. Query Analytics
- Track which canned queries are most frequently used
- Identify patterns in user questions for optimization

## Troubleshooting

### Common Issues

#### 1. No Canned Query Match
**Symptoms**: Question not matched to any canned query
**Solution**: Check question patterns in `get_canned_queries()` and add new patterns if needed

#### 2. Database Connection Errors
**Symptoms**: "Database connection not available" errors
**Solution**: Check Neo4j connection settings and database availability

#### 3. Parameter Extraction Failures
**Symptoms**: Missing or incorrect parameters in queries
**Solution**: Review `extract_query_parameters()` function and add new extraction patterns

#### 4. Cache Issues
**Symptoms**: Slow responses or inconsistent caching
**Solution**: Check cache TTL settings and clear cache if needed

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export DEBUG_CANNED_QUERIES=1
```

This will provide detailed logging of:
- Query matching attempts
- Parameter extraction
- Cache operations
- Execution timing

## Conclusion

The left nav validation system provides a robust, reliable solution for handling all questions that appear in the left navigation. By using canned cypher queries with comprehensive ground truth validation, the system ensures:

1. **100% Reliability** for known questions
2. **Professional Responses** with consistent formatting
3. **Fast Performance** with intelligent caching
4. **Easy Maintenance** with comprehensive testing
5. **No Regressions** with ground truth validation

This system represents a significant improvement in the chatbot's reliability and user experience, particularly for the most commonly asked questions that appear in the left navigation.
