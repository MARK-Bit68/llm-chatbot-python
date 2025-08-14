# Enhanced FMCG SOP Dataset - Memgraph Graph Database Analyzer

This standalone application loads the Enhanced FMCG SOP dataset into Memgraph and provides visualization capabilities through Memgraph Lab.

## 🎯 Overview

The Enhanced FMCG SOP Dataset contains comprehensive supply chain data including:
- **500 SKUs** across 5 product categories (Legumes, Dried Fruits, Nuts, Grains, Spices)
- **3 countries** with multi-regional operations
- **$76.3M total revenue** with detailed financial metrics
- **221 days** of temporal data (Jan 1 - Aug 9, 2023)
- **Complex graph structure** with production, storage, and relationship data

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Make the setup script executable
chmod +x setup_memgraph_fmcg.sh

# Run the automated setup
./setup_memgraph_fmcg.sh
```

### Option 2: Manual Setup

1. **Start Memgraph:**
```bash
docker run -d \
    --name memgraph-fmcg \
    -p 7687:7687 \
    -p 7444:7444 \
    -p 3000:3000 \
    memgraph/memgraph-platform
```

2. **Install Python dependencies:**
```bash
pip install pandas openpyxl gqlalchemy
```

3. **Run the analyzer:**
```bash
python memgraph_fmcg_analyzer.py
```

## 📊 What Gets Loaded

### Node Types
- **Product**: 500 SKUs with pricing, costs, lead times
- **Category**: 5 product categories (Legumes, Dried Fruits, Nuts, Grains, Spices)
- **Country**: 3 countries (Country A, B, C)
- **GraphNode**: 40+ supply chain nodes with group/subgroup classifications
- **Date**: 221 date nodes for temporal analysis

### Relationship Types
- **BELONGS_TO**: Product → Category
- **OPERATES_IN**: Product → Country
- **Graph relationships**: Various supply chain connections
- **Temporal relationships**: Production, Sales, Delivery, Factory Issue data

### Properties
- **Financial**: Revenue, margins, costs, volumes
- **Operational**: Lead times, reorder points, inventory levels
- **Temporal**: Daily production, sales, and delivery values
- **Graph**: Group/subgroup classifications, connectivity data

## 🔍 Sample Queries

### Business Analytics

```cypher
// Top 5 products by revenue
MATCH (p:Product)
WHERE p.total_revenue IS NOT NULL
RETURN p.code as product, p.total_revenue as revenue
ORDER BY p.total_revenue DESC
LIMIT 5
```

```cypher
// Category performance analysis
MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
WHERE p.gross_margin IS NOT NULL
RETURN c.name as category, 
       count(p) as product_count,
       avg(p.gross_margin) as avg_margin,
       sum(p.total_revenue) as total_revenue
ORDER BY total_revenue DESC
```

```cypher
// Country performance comparison
MATCH (p:Product)-[:OPERATES_IN]->(co:Country)
WHERE p.total_revenue IS NOT NULL
RETURN co.name as country,
       count(p) as product_count,
       sum(p.total_revenue) as total_revenue,
       avg(p.gross_margin) as avg_margin
ORDER BY total_revenue DESC
```

### Supply Chain Analysis

```cypher
// Products with longest lead times
MATCH (p:Product)
WHERE p.lead_time IS NOT NULL
RETURN p.code as product, p.lead_time as lead_time_days
ORDER BY p.lead_time DESC
LIMIT 10
```

```cypher
// Graph node connectivity
MATCH (n:GraphNode)-[r]->(m:GraphNode)
RETURN n.code as source, m.code as target, type(r) as relationship
LIMIT 20
```

### Temporal Analysis

```cypher
// Production patterns over time
MATCH (p:Product)-[r:RAW_PRODUCTION_UNIT]->(d:Date)
WHERE p.code = 'SKU001'
RETURN d.value as date, r.value as production_volume
ORDER BY d.value
LIMIT 30
```

```cypher
// Sales vs Production correlation
MATCH (p:Product)-[prod:RAW_PRODUCTION_UNIT]->(d:Date)
MATCH (p)-[sales:RAW_SALESORDER_UNIT]->(d)
WHERE p.code = 'SKU001'
RETURN d.value as date, 
       prod.value as production, 
       sales.value as sales
ORDER BY d.value
LIMIT 30
```

## 🌐 Using Memgraph Lab

1. **Access Memgraph Lab:**
   - Open http://localhost:3000 in your browser
   - The application will automatically open this URL

2. **Connect to Database:**
   - Host: `localhost`
   - Port: `7687`
   - Username: (leave empty)
   - Password: (leave empty)
   - Database: `memgraph`

3. **Explore the Graph:**
   - Use the **Query** tab to run Cypher queries
   - Use the **Schema** tab to explore node and relationship types
   - Use the **Graph** tab for visual exploration
   - Use the **Data** tab to browse node properties

## 🛠️ Advanced Queries

### Complex Business Analysis

```cypher
// Find high-margin products with low lead times
MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
WHERE p.gross_margin > 50 AND p.lead_time < 20
RETURN p.code as product, 
       c.name as category,
       p.gross_margin as margin,
       p.lead_time as lead_time
