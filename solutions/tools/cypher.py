from langchain_neo4j import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate

from llm import llm
from graph import graph

CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Developer translating user questions into Cypher to answer questions about FMCG supply chain data and provide recommendations.
Convert the user's question based on the schema.

Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

Do not return entire nodes or embedding properties.

Fine Tuning:

For SKU codes, use the exact SKU format (e.g., "SKU001", "SKU002").

Example Cypher Statements:

1. To find the category of a SKU:
```
MATCH (sku:SKU {{sku_id: "SKU001"}})-[:BELONGS_TO_CATEGORY]->(cat:Category)
RETURN cat.name
```

2. To find demand plan for a SKU:
```
MATCH (sku:SKU {{sku_id: "SKU001"}})-[:HAS_DEMAND_PLAN]->(dp:DemandPlan)
RETURN dp.monthly_data
```

3. To find all SKUs in a category:
```
MATCH (sku:SKU)-[:BELONGS_TO_CATEGORY]->(cat:Category {{name: "Legumes"}})
RETURN sku.sku_id, sku.name
```

4. To find financial information for a SKU:
```
MATCH (sku:SKU {{sku_id: "SKU001"}})
RETURN sku.plot
```
Note: Financial data (unit_price, unit_cost, revenue, cogs, gross_profit) is embedded in the plot text and needs to be parsed from the returned text.

5. To find demand and financial data for what-if analysis:
```
MATCH (sku:SKU {{sku_id: "SKU001"}})-[:HAS_DEMAND_PLAN]->(dp:DemandPlan)
MATCH (sku:SKU {{sku_id: "SKU001"}})
RETURN dp.monthly_data, sku.plot
```
Note: This returns both demand data and financial data for cost impact analysis.

6. To find inventory information for a SKU:
```
MATCH (sku:SKU {{sku_id: "SKU001"}})-[:HAS_INVENTORY]->(inv:Inventory)
RETURN inv.monthly_data
```

Schema:
{schema}

Question:
{question}
"""

cypher_prompt = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)

cypher_qa = GraphCypherQAChain.from_llm(
    llm,
    graph=graph,
    verbose=True,
    cypher_prompt=cypher_prompt,
    allow_dangerous_requests=True
)