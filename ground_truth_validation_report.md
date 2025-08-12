
# 🧪 Ground Truth Validation Report

## 📊 Summary
- **Total Cases**: 23
- **Successful**: 8
- **Failed**: 15
- **Success Rate**: 34.8%

## ✅ Successful Cases (8)
- **sku_category_001**: What is the category of SKU001? (0.00s)
- **distinct_categories**: List the distinct product categories (0.00s)
- **distinct_categories_count**: How many distinct categories are there? (0.00s)
- **all_skus**: Show me all SKUs (0.00s)
- **top_revenue_sku**: Which SKU has the highest unit price? (0.13s)
- **top_gp_per_unit_sku**: Which SKU has the highest gross profit per unit? (0.00s)
- **country_with_most_skus**: Which country has the most SKUs? (0.00s)
- **skus_with_lead_time_over**: List up to 5 SKUs with lead time over 25 days (0.13s)

## ❌ Failed Cases (15)

### sku_country_001
- **Question**: What country is SKU001 from?
- **Errors**: Expected pattern 'country' not found in response
- **Response**: SKU001 is from **Argentina**.

### sku_details_001
- **Question**: Tell me about SKU001
- **Errors**: Expected pattern 'unit_price' not found in response, Expected pattern 'unit_cost' not found in response
- **Response**: 
# 📊 SKU Details: SKU001

## 🏷️ Basic Information
- **Name**: Product SKU001
- **Category**: Nuts
- **Country**: Argentina

## 💰 Financial Metrics
- **Unit Price**: $9.31
- **Unit Cost**: $6.32
- **Gr...

### all_skus_count
- **Question**: How many SKUs are there?
- **Errors**: Expected pattern 'count' not found in response
- **Response**: There are **501** SKUs in your portfolio.

### negative_gross_profit
- **Question**: Which SKUs have negative gross profit?
- **Errors**: Expected pattern 'negative' not found in response, Expected pattern 'gross profit' not found in response
- **Response**: No data found for your query.

### count_negative_gross_profit
- **Question**: How many SKUs have negative gross profit?
- **Errors**: Expected pattern 'negative' not found in response, Expected pattern 'gross profit' not found in response
- **Response**: There are **501** SKUs in your portfolio.

### total_skus_in_category
- **Question**: How many SKUs are in the Legumes category?
- **Errors**: Expected pattern 'Legumes' not found in response, Expected pattern 'count' not found in response
- **Response**: There are **501** SKUs in your portfolio.

### avg_lead_time_category
- **Question**: What is the average lead time for the Nuts category?
- **Errors**: Expected pattern 'Nuts' not found in response, Expected pattern 'average' not found in response, Expected pattern 'lead time' not found in response, Unexpected pattern 'Error' found in response, Unexpected pattern '❌' found in response, Response contains error indicators
- **Response**: ❌ Error executing query: {code: Neo.ClientError.Statement.ParameterMissing} {message: Expected parameter(s): sku_id}

### avg_unit_price_category
- **Question**: What is the average unit price for the Spices category?
- **Errors**: Expected pattern 'Spices' not found in response, Expected pattern 'average' not found in response, Expected pattern 'unit price' not found in response, Unexpected pattern 'Error' found in response, Unexpected pattern '❌' found in response, Response contains error indicators
- **Response**: ❌ Error executing query: {code: Neo.ClientError.Statement.ParameterMissing} {message: Expected parameter(s): sku_id}

### top_revenue_skus_n
- **Question**: Give me the top 3 SKUs by total revenue
- **Errors**: Expected pattern 'revenue' not found in response
- **Response**: 
# 🏆 Top 3 SKUs by Unit Price

- SKU320 | Product SKU320 | Spices | 24.67
- SKU341 | Product SKU341 | Spices | 24.05
- SKU232 | Product SKU232 | Spices | 23.70

## 📊 Summary
These are your top 3 highe...

### category_highest_avg_lead_time
- **Question**: Which category has the highest average lead time?
- **Errors**: Expected pattern 'highest' not found in response, Expected pattern 'average' not found in response, Expected pattern 'lead time' not found in response, Unexpected pattern 'Error' found in response, Unexpected pattern '❌' found in response, Response contains error indicators
- **Response**: ❌ Error executing query: {code: Neo.ClientError.Statement.ParameterMissing} {message: Expected parameter(s): category}

### excess_inventory_skus
- **Question**: Which SKUs have excess inventory that we can promote next month?
- **Errors**: Expected pattern 'excess' not found in response, Expected pattern 'inventory' not found in response, Expected pattern 'SKU' not found in response, Expected pattern 'promotion' not found in response
- **Response**: No data found for your query.

### regional_demand_variations
- **Question**: Analyze regional demand variations
- **Errors**: Expected pattern 'regional' not found in response, Expected pattern 'demand' not found in response, Expected pattern 'country' not found in response, Expected pattern 'analysis' not found in response
- **Response**: No data found for your query.

### manufacturing_constraints_proxy
- **Question**: Which SKUs have manufacturing constraints?
- **Errors**: Expected pattern 'manufacturing' not found in response, Expected pattern 'constraints' not found in response, Expected pattern 'SKU' not found in response, Expected pattern 'lead time' not found in response, Unexpected pattern 'Error' found in response, Unexpected pattern '❌' found in response, Response contains error indicators
- **Response**: ❌ Error executing query: {code: Neo.ClientError.Statement.ParameterMissing} {message: Expected parameter(s): threshold}

### skus_to_trim_proxy
- **Question**: Which SKUs can we trim to fit within capacity limits?
- **Errors**: Expected pattern 'capacity' not found in response
- **Response**: 
# ✂️ SKUs to Consider Trimming

Found **10** SKUs that may be candidates for trimming (negative profit or low price):

- SKU309 | Product SKU309 | Grains | 4.49 | 3.47 | 1.02
- SKU107 | Product SKU10...

### show_dashboard
- **Question**: Show me the dashboard
- **Errors**: No canned query match found, Expected pattern 'dashboard' not found in response, Expected pattern 'analytics' not found in response, Expected pattern 'charts' not found in response, Expected pattern 'KPIs' not found in response, Unexpected pattern '❌' found in response, Response contains error indicators
- **Response**: ❌ No canned query found for this question

## ⏱️ Performance Metrics
- **Average Response Time**: 0.05s
- **Cache Hits**: 0/23 (0.0%)

## 🔧 Recommendations
- ⚠️ 15 questions need attention
- 🔧 Review failed cases and fix underlying issues
- 🧪 Re-run validation after fixes