ORDER BY p.gross_margin DESC
```

```cypher
// Inventory optimization analysis
MATCH (p:Product)
WHERE p.reorder_point IS NOT NULL AND p.max_inventory IS NOT NULL
RETURN p.code as product,
       p.reorder_point as reorder_point,
       p.max_inventory as max_inventory,
       p.max_inventory - p.reorder_point as safety_stock
ORDER BY safety_stock DESC
```

### Network Analysis

```cypher
// Find central nodes in the supply chain
MATCH (n:GraphNode)
OPTIONAL MATCH (n)-[r1]->()
OPTIONAL MATCH ()-[r2]->(n)
RETURN n.code as node,
       n.group as group,
       count(r1) as outbound,
       count(r2) as inbound,
       count(r1) + count(r2) as total_connections
ORDER BY total_connections DESC
```

```cypher
// Find supply chain paths
MATCH path = (start:GraphNode)-[*1..3]->(end:GraphNode)
WHERE start.code = 'SOS008L02P' AND end.code = 'POV005L04P'
RETURN path
LIMIT 5
```

## 📈 Visualization Tips

### In Memgraph Lab

1. **Color coding**: Use node properties to color nodes by category, country, or group
2. **Size coding**: Use revenue or volume properties to size nodes
3. **Layout**: Try different layout algorithms (Force-directed, Hierarchical, etc.)
4. **Filters**: Use property filters to focus on specific subsets
5. **Expand**: Click on nodes to expand their relationships

### Custom Visualizations

```cypher
// Create a category-based view
MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
RETURN p, c
```

```cypher
// Create a country-based view
MATCH (p:Product)-[:OPERATES_IN]->(co:Country)
RETURN p, co
```

## 🔧 Troubleshooting

### Common Issues

1. **Memgraph not starting:**
   ```bash
   # Check if port 7687 is available
   lsof -i :7687
   
   # Stop existing container
   docker stop memgraph-fmcg
   docker rm memgraph-fmcg
   
   # Start fresh
   docker run -d --name memgraph-fmcg -p 7687:7687 -p 7444:7444 -p 3000:3000 memgraph/memgraph-platform
   ```

2. **Connection errors:**
   - Ensure Memgraph is running: `docker ps | grep memgraph`
   - Check logs: `docker logs memgraph-fmcg`
   - Wait for startup: Memgraph takes 10-30 seconds to fully start

3. **Excel file not found:**
   - Ensure `Enhanced_FMCG_SOP_Dataset.xlsx` is in the same directory
   - Check file permissions

4. **Python dependencies:**
   ```bash
   pip install --upgrade pandas openpyxl gqlalchemy
   ```

### Performance Tips

1. **Large queries**: Use LIMIT clauses for initial exploration
2. **Complex patterns**: Break down complex queries into smaller parts
3. **Indexing**: The script creates constraints that act as indexes
4. **Memory**: Memgraph uses in-memory storage, so large datasets need sufficient RAM

## 📚 Data Schema Reference

### Node Labels
- `Product`: Individual SKUs with business properties
- `Category`: Product categories (Legumes, Dried Fruits, etc.)
- `Country`: Geographic regions (Country A, B, C)
- `GraphNode`: Supply chain network nodes
- `Date`: Temporal nodes for time-series analysis

### Relationship Types
- `BELONGS_TO`: Product → Category
- `OPERATES_IN`: Product → Country
- `RAW_EDGES_*`: Supply chain network relationships
- `RAW_PRODUCTION_UNIT`: Product → Date (production data)
- `RAW_SALESORDER_UNIT`: Product → Date (sales data)
- `RAW_DELIVERYTO_UNIT`: Product → Date (delivery data)
- `RAW_FACTORYISSUE_UNIT`: Product → Date (factory data)

### Key Properties
- `code`: Unique identifier for products and nodes
- `total_revenue`: Financial performance metric
- `gross_margin`: Profitability metric
- `lead_time`: Operational efficiency metric
- `reorder_point`: Inventory management metric
- `value`: Temporal data values

## 🎯 Use Cases

1. **Supply Chain Optimization**: Analyze network relationships and bottlenecks
2. **Demand Forecasting**: Study temporal patterns and seasonality
3. **Financial Analysis**: Compare profitability across products and regions
4. **Inventory Management**: Optimize reorder points and safety stock
5. **Network Analysis**: Identify critical nodes and relationships
6. **Performance Benchmarking**: Compare products, categories, and countries

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Memgraph documentation: https://memgraph.com/docs
3. Check the application logs for detailed error messages

## 🔄 Maintenance

### Regular Tasks
- **Backup data**: Export important queries and visualizations
- **Clean up**: Remove old containers if needed
- **Update dependencies**: Keep Python packages updated

### Useful Commands
```bash
# Stop Memgraph
docker stop memgraph-fmcg

# Start Memgraph
docker start memgraph-fmcg

# Remove Memgraph (data will be lost)
docker rm memgraph-fmcg

# View logs
docker logs memgraph-fmcg

# Access Memgraph shell
docker exec -it memgraph-fmcg mg_client
```
