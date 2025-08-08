#!/usr/bin/env python3
"""
Test S&OP Queries (Aliased)
Runs S&OP validation queries using explicit Cypher aliases to ensure fields map correctly.
"""
import os
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')


def get_neo4j_config(key: str, default: str = "") -> str:
    try:
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            with open(secrets_path, "r") as f:
                for line in f:
                    if line.startswith(f"{key}="):
                        return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return os.getenv(key, default)


def get_graph():
    try:
        from langchain_neo4j import Neo4jGraph
        graph = Neo4jGraph(
            url=get_neo4j_config("NEO4J_URI"),
            username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
            password=get_neo4j_config("NEO4J_PASSWORD"),
        )
        graph.query("RETURN 1 AS ok")
        return graph
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return None


def rows_to_dicts(rows, keys):
    dicts = []
    for r in rows:
        if isinstance(r, dict):
            dicts.append(r)
        else:
            # assume tuple ordering matches keys order
            d = {}
            for i, k in enumerate(keys):
                d[k] = r[i] if i < len(r) else None
            dicts.append(d)
    return dicts


class AliasedSOPQueryTester:
    def __init__(self):
        self.graph = get_graph()
        if not self.graph:
            raise RuntimeError("No Neo4j graph connection")

    def run(self):
        print("🚀 Running S&OP queries with explicit aliases...")
        print("=" * 60)

        # 1. Plants with high utilization
        print("\n📋 Manufacturing capacity constraints (plants with utilization > 0.8)")
        q1 = (
            "MATCH (plant:ManufacturingPlant) "
            "WHERE plant.utilization_rate > 0.8 "
            "RETURN plant.name AS plant_name, plant.total_capacity AS total_capacity, "
            "plant.available_capacity AS available_capacity, plant.utilization_rate AS utilization_rate "
            "ORDER BY plant.utilization_rate DESC LIMIT 5"
        )
        r1 = self.graph.query(q1)
        r1 = rows_to_dicts(r1, ["plant_name", "total_capacity", "available_capacity", "utilization_rate"])
        print(f"✅ {len(r1)} plants")
        for row in r1:
            print(f"  - {row['plant_name']} (Utilization: {row['utilization_rate']:.0%}, Available: {int(row['available_capacity'])})")

        # 2. Regions with demand variations
        print("\n📋 Regional demand variations")
        q2 = (
            "MATCH (reg:Region) "
            "RETURN reg.name AS region, reg.demand_multiplier AS demand_multiplier, reg.service_level AS service_level "
            "ORDER BY demand_multiplier DESC LIMIT 10"
        )
        r2 = self.graph.query(q2)
        r2 = rows_to_dicts(r2, ["region", "demand_multiplier", "service_level"])
        print(f"✅ {len(r2)} regions")
        for row in r2:
            print(f"  - {row['region']} (Multiplier: {row['demand_multiplier']:.2f}, Service: {row['service_level']:.0%})")

        # 3. SKUs with lead time data
        print("\n📋 SKUs with lead time data (top 10 by lead time)")
        q3 = (
            "MATCH (sku:SKU) WHERE sku.lead_time_days > 0 "
            "RETURN sku.sku_id AS sku_id, sku.name AS name, sku.lead_time_days AS lead_time_days, "
            "sku.manufacturing_plant AS plant, sku.region AS region "
            "ORDER BY lead_time_days DESC LIMIT 10"
        )
        r3 = self.graph.query(q3)
        r3 = rows_to_dicts(r3, ["sku_id", "name", "lead_time_days", "plant", "region"])
        print(f"✅ {len(r3)} SKUs")
        for row in r3:
            print(f"  - {row['name']} ({row['sku_id']}) - Lead Time: {int(row['lead_time_days'])} days, Plant: {row['plant']}, Region: {row['region']}")

        # 4. Inventory safety stock and reorder
        print("\n📋 Safety stock and reorder analysis")
        q4 = (
            "MATCH (sku:SKU)-[:HAS_INVENTORY]->(inv:Inventory) "
            "WHERE inv.safety_stock > 0 AND sku.reorder_point > 0 "
            "RETURN sku.sku_id AS sku_id, sku.name AS name, inv.safety_stock AS safety_stock, sku.reorder_point AS reorder_point, sku.max_inventory AS max_inventory "
            "ORDER BY safety_stock DESC LIMIT 10"
        )
        r4 = self.graph.query(q4)
        r4 = rows_to_dicts(r4, ["sku_id", "name", "safety_stock", "reorder_point", "max_inventory"])
        print(f"✅ {len(r4)} SKUs")
        for row in r4:
            print(f"  - {row['name']} ({row['sku_id']}) - Safety: {int(row['safety_stock'])}, Reorder: {int(row['reorder_point'])}")

        # 5. Excess inventory identification
        print("\n📋 Excess inventory identification")
        q5 = (
            "MATCH (sku:SKU)-[:HAS_INVENTORY]->(inv:Inventory) "
            "WHERE inv.initial_inventory > sku.reorder_point * 1.5 "
            "RETURN sku.sku_id AS sku_id, sku.name AS name, inv.initial_inventory AS initial_inventory, sku.reorder_point AS reorder_point "
            "ORDER BY initial_inventory DESC LIMIT 10"
        )
        r5 = self.graph.query(q5)
        r5 = rows_to_dicts(r5, ["sku_id", "name", "initial_inventory", "reorder_point"])
        print(f"✅ {len(r5)} SKUs")
        for row in r5:
            print(f"  - {row['name']} ({row['sku_id']}) - Inventory: {int(row['initial_inventory'])}, Reorder: {int(row['reorder_point'])}")

        # 6. Customers with priority and revenue
        print("\n📋 Customer prioritization matrix")
        q6 = (
            "MATCH (cust:Customer) "
            "RETURN cust.customer_id AS customer_id, cust.name AS name, cust.priority_level AS priority_level, "
            "cust.priority_score AS priority_score, cust.total_revenue AS total_revenue "
            "ORDER BY priority_score DESC, total_revenue DESC LIMIT 10"
        )
        r6 = self.graph.query(q6)
        r6 = rows_to_dicts(r6, ["customer_id", "name", "priority_level", "priority_score", "total_revenue"])
        print(f"✅ {len(r6)} customers")
        for row in r6:
            print(f"  - {row['name']} ({row['customer_id']}) - Priority: {row['priority_level']}, Score: {int(row['priority_score'])}, Revenue: ${row['total_revenue']:,.0f}")

        print("\n🎉 Aliased S&OP queries finished.")


if __name__ == "__main__":
    AliasedSOPQueryTester().run()