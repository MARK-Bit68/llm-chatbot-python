#!/usr/bin/env python3
"""
Verification script to cross-check response accuracy with raw database data
"""

from graph import graph

def verify_data_accuracy():
    print('🔍 VERIFICATION: Cross-checking response accuracy with raw database data')

    # Test 1: Verify SKU001 category
    print('\n📊 Test 1: SKU001 Category Verification')
    raw_data = graph.query("MATCH (sku:SKU {sku_id: 'SKU001'}) RETURN sku.plot LIMIT 1")
    if raw_data:
        plot_data = raw_data[0]['sku.plot']
        print('Raw plot data:', plot_data[:200] + '...')
        
        # Extract category manually
        if 'category: ' in plot_data:
            category_start = plot_data.find('category: ') + len('category: ')
            category_end = plot_data.find(' | ', category_start)
            actual_category = plot_data[category_start:category_end]
            print('✅ Actual category from database:', actual_category)
        else:
            print('❌ Category not found in raw data')

    # Test 2: Verify price range
    print('\n📊 Test 2: Price Range Verification')
    price_query = """
    MATCH (sku:SKU)
    WITH sku, split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] as price
    WHERE price IS NOT NULL AND price <> ''
    RETURN min(toFloat(price)) as min_price, max(toFloat(price)) as max_price
    """
    price_result = graph.query(price_query)
    if price_result:
        print('✅ Actual price range from database:', price_result[0])
    else:
        print('❌ Price range query failed')

    # Test 3: Verify profit margin calculation
    print('\n📊 Test 3: Profit Margin Verification')
    margin_query = """
    MATCH (sku:SKU)
    WITH sku, 
         split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] as price,
         split(split(sku.plot, 'unit_cost: ')[1], ' | ')[0] as cost
    WHERE price IS NOT NULL AND cost IS NOT NULL AND price <> '' AND cost <> ''
    RETURN sku.sku_id, toFloat(price) as price, toFloat(cost) as cost, 
           (toFloat(price) - toFloat(cost)) as margin
    ORDER BY margin DESC
    LIMIT 3
    """
    margin_result = graph.query(margin_query)
    if margin_result:
        print('✅ Top 3 profit margins from database:')
        for row in margin_result:
            print(f'  {row["sku.sku_id"]}: Price=${row["price"]}, Cost=${row["cost"]}, Margin=${row["margin"]:.2f}')
    else:
        print('❌ Profit margin calculation failed')

    # Test 4: Verify all SKUs have data
    print('\n📊 Test 4: Data Completeness Verification')
    completeness_query = """
    MATCH (sku:SKU)
    RETURN count(sku) as total_skus,
           count(CASE WHEN sku.plot CONTAINS 'category: ' THEN 1 END) as with_category,
           count(CASE WHEN sku.plot CONTAINS 'unit_price: ' THEN 1 END) as with_price,
           count(CASE WHEN sku.plot CONTAINS 'unit_cost: ' THEN 1 END) as with_cost
    """
    completeness_result = graph.query(completeness_query)
    if completeness_result:
        data = completeness_result[0]
        print('✅ Data completeness:')
        print(f'  Total SKUs: {data["total_skus"]}')
        print(f'  With category: {data["with_category"]}')
        print(f'  With price: {data["with_price"]}')
        print(f'  With cost: {data["with_cost"]}')
        
        if data["total_skus"] == data["with_category"] == data["with_price"] == data["with_cost"]:
            print('✅ All SKUs have complete data')
        else:
            print('❌ Some SKUs missing data')
    else:
        print('❌ Completeness check failed')

    # Test 5: Compare our enhanced query with manual extraction
    print('\n📊 Test 5: Enhanced Query vs Manual Extraction')
    from solutions.tools.cypher import enhanced_cypher_qa
    
    enhanced_result = enhanced_cypher_qa("What is the category of SKU001?")
    print('Enhanced query result:', enhanced_result[:200] + '...' if len(enhanced_result) > 200 else enhanced_result)
    
    # Manual extraction for comparison
    manual_result = graph.query("""
    MATCH (sku:SKU {sku_id: 'SKU001'})
    RETURN split(split(sku.plot, 'category: ')[1], ' | ')[0] as category
    """)
    if manual_result:
        manual_category = manual_result[0]['category']
        print('Manual extraction result:', manual_category)
        
        # Check if enhanced result contains the manual result
        if manual_category in enhanced_result:
            print('✅ Enhanced query correctly contains manual extraction result')
        else:
            print('❌ Enhanced query does not match manual extraction')

    print('\n🎯 Verification complete!')

if __name__ == "__main__":
    verify_data_accuracy() 