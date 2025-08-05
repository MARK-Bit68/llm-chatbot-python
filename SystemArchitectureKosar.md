# System Architecture: Leveraging a Graph Database Beyond Vector Search

---

## 2. The Dual-Tool Approach: Vector Search and Graph Query

The application's "brain" is a ReAct agent that has access to two primary data retrieval tools:

1.  **`Entity Information Search` (Vector Search)**: This tool is designed for semantic similarity or "fuzzy" searches. It leverages a vector index (`skuPlots`) built on the `SKU` nodes in the Neo4j database. Its primary function is to find products based on conceptual similarity to a user's query.

2.  **`Enhanced Database Query` (Graph Query)**: This is the system's powerhouse tool. It is explicitly instructed to handle the vast majority of queries, including any request for a specific SKU, all SKUs, analytics, aggregations, or general data exploration. It uses a Large Language Model (LLM) to dynamically generate precise Cypher queries that run directly against the graph database.

The agent's prompting heavily prioritizes the `Enhanced Database Query` tool, establishing the graph as the default and more powerful option, with vector search reserved as a fallback for when semantic context is more important than analytical precision.

---

## 3. The Role of Vector Search: A Semantic Entry Point

The vector search component is implemented using `langchain_neo4j.Neo4jVector`. It indexes an embedding of the `plot` property of each `SKU` node, which is a text blob containing all information about the product.

**Use Cases:**
*   **Conceptual Similarity**: Answering questions like, "What products are similar to our premium coffee beans?"
*   **Fuzzy Matching**: Finding relevant products when the user's query is vague or doesn't use exact keywords.

**How it Works**: The user's query is embedded into a vector, and the system performs a cosine similarity search against the pre-computed vectors in the `skuPlots` index. It retrieves the most similar `SKU` nodes.

**Limitation**: Vector search is fundamentally about similarity, not analytics. It can find *what* is relevant, but it cannot compute, aggregate, or answer complex questions about *why* or *how*. It cannot answer a question like, "What is the total revenue for all products in the 'Legumes' category?"

---

## 4. The Power of the Graph: Analytics, Precision, and Context

The true analytical capability of the application comes from the graph database, accessed via the `Enhanced Database Query` tool. This tool does not rely on pre-defined queries; it dynamically generates Cypher queries based on the user's specific question.

### 4.1. The Data Model

The data is modeled as a collection of `SKU` nodes. While the ingestion script suggests a more complex model with relationships, the `cypher.py` tool's prompt reveals a pragmatic simplification: each `SKU` node contains a rich `plot` property—a pipe-separated string of key-value pairs (e.g., `category: Legumes | country: Country B | unit_price: 10.9 | ...`). The dynamic Cypher generation is designed to parse this string on the fly.

### 4.2. Capabilities Beyond Vector Search

This graph-centric approach unlocks several critical capabilities:

| Capability | Example User Query | Why Vector Search Fails | Why Graph Search Succeeds |
| :--- | :--- | :--- | :--- |
| **Precise Lookups** | "Tell me everything about SKU001." | Might return *similar* SKUs, not necessarily the exact one. Lacks precision. | A `MATCH (sku:SKU {sku_id: 'SKU001'})` query pinpoints the exact node and returns all its data. |
| **Complex Filtering** | "Show me SKUs in Country B with negative gross profit." | Cannot perform structured filtering on multiple, disparate properties (country and profit). | The LLM generates a Cypher query with a `WHERE` clause that filters on `country` and `gross_profit` parsed from the `plot` string. |
| **Aggregation & Analytics** | "What is the average lead time for each product category?" | Has no mechanism for grouping nodes or performing mathematical operations like `avg()`. | The LLM generates a query that groups by `category` and calculates the average `lead_time_days` for each group. |
| **Multi-Hop Queries (Conceptual)** | "Which suppliers provide products with >30 day lead times?" | Cannot traverse relationships. It only knows about individual documents (nodes). | A graph can traverse relationships from `Supplier` to `SKU` to answer such questions (though this model is flat, the principle holds). |

### 4.3. Example Query Flow: An Analytical Question

Consider the query: **"What is the total revenue for products in the 'Legumes' category in Country B?"**

