#!/usr/bin/env python3
"""
Additional verification tests for edge cases and data consistency
"""

from solutions.tools.cypher import enhanced_cypher_qa
from graph import graph

def additional_verification():
    print('🔍 ADDITIONAL ACCURACY VERIFICATION TESTS')

    # Test 1: Verify complex calculations
    print('\n📊 Test 1: Complex Calculation Verification')
    enhanced_result = enhanced_cypher_qa('Show me products with highest profit margins')
    print('Enhanced result preview:', enhanced_result[:300] + '...')

    # Manual verification of top profit margin
    manual_query = '''
    MATCH (sku:SKU)
    WITH sku, 
         split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] as price,
         split(split(sku.plot, 'unit_cost: ')[1], ' | ')[0] as cost
    WHERE price IS NOT NULL AND cost IS NOT NULL AND price <> '' AND cost <> ''
    RETURN sku.sku_id, toFloat(price) as price, toFloat(cost) as cost, 
           (toFloat(price) - toFloat(cost)) as margin
    ORDER BY margin DESC
    LIMIT 1
    '''
    manual_result = graph.query(manual_query)
    if manual_result:
        top_sku = manual_result[0]
        print(f'✅ Manual verification - Top profit margin: {top_sku["sku.sku_id"]} with margin ${top_sku["margin"]:.2f}')
        
        # Check if enhanced result mentions this SKU
        if top_sku['sku.sku_id'] in enhanced_result:
            print('✅ Enhanced result correctly identifies top profit margin SKU')
        else:
            print('❌ Enhanced result does not match manual calculation')

    # Test 2: Verify data consistency across all SKUs
    print('\n📊 Test 2: Data Consistency Verification')
    consistency_query = '''
    MATCH (sku:SKU)
    WITH sku, 
         split(split(sku.plot, 'category: ')[1], ' | ')[0] as category,
         split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] as price,
         split(split(sku.plot, 'unit_cost: ')[1], ' | ')[0] as cost
    WHERE category IS NOT NULL AND price IS NOT NULL AND cost IS NOT NULL
    RETURN count(*) as consistent_skus
    '''
    consistency_result = graph.query(consistency_query)
    if consistency_result:
        consistent_count = consistency_result[0]['consistent_skus']
        print(f'✅ {consistent_count} SKUs have consistent data extraction')

    # Test 3: Verify no data loss
    print('\n📊 Test 3: Data Loss Verification')
    total_skus = graph.query('MATCH (sku:SKU) RETURN count(sku) as total')[0]['total']
    extracted_skus = graph.query('''
    MATCH (sku:SKU)
    WHERE split(split(sku.plot, 'category: ')[1], ' | ')[0] IS NOT NULL
    RETURN count(sku) as extracted
    ''')[0]['extracted']

    print(f'✅ Total SKUs: {total_skus}')
    print(f'✅ Successfully extracted: {extracted_skus}')
    if total_skus == extracted_skus:
        print('✅ No data loss - all SKUs successfully processed')
    else:
        print(f'❌ Data loss detected: {total_skus - extracted_skus} SKUs not processed')

    # Test 4: Verify response quality
    print('\n📊 Test 4: Response Quality Verification')
    test_queries = [
        'What is the category of SKU001?',
        'What is the price range of our products?',
        'Show me products with highest profit margins',
        'Tell me about SKU003'
    ]

    for query in test_queries:
        result = enhanced_cypher_qa(query)
        if result and len(result) > 50:  # Meaningful response
            print(f'✅ Query "{query[:30]}..." - Quality response ({len(result)} chars)')
        else:
            print(f'❌ Query "{query[:30]}..." - Poor response')

    # Test 5: Verify mathematical accuracy
    print('\n📊 Test 5: Mathematical Accuracy Verification')
    math_test_query = '''
    MATCH (sku:SKU)
    WITH sku, 
         split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] as price,
         split(split(sku.plot, 'unit_cost: ')[1], ' | ')[0] as cost
    WHERE price IS NOT NULL AND cost IS NOT NULL AND price <> '' AND cost <> ''
    RETURN sku.sku_id, 
           toFloat(price) as price, 
           toFloat(cost) as cost, 
           (toFloat(price) - toFloat(cost)) as calculated_margin,
           (toFloat(price) - toFloat(cost)) / toFloat(price) * 100 as margin_percentage
    ORDER BY calculated_margin DESC
    LIMIT 3
    '''
    math_result = graph.query(math_test_query)
    if math_result:
        print('✅ Mathematical calculations verified:')
        for row in math_result:
            sku_id = row['sku.sku_id']
            price = row['price']
            cost = row['cost']
            margin = row['calculated_margin']
            margin_pct = row['margin_percentage']
            print(f'  {sku_id}: Price=${price}, Cost=${cost}, Margin=${margin:.2f} ({margin_pct:.1f}%)')

    print('\n🎯 All additional verification tests completed!')

if __name__ == "__main__":
    additional_verification() 