#!/usr/bin/env python3
"""
Memgraph Database Summary - Check what data is loaded
"""

from neo4j import GraphDatabase

def main():
    print("🔍 Memgraph Database Summary")
    print("=" * 50)
    
    try:
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("", ""))
        
        with driver.session() as session:
            # Get node counts by label
            print("\n📊 Node Counts by Label:")
            
            # Count different node types
            node_types = ["GraphNode", "Product", "Location", "TemporalEvent"]
            for node_type in node_types:
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                count = result.single()["count"]
                print(f"   {node_type}: {count}")
            
            # Get relationship counts by type
            print("\n🔗 Relationship Counts by Type:")
            
            # Count different relationship types
            rel_types = ["AVAILABLE_AT", "SHIPS_TO", "GROUP", "SUBGROUP", "PLANT", "STORAGE", 
                        "DELIVERYTO_UNIT", "DELIVERYTO_WEIGH", "FACTORYISSUE_UNIT", "FACTORYISSUE_WEIGHT",
                        "PRODUCTION_UNIT", "PRODUCTION_WEIGHT", "SALESORDER_UNIT", "SALESORDER_WEIGHT"]
            
            for rel_type in rel_types:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                count = result.single()["count"]
                if count > 0:
                    print(f"   {rel_type}: {count}")
            
            # Sample data from each node type
            print("\n📋 Sample Data:")
            
            # GraphNode samples
            result = session.run("MATCH (n:GraphNode) RETURN n.code, n.type, n.name LIMIT 5")
            print("\n   GraphNode samples:")
            for record in result:
                print(f"     {record['n.code']} ({record['n.type']}): {record['n.name']}")
            
            # Product samples (if any)
            result = session.run("MATCH (p:Product) RETURN p.code, p.name, p.category LIMIT 5")
            products = list(result)
            if products:
                print("\n   Product samples:")
                for record in products:
                    print(f"     {record['p.code']}: {record['p.name']} ({record['p.category']})")
            else:
                print("\n   No Product nodes found")
            
            # Location samples (if any)
            result = session.run("MATCH (l:Location) RETURN l.code, l.name, l.type LIMIT 5")
            locations = list(result)
            if locations:
                print("\n   Location samples:")
                for record in locations:
                    print(f"     {record['l.code']}: {record['l.name']} ({record['l.type']})")
            else:
                print("\n   No Location nodes found")
            
            # TemporalEvent samples
            result = session.run("MATCH (t:TemporalEvent) RETURN t.date, t.type LIMIT 5")
            print("\n   TemporalEvent samples:")
            for record in result:
                print(f"     {record['t.date']}: {record['t.type']}")
            
            # Sample relationships
            print("\n🔗 Sample Relationships:")
            result = session.run("""
                MATCH (n1)-[r]->(n2)
                RETURN labels(n1)[0] as from_label, type(r) as rel_type, labels(n2)[0] as to_label
                LIMIT 10
            """)
            
            for record in result:
                print(f"     {record['from_label']} -[{record['rel_type']}]-> {record['to_label']}")
        
        driver.close()
        
        print("\n🎉 Summary complete!")
        print("🌐 Open Memgraph Lab at: http://localhost:3000 to explore the data visually")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