1.  **Agent Receives Query**: The agent's LLM recognizes this is not a similarity search but an analytical question requiring filtering (`category`, `country`) and aggregation (`sum`).
2.  **Tool Selection**: It correctly chooses the `Enhanced Database Query` tool.
3.  **Dynamic Cypher Generation**: The tool's own LLM, guided by its detailed prompt, generates the following Cypher query:
    ```cypher
    MATCH (sku:SKU)
    WHERE split(split(sku.plot, 'category: ')[1], ' | ')[0] = 'Legumes'
      AND split(split(sku.plot, 'country: ')[1], ' | ')[0] = 'Country B'
    RETURN sum(toFloat(split(split(sku.plot, 'revenue: ')[1], ' | ')[0])) as total_revenue
    ```
4.  **Execution & Result**: The query is executed directly on the Neo4j database, which performs the filtering and aggregation efficiently. It returns a single, precise numerical answer.

A pure vector search system would be incapable of executing this request. It might find SKUs related to "Legumes" and "Country B," but it could not perform the `sum()` aggregation or enforce the `AND` condition with certainty.

---

## 5. Interactive Dashboard Integration

The system includes a **dynamic dashboard component** that integrates seamlessly within the chat interface, providing visual analytics and real-time insights.

### 5.1. Dashboard Architecture

The dashboard is implemented as a **component-based system** that renders within the existing Streamlit chat interface:

- **`dashboard_component.py`**: Core dashboard functionality with data extraction and visualization
- **Modified `bot.py`**: Enhanced with keyword detection for dashboard requests
- **Real-time Integration**: Charts render directly within chat messages

### 5.2. Dashboard Capabilities

#### **Data Integration**
- **Live Neo4j Connection**: Real-time data extraction from production database
- **Rich Data Processing**: 10 SKUs, 5 categories, 2 countries, 18 months of data
- **Financial Analytics**: $930K revenue, $326K profit, 35.1% margin calculations

#### **Interactive Visualizations**
1. **Key Metrics Cards**: Revenue, volume, margin, unit price at a glance
2. **Monthly Trends Chart**: Demand vs Supply vs Inventory with category/country filters
3. **Category Performance**: Pie charts and detailed metrics tables
4. **SKU Performance**: Bar charts comparing demand vs supply across all products
5. **Geographic Distribution**: Country-specific performance analysis
6. **Detailed Metrics Table**: Complete SKU-level financial data with formatting

### 5.3. User Experience

#### **Natural Integration**
- **Keyword Detection**: Automatically triggers on dashboard-related queries
- **Seamless Rendering**: Charts appear within chat conversation flow
- **Interactive Filters**: Category and country selection within dashboard
- **Professional Visualizations**: Plotly charts with responsive design

#### **Trigger Keywords**
The dashboard activates when users type:
- "Show me a dashboard"
- "Generate a report"
- "Create charts and graphs"
- "Display analytics"
- "Show me KPIs"

### 5.4. Technical Implementation

#### **Data Processing Pipeline**
```python
# Real-time data extraction from Neo4j
result = graph.query("MATCH (sku:SKU) RETURN sku.plot as plot_data")

# Complex string parsing for rich data structure
pairs = plot_data.split(' | ')
for pair in pairs:
    key, value = pair.split(':', 1)
    data_dict[key.strip()] = value.strip()

# Monthly data aggregation (18 months × 10 SKUs)
monthly_data = []
for month in ['jan_2024', ..., 'jun_2025']:
    monthly_data.append({
        'demand': row[month],
        'supply': row.get(f'Supply Plan: {month.split("_")[0].title()}', 0),
        'inventory': row.get(f'Inventory Plan: {month.split("_")[0].title()}', 0)
    })
```

#### **Visualization Engine**
- **Plotly Integration**: Interactive charts with hover effects and zoom
- **Streamlit Components**: Native integration with chat interface
- **Responsive Design**: Works on desktop and mobile devices
- **State Management**: Filter persistence across interactions

### 5.5. Business Insights

The dashboard reveals critical supply chain insights:

#### **Category Performance**
1. **Dried Fruits**: $476K revenue, 59% margin (Star performer)
2. **Legumes**: $180K revenue, 54% margin (Strong performer)
3. **Grains**: $75K revenue, 15% margin (Needs optimization)
4. **Nuts**: $138K revenue, -20% margin (Critical attention needed)
5. **Spices**: $60K revenue, -33% margin (Immediate intervention required)

#### **Supply Chain Gaps**
- **Demand-Supply Mismatches**: Identified specific SKUs with supply gaps
- **Seasonal Patterns**: 18-month trends visible across all categories
- **Geographic Variations**: Clear differences between Country A and B performance
- **Financial Optimization**: Revenue and margin analysis by category

This dashboard integration demonstrates how the system combines **analytical precision** (graph queries) with **visual insights** (interactive charts) to provide comprehensive supply chain intelligence within a natural chat interface.

