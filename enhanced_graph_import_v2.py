#!/usr/bin/env python3
"""
Enhanced Graph Import Script V2
Handles multiple Excel file formats and provides comprehensive debugging
"""

import pandas as pd
import os
from langchain_neo4j import Neo4jGraph
from typing import Dict, List, Any
import logging

# Load environment variables from .streamlit/secrets.toml
def load_secrets():
    """Load secrets from .streamlit/secrets.toml"""
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        with open(secrets_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Loaded secrets from .streamlit/secrets.toml")

# Load secrets at module level
load_secrets()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedGraphImporterV2:
    """Enhanced graph importer that handles multiple Excel formats"""
    
    def __init__(self):
        self.graph = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Neo4j connection"""
        try:
            self.graph = Neo4jGraph(
                url=os.getenv("NEO4J_URI"),
                username=os.getenv("NEO4J_USERNAME", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD"),
            )
            logger.info("✅ Neo4j connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            self.graph = None
    
    def clear_existing_data(self):
        """Clear existing graph data"""
        if not self.graph:
            return False
        
        try:
            logger.info("🧹 Clearing existing graph data...")
            # Clear all nodes and relationships (but keep metadata)
            self.graph.query("MATCH (n) WHERE NOT n:Metadata DETACH DELETE n")
            logger.info("✅ Cleared existing graph data (preserved metadata)")
            return True
        except Exception as e:
            logger.error(f"❌ Error clearing data: {e}")
            return False
    
    def analyze_excel_structure(self, excel_file_path: str) -> Dict[str, Any]:
        """Analyze Excel file structure to determine import strategy"""
        
        logger.info(f"🔍 Analyzing Excel file structure: {excel_file_path}")
        
        try:
            xl = pd.ExcelFile(excel_file_path)
            sheets = xl.sheet_names
            logger.info(f"📊 Found {len(sheets)} sheets: {sheets}")
            
            analysis = {
                'file_path': excel_file_path,
                'sheets': sheets,
                'import_strategy': 'unknown',
                'sheet_analysis': {}
            }
            
            # Check for Raw format (original expected format)
            raw_sheets = [s for s in sheets if 'Raw' in s]
            if raw_sheets:
                logger.info(f"🎯 Detected Raw format with sheets: {raw_sheets}")
                analysis['import_strategy'] = 'raw_format'
                for sheet in raw_sheets:
                    try:
                        df = pd.read_excel(excel_file_path, sheet_name=sheet)
                        analysis['sheet_analysis'][sheet] = {
                            'rows': len(df),
                            'columns': list(df.columns),
                            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
                        }
                    except Exception as e:
                        logger.error(f"❌ Error analyzing sheet {sheet}: {e}")
            
            # Check for FMCG format (single sheet with SKU data)
            elif len(sheets) == 1 and 'Sheet1' in sheets:
                logger.info("🎯 Detected FMCG format (single sheet)")
                analysis['import_strategy'] = 'fmcg_format'
                try:
                    df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
                    analysis['sheet_analysis']['Sheet1'] = {
                        'rows': len(df),
                        'columns': list(df.columns),
                        'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
                    }
                    logger.info(f"📋 Sheet1 contains {len(df)} rows with columns: {list(df.columns)}")
                except Exception as e:
                    logger.error(f"❌ Error analyzing Sheet1: {e}")
            
            # Check for Enhanced format (multiple business sheets)
            else:
                logger.info("🎯 Detected Enhanced format (multiple business sheets)")
                analysis['import_strategy'] = 'enhanced_format'
                for sheet in sheets:
                    try:
                        df = pd.read_excel(excel_file_path, sheet_name=sheet)
                        analysis['sheet_analysis'][sheet] = {
                            'rows': len(df),
                            'columns': list(df.columns),
                            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
                        }
                    except Exception as e:
                        logger.error(f"❌ Error analyzing sheet {sheet}: {e}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing Excel structure: {e}")
            return {'error': str(e)}
    
    def import_graph(self, excel_file_path: str, original_filename: str = None) -> Dict[str, Any]:
        """Import graph based on detected format"""
        
        if not self.graph:
            return {"error": "Neo4j connection not available"}
        
        if not os.path.exists(excel_file_path):
            return {"error": f"Excel file not found: {excel_file_path}"}
        
        try:
            logger.info(f"📁 Starting enhanced graph import from: {excel_file_path}")
            
            # Clear existing data
            if not self.clear_existing_data():
                return {"error": "Failed to clear existing data"}
            
            # Analyze file structure
            analysis = self.analyze_excel_structure(excel_file_path)
            if 'error' in analysis:
                return {"error": analysis['error']}
            
            logger.info(f"🎯 Using import strategy: {analysis['import_strategy']}")
            
            # Import based on detected format
            if analysis['import_strategy'] == 'raw_format':
                result = self._import_raw_format(excel_file_path, analysis)
            elif analysis['import_strategy'] == 'fmcg_format':
                result = self._import_fmcg_format(excel_file_path, analysis)
            elif analysis['import_strategy'] == 'enhanced_format':
                result = self._import_enhanced_format(excel_file_path, analysis)
            else:
                return {"error": f"Unknown import strategy: {analysis['import_strategy']}"}
            
            # Store import metadata
            self._store_import_metadata(excel_file_path, original_filename, analysis, result)
            
            # Validate connectivity
            connectivity_stats = self._validate_connectivity()
            result['connectivity'] = connectivity_stats
            
            logger.info(f"✅ Import completed successfully!")
            logger.info(f"📊 Final stats: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error during import: {e}")
            return {"error": str(e)}
    
    def _import_raw_format(self, excel_file_path: str, analysis: Dict) -> Dict[str, Any]:
        """Import Raw format (original expected format)"""
        logger.info("🏗️ Importing Raw format...")
        
        stats = {"products": 0, "groups": 0, "subgroups": 0, "plants": 0, "storage": 0}
        
        try:
            # Import Product nodes from Raw - Nodes
            if 'Raw - Nodes' in analysis['sheets']:
                nodes_df = pd.read_excel(excel_file_path, sheet_name='Raw - Nodes')
                logger.info(f"📦 Creating {len(nodes_df)} product nodes...")
                
                for _, row in nodes_df.iterrows():
                    node_id = row['Node']
                    self.graph.query("""
                        CREATE (p:Product {
                            id: $node_id,
                            code: $node_id,
                            name: $node_id,
                            type: 'Product'
                        })
                    """, {"node_id": node_id})
                    stats["products"] += 1
                
                logger.info(f"✅ Created {stats['products']} product nodes")
            
            # Import relationships from Raw sheets
            relationship_stats = self._import_raw_relationships(excel_file_path, analysis)
            stats.update(relationship_stats)
            
            return {
                "success": True,
                "format": "raw_format",
                "nodes_created": stats,
                "relationships_created": relationship_stats,
                "message": "Raw format import completed"
            }
            
        except Exception as e:
            logger.error(f"❌ Error importing Raw format: {e}")
            return {"error": str(e)}
    
    def _import_fmcg_format(self, excel_file_path: str, analysis: Dict) -> Dict[str, Any]:
        """Import FMCG format (single sheet with SKU data)"""
        logger.info("🏗️ Importing FMCG format...")
        
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
            logger.info(f"📦 Processing {len(df)} SKU records...")
            
            stats = {"products": 0, "categories": 0, "countries": 0, "plants": 0, "relationships": 0}
            
            # Create unique categories
            categories = df['Category'].unique()
            logger.info(f"🏷️ Creating {len(categories)} category nodes...")
            for category in categories:
                self.graph.query("""
                    CREATE (c:Category {
                        id: $category_id,
                        name: $category_id,
                        type: 'Category'
                    })
                """, {"category_id": category})
                stats["categories"] += 1
            
            # Create unique countries
            countries = df['Country'].unique()
            logger.info(f"🌍 Creating {len(countries)} country nodes...")
            for country in countries:
                self.graph.query("""
                    CREATE (c:Country {
                        id: $country_id,
                        name: $country_id,
                        type: 'Country'
                    })
                """, {"country_id": country})
                stats["countries"] += 1
            
            # Create unique plants
            plants = df['Manufacturing Plant'].unique()
            logger.info(f"🏭 Creating {len(plants)} plant nodes...")
            for plant in plants:
                self.graph.query("""
                    CREATE (p:Plant {
                        id: $plant_id,
                        name: $plant_id,
                        type: 'Plant'
                    })
                """, {"plant_id": plant})
                stats["plants"] += 1
            
            # Create product nodes and relationships
            logger.info("🔗 Creating product nodes and relationships...")
            for _, row in df.iterrows():
                sku_code = row['SKU Code']
                
                # Create product node
                self.graph.query("""
                    CREATE (p:Product {
                        id: $sku_code,
                        code: $sku_code,
                        name: $sku_code,
                        category: $category,
                        country: $country,
                        region: $region,
                        uom: $uom,
                        unit_price: $unit_price,
                        unit_cost: $unit_cost,
                        lead_time: $lead_time,
                        manufacturing_plant: $plant,
                        manufacturing_capacity: $capacity,
                        type: 'Product'
                    })
                """, {
                    "sku_code": sku_code,
                    "category": row['Category'],
                    "country": row['Country'],
                    "region": row.get('Region', ''),
                    "uom": row['UOM'],
                    "unit_price": float(row['Unit Price ($)']),
                    "unit_cost": float(row['Unit Cost ($)']),
                    "lead_time": int(row['Lead Time (days)']),
                    "plant": row['Manufacturing Plant'],
                    "capacity": float(row.get('Manufacturing Capacity', 0))
                })
                stats["products"] += 1
                
                # Create relationships
                # Product -> Category
                self.graph.query("""
                    MATCH (p:Product {id: $sku_code})
                    MATCH (c:Category {id: $category})
                    CREATE (p)-[:BELONGS_TO]->(c)
                """, {"sku_code": sku_code, "category": row['Category']})
                stats["relationships"] += 1
                
                # Product -> Country
                self.graph.query("""
                    MATCH (p:Product {id: $sku_code})
                    MATCH (c:Country {id: $country})
                    CREATE (p)-[:OPERATES_IN]->(c)
                """, {"sku_code": sku_code, "country": row['Country']})
                stats["relationships"] += 1
                
                # Product -> Plant
                self.graph.query("""
                    MATCH (p:Product {id: $sku_code})
                    MATCH (plant:Plant {id: $plant})
                    CREATE (p)-[:MANUFACTURED_AT]->(plant)
                """, {"sku_code": sku_code, "plant": row['Manufacturing Plant']})
                stats["relationships"] += 1
            
            logger.info(f"✅ FMCG import completed: {stats}")
            
            return {
                "success": True,
                "format": "fmcg_format",
                "nodes_created": {
                    "products": stats["products"],
                    "categories": stats["categories"],
                    "countries": stats["countries"],
                    "plants": stats["plants"]
                },
                "relationships_created": {
                    "total_relationships": stats["relationships"]
                },
                "message": "FMCG format import completed"
            }
            
        except Exception as e:
            logger.error(f"❌ Error importing FMCG format: {e}")
            return {"error": str(e)}
    
    def _import_enhanced_format(self, excel_file_path: str, analysis: Dict) -> Dict[str, Any]:
        """Import Enhanced format (multiple business sheets)"""
        logger.info("🏗️ Importing Enhanced format...")
        
        # This would handle the Enhanced_SOP_Dataset.xlsx format
        # For now, fall back to FMCG format for the first sheet
        return self._import_fmcg_format(excel_file_path, analysis)
    
    def _import_raw_relationships(self, excel_file_path: str, analysis: Dict) -> Dict[str, int]:
        """Import relationships from Raw format sheets"""
        stats = {"group_edges": 0, "subgroup_edges": 0, "plant_edges": 0, "storage_edges": 0}
        
        try:
            # Import Group relationships
            if 'Raw - Edges Group' in analysis['sheets']:
                group_edges_df = pd.read_excel(excel_file_path, sheet_name='Raw - Edges Group')
                logger.info(f"🔗 Creating {len(group_edges_df)} group relationships...")
                
                for _, row in group_edges_df.iterrows():
                    self.graph.query("""
                        MATCH (a:Product {code: $node1})
                        MATCH (b:Product {code: $node2})
                        CREATE (a)-[:SAME_GROUP {groupCode: $groupCode}]->(b)
                    """, {
                        "node1": row['node1'],
                        "node2": row['node2'],
                        "groupCode": row['GroupCode']
                    })
                    stats["group_edges"] += 1
            
            # Add other relationship types as needed...
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error importing relationships: {e}")
            return stats
    
    def _store_import_metadata(self, excel_file_path: str, original_filename: str, analysis: Dict, result: Dict):
        """Store import metadata in the database"""
        try:
            import datetime
            import hashlib
            
            # Calculate file hash for integrity
            with open(excel_file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # Get file stats
            file_stats = os.stat(excel_file_path)
            
            # Create metadata node
            metadata = {
                "filename": original_filename or os.path.basename(excel_file_path),
                "file_path": excel_file_path,
                "file_size_bytes": file_stats.st_size,
                "file_hash": file_hash,
                "import_timestamp": datetime.datetime.now().isoformat(),
                "import_strategy": analysis.get('import_strategy', 'unknown'),
                "sheets_found": analysis.get('sheets', []),
                "total_sheets": len(analysis.get('sheets', [])),
                "nodes_created": result.get('nodes_created', {}),
                "relationships_created": result.get('relationships_created', {}),
                "format_detected": result.get('format', 'unknown'),
                "import_success": result.get('success', False),
                "error_message": result.get('error', None)
            }
            
            # Store in database
            self.graph.query("""
                MERGE (m:Metadata {id: 'current_import'})
                SET m = $metadata
                SET m.last_updated = datetime()
            """, {"metadata": metadata})
            
            logger.info(f"📋 Stored import metadata for: {metadata['filename']}")
            
        except Exception as e:
            logger.error(f"❌ Error storing metadata: {e}")
    
    def _validate_connectivity(self) -> Dict[str, Any]:
        """Validate graph connectivity with detailed logging"""
        
        try:
            logger.info("🔍 Validating graph connectivity...")
            
            # Count total nodes
            total_nodes = self.graph.query("MATCH (n) RETURN count(n) as count")[0]['count']
            logger.info(f"📊 Total nodes: {total_nodes}")
            
            # Count isolated nodes
            isolated_nodes = self.graph.query("""
                MATCH (n)
                WHERE NOT (n)--()
                RETURN count(n) as count
            """)[0]['count']
            logger.info(f"🚫 Isolated nodes: {isolated_nodes}")
            
            # Count connected nodes
            connected_nodes = total_nodes - isolated_nodes
            logger.info(f"🔗 Connected nodes: {connected_nodes}")
            
            # Count total relationships
            total_relationships = self.graph.query("MATCH ()-[r]->() RETURN count(r) as count")[0]['count']
            logger.info(f"🔗 Total relationships: {total_relationships}")
            
            # Get node type distribution
            node_types = self.graph.query("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """)
            logger.info("📋 Node type distribution:")
            for record in node_types:
                logger.info(f"  {record['type']}: {record['count']}")
            
            # Get relationship type distribution
            relationship_types = self.graph.query("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            logger.info("🔗 Relationship type distribution:")
            for record in relationship_types:
                logger.info(f"  {record['type']}: {record['count']}")
            
            connectivity_stats = {
                "total_nodes": total_nodes,
                "connected_nodes": connected_nodes,
                "isolated_nodes": isolated_nodes,
                "total_relationships": total_relationships,
                "connectivity_percentage": (connected_nodes / total_nodes * 100) if total_nodes > 0 else 0,
                "node_types": {record['type']: record['count'] for record in node_types},
                "relationship_types": {record['type']: record['count'] for record in relationship_types}
            }
            
            logger.info(f"✅ Connectivity validation complete: {connectivity_stats['connectivity_percentage']:.1f}% connected")
            return connectivity_stats
            
        except Exception as e:
            logger.error(f"❌ Error validating connectivity: {e}")
            return {"error": str(e)}

def import_enhanced_fmcg_graph_v2(excel_file_path: str, original_filename: str = None) -> Dict[str, Any]:
    """Main function to import enhanced FMCG graph with comprehensive debugging"""
    
    importer = EnhancedGraphImporterV2()
    return importer.import_graph(excel_file_path, original_filename)

if __name__ == "__main__":
    # Test with the AI Enhanced Excel file
    result = import_enhanced_fmcg_graph_v2("AI_Enhanced_SOP_Dataset.xlsx")
    print(f"Import result: {result}")
