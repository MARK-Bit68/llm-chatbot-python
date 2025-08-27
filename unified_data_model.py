#!/usr/bin/env python3
"""
Unified Data Model for FMCG Supply Chain Analytics

This module provides a standardized schema for all ingestion scripts and ensures
dashboard compatibility across different datasets.

USAGE:
    # Basic usage
    from unified_data_model import get_unified_model, validate_dashboard_compatibility
    
    # Get model instance
    model = get_unified_model()
    if model:
        # Validate schema
        result = model.validate_schema()
        print(f"Schema valid: {result.is_valid}")
        print(f"Products: {result.node_count}")
    
    # Quick validation
    result = validate_dashboard_compatibility()
    print(f"Dashboard ready: {result.is_valid}")

COMMAND LINE:
    python unified_data_model.py  # Test the model and validate current schema

CORE PRINCIPLES:
1. Single source of truth for data schema
2. Backward compatibility with existing data
3. Schema validation for all ingestion scripts
4. Dashboard compatibility guarantee

REQUIREMENTS:
- Neo4j database connection (configured in .streamlit/secrets.toml)
- Python 3.7+
- langchain_neo4j package
"""

from __future__ import annotations

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
from langchain_neo4j import Neo4jGraph

logger = logging.getLogger(__name__)

class NodeType(Enum):
    """Standardized node types"""
    PRODUCT = "Product"
    SKU = "SKU"  # Legacy support
    CATEGORY = "Category"
    GROUP = "Group"
    SUBGROUP = "SubGroup"
    PLANT = "Plant"
    STORAGE = "StorageLocation"
    COUNTRY = "Country"
    REGION = "Region"
    BRAND = "Brand"
    DEMAND_PLAN = "DemandPlan"
    SUPPLY_PLAN = "SupplyPlan"
    INVENTORY = "Inventory"

class RelationshipType(Enum):
    """Standardized relationship types"""
    BELONGS_TO = "BELONGS_TO"
    IN_GROUP = "IN_GROUP"
    IN_SUBGROUP = "IN_SUBGROUP"
    PRODUCED_AT = "PRODUCED_AT"
    STORED_AT = "STORED_AT"
    OPERATES_IN = "OPERATES_IN"
    HAS_DEMAND_PLAN = "HAS_DEMAND_PLAN"
    HAS_SUPPLY_PLAN = "HAS_SUPPLY_PLAN"
    HAS_INVENTORY = "HAS_INVENTORY"
    BRANDED_AS = "BRANDED_AS"

@dataclass
class ProductSchema:
    """Standardized Product node schema"""
    # Core identifiers
    sku_code: str
    name: str
    
    # Classification
    category: Optional[str] = None
    group: Optional[str] = None
    subgroup: Optional[str] = None
    brand: Optional[str] = None
    
    # Financial data
    unit_price: Optional[float] = None
    unit_cost: Optional[float] = None
    annual_revenue: Optional[float] = None
    annual_profit: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    
    # Operational data
    uom: Optional[str] = None
    lead_time_days: Optional[int] = None
    safety_stock: Optional[float] = None
    
    # Classifications
    abc_classification: Optional[str] = None
    xyz_classification: Optional[str] = None
    overall_risk_rating: Optional[str] = None
    
    # Location data
    country: Optional[str] = None
    region: Optional[str] = None
    
    # Manufacturing data
    plant_id: Optional[str] = None
    storage_location_id: Optional[str] = None
    
    # Monthly data (for time series)
    monthly_demand: Dict[str, float] = field(default_factory=dict)
    monthly_supply: Dict[str, float] = field(default_factory=dict)
    monthly_inventory: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    created_at: Optional[str] = None
    data_source: Optional[str] = None

@dataclass
class SchemaValidationResult:
    """Result of schema validation"""
    is_valid: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    node_count: int = 0
    relationship_count: int = 0

class UnifiedDataModel:
    """
    Unified data model that ensures consistency across all ingestion scripts
    and provides dashboard compatibility.
    """
    
    def __init__(self, graph: Neo4jGraph):
        self.graph = graph
        self.required_fields = ['sku_code', 'name']
        self.financial_fields = ['unit_price', 'unit_cost', 'annual_revenue', 'annual_profit', 'gross_margin_pct']
        self.operational_fields = ['uom', 'lead_time_days', 'safety_stock']
    
    def create_product_node(self, product: ProductSchema) -> bool:
        """
        Create a standardized Product node with all relationships.
        This ensures dashboard compatibility.
        """
        try:
            # Create the main Product node
            product_props = {
                'sku_code': product.sku_code,
                'name': product.name,
                'unit_price': product.unit_price,
                'unit_cost': product.unit_cost,
                'annual_revenue': product.annual_revenue,
                'annual_profit': product.annual_profit,
                'gross_margin_pct': product.gross_margin_pct,
                'uom': product.uom,
                'lead_time_days': product.lead_time_days,
                'safety_stock': product.safety_stock,
                'abc_classification': product.abc_classification,
                'xyz_classification': product.xyz_classification,
                'overall_risk_rating': product.overall_risk_rating,
                'country': product.country,
                'region': product.region,
                'created_at': product.created_at or '2024-01-01',
                'data_source': product.data_source or 'unified_model'
            }
            
            # Remove None values
            product_props = {k: v for k, v in product_props.items() if v is not None}
            
            # Create Product node
            self.graph.query("""
                MERGE (p:Product {sku_code: $sku_code})
                SET p += $props
            """, {
                'sku_code': product.sku_code,
                'props': product_props
            })
            
            # Create relationships
            self._create_relationships(product)
            
            # Create monthly data if available
            if product.monthly_demand or product.monthly_supply or product.monthly_inventory:
                self._create_monthly_data(product)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating product node {product.sku_code}: {e}")
            return False
    
    def _create_relationships(self, product: ProductSchema):
        """Create all relationships for a product"""
        
        # Category relationship
        if product.category:
            self.graph.query("""
                MERGE (c:Category {name: $category})
                MERGE (p:Product {sku_code: $sku_code})
                MERGE (p)-[:BELONGS_TO]->(c)
            """, {
                'category': product.category,
                'sku_code': product.sku_code
            })
        
        # Group relationship
        if product.group:
            self.graph.query("""
                MERGE (g:Group {code: $group})
                MERGE (p:Product {sku_code: $sku_code})
                MERGE (p)-[:IN_GROUP]->(g)
            """, {
                'group': product.group,
                'sku_code': product.sku_code
            })
        
        # Subgroup relationship
        if product.subgroup:
            self.graph.query("""
                MERGE (sg:SubGroup {code: $subgroup})
                MERGE (p:Product {sku_code: $sku_code})
                MERGE (p)-[:IN_SUBGROUP]->(sg)
            """, {
                'subgroup': product.subgroup,
                'sku_code': product.sku_code
            })
        
        # Plant relationship
        if product.plant_id:
            self.graph.query("""
                MERGE (pl:Plant {id: $plant_id})
                MERGE (p:Product {sku_code: $sku_code})
                MERGE (p)-[:PRODUCED_AT]->(pl)
            """, {
                'plant_id': product.plant_id,
                'sku_code': product.sku_code
            })
        
        # Storage relationship
        if product.storage_location_id:
            self.graph.query("""
                MERGE (sl:StorageLocation {id: $storage_id})
                MERGE (p:Product {sku_code: $sku_code})
                MERGE (p)-[:STORED_AT]->(sl)
            """, {
                'storage_id': product.storage_location_id,
                'sku_code': product.sku_code
            })
        
        # Country relationship
        if product.country:
            self.graph.query("""
                MERGE (co:Country {name: $country})
                MERGE (p:Product {sku_code: $sku_code})
                MERGE (p)-[:OPERATES_IN]->(co)
            """, {
                'country': product.country,
                'sku_code': product.sku_code
            })
        
        # Brand relationship
        if product.brand:
            self.graph.query("""
                MERGE (b:Brand {name: $brand})
                MERGE (p:Product {sku_code: $sku_code})
                MERGE (p)-[:BRANDED_AS]->(b)
            """, {
                'brand': product.brand,
                'sku_code': product.sku_code
            })
    
    def _create_monthly_data(self, product: ProductSchema):
        """Create monthly demand, supply, and inventory data"""
        
        # Create DemandPlan node
        if product.monthly_demand:
            demand_data = json.dumps(product.monthly_demand)
            self.graph.query("""
                MERGE (dp:DemandPlan {sku_code: $sku_code, monthly_data: $demand_data})
                MERGE (p:Product {sku_code: $sku_code})
                MERGE (p)-[:HAS_DEMAND_PLAN]->(dp)
            """, {
                'sku_code': product.sku_code,
                'demand_data': demand_data
            })
        
        # Create SupplyPlan node
        if product.monthly_supply:
            supply_data = json.dumps(product.monthly_supply)
            self.graph.query("""
                MERGE (sp:SupplyPlan {sku_code: $sku_code, monthly_data: $supply_data})
                MERGE (p:Product {sku_code: $sku_code})
                MERGE (p)-[:HAS_SUPPLY_PLAN]->(sp)
            """, {
                'sku_code': product.sku_code,
                'supply_data': supply_data
            })
        
        # Create Inventory node
        if product.monthly_inventory:
            inventory_data = json.dumps(product.monthly_inventory)
            self.graph.query("""
                MERGE (inv:Inventory {sku_code: $sku_code, monthly_data: $inventory_data})
                MERGE (p:Product {sku_code: $sku_code})
                MERGE (p)-[:HAS_INVENTORY]->(inv)
            """, {
                'sku_code': product.sku_code,
                'inventory_data': inventory_data
            })
    
    def validate_schema(self) -> SchemaValidationResult:
        """
        Validate that the current database schema is compatible with the dashboard.
        """
        result = SchemaValidationResult()
        
        try:
            # Check if Product nodes exist
            product_count = self.graph.query("MATCH (p:Product) RETURN count(p) as count")[0]['count']
            result.node_count = product_count
            
            if product_count == 0:
                result.errors.append("No Product nodes found in database")
                result.is_valid = False
                return result
            
            # Check for required fields
            missing_fields = []
            for field in self.required_fields:
                count = self.graph.query(f"MATCH (p:Product) WHERE p.{field} IS NULL RETURN count(p) as count")[0]['count']
                if count > 0:
                    missing_fields.append(f"{field}: {count} products missing")
            
            if missing_fields:
                result.warnings.append(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Check for financial data
            financial_data_count = self.graph.query("""
                MATCH (p:Product) 
                WHERE p.unit_price IS NOT NULL OR p.unit_cost IS NOT NULL OR p.annual_revenue IS NOT NULL
                RETURN count(p) as count
            """)[0]['count']
            
            if financial_data_count == 0:
                result.warnings.append("No financial data found in Product nodes")
            else:
                result.node_count = financial_data_count
            
            # Check relationships
            relationship_count = self.graph.query("MATCH ()-[r]->() RETURN count(r) as count")[0]['count']
            result.relationship_count = relationship_count
            
            # Check dashboard compatibility
            dashboard_query = """
                MATCH (p:Product)
                OPTIONAL MATCH (p)-[:BELONGS_TO]->(cat:Category)
                RETURN p.sku_code as sku_id, 
                       p.name as name,
                       p.unit_price as unit_price,
                       p.unit_cost as unit_cost,
                       p.annual_revenue as annual_revenue,
                       p.annual_profit as annual_profit,
                       p.gross_margin_pct as gross_margin,
                       cat.name as category
                LIMIT 1
            """
            
            dashboard_result = self.graph.query(dashboard_query)
            if not dashboard_result:
                result.errors.append("Dashboard query failed - schema incompatible")
                result.is_valid = False
            else:
                result.is_valid = True
                
        except Exception as e:
            result.errors.append(f"Validation error: {e}")
            result.is_valid = False
        
        return result
    
    def migrate_sku_to_product(self) -> Dict[str, int]:
        """
        Migrate existing SKU nodes to Product nodes for backward compatibility.
        """
        migration_stats = {
            'skus_migrated': 0,
            'products_created': 0,
            'relationships_created': 0
        }
        
        try:
            # Get all SKU nodes
            sku_nodes = self.graph.query("""
                MATCH (sku:SKU)
                OPTIONAL MATCH (sku)-[:HAS_DEMAND_PLAN]->(dp:DemandPlan)
                OPTIONAL MATCH (sku)-[:HAS_SUPPLY_PLAN]->(sp:SupplyPlan)
                OPTIONAL MATCH (sku)-[:HAS_INVENTORY]->(inv:Inventory)
                OPTIONAL MATCH (sku)-[:BELONGS_TO_CATEGORY]->(cat:Category)
                RETURN sku, dp, sp, inv, cat
            """)
            
            for record in sku_nodes:
                sku = record['sku']
                
                # Create Product node from SKU
                product = ProductSchema(
                    sku_code=sku.get('sku_id', f"SKU_{sku.get('id', 'unknown')}"),
                    name=sku.get('name', 'Unknown Product'),
                    category=record['cat'].get('name') if record['cat'] else None,
                    data_source='sku_migration'
                )
                
                # Add monthly data if available
                if record['dp'] and record['dp'].get('monthly_data'):
                    try:
                        product.monthly_demand = json.loads(record['dp']['monthly_data'])
                    except:
                        pass
                
                if record['sp'] and record['sp'].get('monthly_data'):
                    try:
                        product.monthly_supply = json.loads(record['sp']['monthly_data'])
                    except:
                        pass
                
                if record['inv'] and record['inv'].get('monthly_data'):
                    try:
                        product.monthly_inventory = json.loads(record['inv']['monthly_data'])
                    except:
                        pass
                
                # Create the product node
                if self.create_product_node(product):
                    migration_stats['skus_migrated'] += 1
                    migration_stats['products_created'] += 1
            
            logger.info(f"Migration completed: {migration_stats}")
            return migration_stats
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return migration_stats
    
    def create_indexes(self):
        """Create indexes for optimal dashboard performance"""
        indexes = [
            "CREATE INDEX product_sku_code IF NOT EXISTS FOR (p:Product) ON (p.sku_code)",
            "CREATE INDEX product_category IF NOT EXISTS FOR (p:Product) ON (p.category)",
            "CREATE INDEX category_name IF NOT EXISTS FOR (c:Category) ON (c.name)",
            "CREATE INDEX demand_plan_sku IF NOT EXISTS FOR (dp:DemandPlan) ON (dp.sku_code)",
            "CREATE INDEX supply_plan_sku IF NOT EXISTS FOR (sp:SupplyPlan) ON (sp.sku_code)",
            "CREATE INDEX inventory_sku IF NOT EXISTS FOR (inv:Inventory) ON (inv.sku_code)"
        ]
        
        for index_query in indexes:
            try:
                self.graph.query(index_query)
            except Exception as e:
                logger.warning(f"Index creation failed: {e}")

def get_neo4j_config(key, default=""):
    """Get Neo4j config from environment variables or secrets file"""
    # First try environment variables
    env_value = os.getenv(key)
    if env_value:
        return env_value
    
    # Then try secrets file
    try:
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        k, v = line.split('=', 1)
                        if k.strip() == key:
                            return v.strip().strip('"')
    except:
        pass
    
    return default

def get_unified_model() -> Optional[UnifiedDataModel]:
    """Get a UnifiedDataModel instance with Neo4j connection"""
    try:
        # Use the same connection approach as dashboard_component.py
        graph = Neo4jGraph(
            url=get_neo4j_config("NEO4J_URI"),
            username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
            password=get_neo4j_config("NEO4J_PASSWORD"),
        )
        return UnifiedDataModel(graph)
    except Exception as e:
        logger.error(f"Failed to create UnifiedDataModel: {e}")
        return None

def validate_dashboard_compatibility() -> SchemaValidationResult:
    """Validate that the current database is compatible with the dashboard"""
    model = get_unified_model()
    if model:
        return model.validate_schema()
    else:
        return SchemaValidationResult(is_valid=False, errors=["Cannot connect to database"])

if __name__ == "__main__":
    """
    Test the unified data model and validate current database schema.
    
    This script will:
    1. Connect to the Neo4j database
    2. Validate the current schema
    3. Display detailed results
    
    EXPECTED OUTPUT:
        Schema validation: ✅ Valid
        Products: 2000
        Relationships: 8034
        
    If you see errors, check:
    1. .streamlit/secrets.toml file exists and has correct credentials
    2. Neo4j database is accessible
    3. Database contains Product nodes
    """
    print("🔍 Testing Unified Data Model...")
    print("=" * 50)
    
    # Test the unified model
    model = get_unified_model()
    if model:
        result = model.validate_schema()
        print(f"Schema validation: {'✅ Valid' if result.is_valid else '❌ Invalid'}")
        print(f"Products: {result.node_count}")
        print(f"Relationships: {result.relationship_count}")
        
        if result.errors:
            print(f"\n❌ Errors found:")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        if result.is_valid and result.node_count > 0:
            print(f"\n✅ Database is ready for dashboard use!")
        else:
            print(f"\n❌ Database needs attention before dashboard can work properly.")
            
    else:
        print("❌ Cannot connect to database")
        print("\nTROUBLESHOOTING:")
        print("1. Check that .streamlit/secrets.toml exists with correct credentials")
        print("2. Verify Neo4j database is running and accessible")
        print("3. Ensure NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD are set")
        print("4. Check network connectivity to the database")
