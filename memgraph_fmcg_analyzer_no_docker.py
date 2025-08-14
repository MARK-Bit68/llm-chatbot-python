#!/usr/bin/env python3
"""
Enhanced FMCG SOP Dataset - Graph Database Analyzer (No Docker Required)

This standalone application loads the Enhanced FMCG SOP dataset into a graph database
and provides visualization capabilities without requiring Docker.

Options:
1. Neo4j Desktop (local installation)
2. Neo4j AuraDB (cloud service - free tier available)
3. In-memory graph analysis with NetworkX
"""

import os
import sys
import pandas as pd
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import webbrowser
from datetime import datetime
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class FMCGGraphAnalyzerNoDocker:
    """Loads Enhanced FMCG SOP dataset into graph database without Docker"""
    
    def __init__(self, excel_file: str = "Enhanced_FMCG_SOP_Dataset.xlsx"):
        self.excel_file = excel_file
        self.data_cache = {}
        self.graph_data = {}
        
    def load_excel_data(self):
        """Load data from Excel file into memory"""
        print(f"📊 Loading data from {self.excel_file}...")
        
        try:
            excel_file = pd.ExcelFile(self.excel_file)
            print(f"   Found {len(excel_file.sheet_names)} sheets")
            
            for sheet_name in excel_file.sheet_names:
                print(f"   Loading sheet: {sheet_name}")
                self.data_cache[sheet_name] = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            
            print("✅ Excel data loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load Excel file: {e}")
            return False
    
    def analyze_data_with_networkx(self):
        """Analyze data using NetworkX for graph analysis"""
        print("🕸️  Analyzing data with NetworkX...")
        
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            from collections import defaultdict
            
            # Create graph
            G = nx.DiGraph()
            
            # Add nodes from master data
            if "Master Data" in self.data_cache:
                df = self.data_cache["Master Data"]
                for _, row in df.iterrows():
                    G.add_node(row['SKU Code'], 
                              type='Product',
                              category=row['Category'],
                              country=row['Country'],
                              unit_price=float(row['Unit Price ($)']),
                              lead_time=int(row['Lead Time (days)']))
            
            # Add category and country nodes
            if "Master Data" in self.data_cache:
                df = self.data_cache["Master Data"]
                categories = df['Category'].unique()
                countries = df['Country'].unique()
                
                for category in categories:
                    G.add_node(category, type='Category')
                
                for country in countries:
                    G.add_node(country, type='Country')
                
                # Add relationships
                for _, row in df.iterrows():
                    G.add_edge(row['SKU Code'], row['Category'], type='BELONGS_TO')
                    G.add_edge(row['SKU Code'], row['Country'], type='OPERATES_IN')
            
            # Add financial data
            if "Financial Plan" in self.data_cache:
                df = self.data_cache["Financial Plan"]
                for _, row in df.iterrows():
                    if row['SKU Code'] in G.nodes():
                        G.nodes[row['SKU Code']].update({
                            'total_revenue': float(row['Total Revenue ($)']),
                            'gross_margin': float(row['Gross Margin (%)']),
                            'total_volume': int(row['Total Volume'])
                        })
            
            # Add logistics data
            if "Logistics Plan" in self.data_cache:
                df = self.data_cache["Logistics Plan"]
                for _, row in df.iterrows():
                    if row['SKU Code'] in G.nodes():
                        G.nodes[row['SKU Code']].update({
                            'reorder_point': int(row['Reorder Point']),
                            'max_inventory': int(row['Max Inventory']),
                            'min_order_quantity': int(row['Min Order Quantity'])
                        })
            
            # Graph analysis
            print(f"✅ Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            
            # Basic statistics
            print("\n📊 Graph Statistics:")
            print(f"   - Total nodes: {G.number_of_nodes()}")
            print(f"   - Total edges: {G.number_of_edges()}")
            print(f"   - Product nodes: {len([n for n, d in G.nodes(data=True) if d.get('type') == 'Product'])}")
            print(f"   - Category nodes: {len([n for n, d in G.nodes(data=True) if d.get('type') == 'Category'])}")
            print(f"   - Country nodes: {len([n for n, d in G.nodes(data=True) if d.get('type') == 'Country'])}")
            
            # Store graph for later use
            self.graph_data['networkx_graph'] = G
            
            return True
            
        except ImportError:
            print("❌ NetworkX not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "networkx", "matplotlib"])
            return self.analyze_data_with_networkx()
        except Exception as e:
            print(f"❌ NetworkX analysis failed: {e}")
            return False
    
    def run_sample_queries(self):
        """Run sample queries on the graph data"""
        print("\n🔍 Sample Queries and Results:")
        
        if 'networkx_graph' not in self.graph_data:
            print("❌ No graph data available")
            return
        
        G = self.graph_data['networkx_graph']
        
        # Sample queries
        queries = [
            {
                "name": "Top 5 Products by Revenue",
                "query": lambda: sorted(
                    [(n, d.get('total_revenue', 0)) for n, d in G.nodes(data=True) 
                     if d.get('type') == 'Product' and d.get('total_revenue')],
                    key=lambda x: x[1], reverse=True
                )[:5]
            },
            {
                "name": "Products by Category Count",
                "query": lambda: [(n, len(list(G.predecessors(n)))) for n, d in G.nodes(data=True) 
                                if d.get('type') == 'Category']
            },
            {
                "name": "Products with Longest Lead Times",
                "query": lambda: sorted(
                    [(n, d.get('lead_time', 0)) for n, d in G.nodes(data=True) 
                     if d.get('type') == 'Product' and d.get('lead_time')],
                    key=lambda x: x[1], reverse=True
                )[:10]
            },
            {
                "name": "High Margin Products (>50%)",
                "query": lambda: [(n, d.get('gross_margin', 0)) for n, d in G.nodes(data=True) 
                                if d.get('type') == 'Product' and d.get('gross_margin', 0) > 50]
            }
        ]
        
        for query_info in queries:
            print(f"\n📋 {query_info['name']}:")
            try:
                result = query_info['query']()
                if result:
                    # Print results in table format
                    if len(result) > 0 and len(result[0]) == 2:
                        print("   Product | Value")
                        print("   " + "-" * 20)
                        for item, value in result[:5]:  # Limit to 5 rows
                            print(f"   {item} | {value}")
                        if len(result) > 5:
                            print(f"   ... and {len(result) - 5} more")
                else:
                    print("   No results found")
            except Exception as e:
                print(f"   Error: {e}")
    
    def create_visualization(self):
        """Create a simple visualization of the graph"""
        print("\n📈 Creating visualization...")
        
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            
            G = self.graph_data['networkx_graph']
            
            # Create a simple visualization
            plt.figure(figsize=(12, 8))
            
            # Position nodes
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Draw nodes by type
            product_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'Product']
            category_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'Category']
            country_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'Country']
            
            # Draw nodes
            nx.draw_networkx_nodes(G, pos, nodelist=product_nodes, node_color='lightblue', 
                                 node_size=100, alpha=0.7, label='Products')
            nx.draw_networkx_nodes(G, pos, nodelist=category_nodes, node_color='lightgreen', 
                                 node_size=200, alpha=0.8, label='Categories')
            nx.draw_networkx_nodes(G, pos, nodelist=country_nodes, node_color='lightcoral', 
                                 node_size=200, alpha=0.8, label='Countries')
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, alpha=0.5, arrows=True, arrowsize=10)
            
            # Add labels for categories and countries
            labels = {n: n for n in category_nodes + country_nodes}
            nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
            
            plt.title("Enhanced FMCG SOP Dataset - Graph Structure")
            plt.legend()
            plt.axis('off')
            
            # Save the plot
            plot_file = "fmcg_graph_visualization.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Visualization saved as {plot_file}")
            
            # Open the image
            try:
                subprocess.run(['open', plot_file], check=True)
                print("✅ Opened visualization in default image viewer")
            except:
                print(f"💡 Visualization saved as {plot_file} - open it manually to view")
            
            return True
            
        except Exception as e:
            print(f"❌ Visualization failed: {e}")
            return False
    
    def export_graph_data(self):
        """Export graph data for external visualization tools"""
        print("\n📤 Exporting graph data...")
        
        try:
            G = self.graph_data['networkx_graph']
            
            # Export as JSON for web visualization
            graph_data = {
                'nodes': [],
                'edges': []
            }
            
            # Add nodes
            for node, data in G.nodes(data=True):
                graph_data['nodes'].append({
                    'id': node,
                    'type': data.get('type', 'Unknown'),
                    'category': data.get('category', ''),
                    'country': data.get('country', ''),
                    'unit_price': data.get('unit_price', 0),
                    'lead_time': data.get('lead_time', 0),
                    'total_revenue': data.get('total_revenue', 0),
                    'gross_margin': data.get('gross_margin', 0)
                })
            
            # Add edges
            for source, target, data in G.edges(data=True):
                graph_data['edges'].append({
                    'source': source,
                    'target': target,
                    'type': data.get('type', 'RELATED_TO')
                })
            
            # Save to JSON file
            json_file = "fmcg_graph_data.json"
            with open(json_file, 'w') as f:
                json.dump(graph_data, f, indent=2)
            
            print(f"✅ Graph data exported to {json_file}")
            print(f"   - {len(graph_data['nodes'])} nodes")
            print(f"   - {len(graph_data['edges'])} edges")
            
            return True
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False
    
    def create_web_visualization(self):
        """Create a simple web-based visualization"""
        print("\n🌐 Creating web visualization...")
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced FMCG SOP Dataset - Graph Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .controls { margin-bottom: 20px; }
        .info { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        #graph { border: 1px solid #ddd; border-radius: 5px; }
        .node { cursor: pointer; }
        .node:hover { stroke: #333; stroke-width: 2px; }
        .link { stroke: #999; stroke-opacity: 0.6; }
        .tooltip { position: absolute; background: white; border: 1px solid #ddd; padding: 5px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Enhanced FMCG SOP Dataset - Graph Visualization</h1>
        
        <div class="info">
            <h3>Dataset Overview</h3>
            <p>This visualization shows the relationships between products, categories, and countries in the Enhanced FMCG SOP dataset.</p>
            <ul>
                <li><strong>Blue nodes:</strong> Products (SKUs)</li>
                <li><strong>Green nodes:</strong> Categories (Legumes, Dried Fruits, Nuts, Grains, Spices)</li>
                <li><strong>Red nodes:</strong> Countries (Country A, B, C)</li>
                <li><strong>Edges:</strong> Relationships between entities</li>
            </ul>
        </div>
        
        <div class="controls">
            <button onclick="resetZoom()">Reset Zoom</button>
            <button onclick="toggleLabels()">Toggle Labels</button>
            <span id="stats"></span>
        </div>
        
        <div id="graph"></div>
    </div>

    <script>
        // Load graph data
        fetch('fmcg_graph_data.json')
            .then(response => response.json())
            .then(data => {
                createVisualization(data);
            })
            .catch(error => {
                console.error('Error loading graph data:', error);
                document.getElementById('graph').innerHTML = '<p>Error loading graph data. Please ensure fmcg_graph_data.json is available.</p>';
            });

        function createVisualization(data) {
            const width = 1000;
            const height = 600;
            
            const svg = d3.select('#graph')
                .append('svg')
                .attr('width', width)
                .attr('height', height);
            
            const g = svg.append('g');
            
            // Create force simulation
            const simulation = d3.forceSimulation(data.nodes)
                .force('link', d3.forceLink(data.edges).id(d => d.id).distance(100))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2));
            
            // Create links
            const link = g.append('g')
                .selectAll('line')
                .data(data.edges)
                .enter().append('line')
                .attr('class', 'link');
            
            // Create nodes
            const node = g.append('g')
                .selectAll('circle')
                .data(data.nodes)
                .enter().append('circle')
                .attr('class', 'node')
                .attr('r', d => d.type === 'Product' ? 4 : 8)
                .attr('fill', d => {
                    if (d.type === 'Product') return '#4e79a7';
                    if (d.type === 'Category') return '#59a14f';
                    if (d.type === 'Country') return '#e15759';
                    return '#b07aa1';
                })
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));
            
            // Add tooltips
            const tooltip = d3.select('body').append('div')
                .attr('class', 'tooltip')
                .style('opacity', 0);
            
            node.on('mouseover', function(event, d) {
                tooltip.transition()
                    .duration(200)
                    .style('opacity', .9);
                tooltip.html(`
                    <strong>${d.id}</strong><br/>
                    Type: ${d.type}<br/>
                    ${d.category ? 'Category: ' + d.category + '<br/>' : ''}
                    ${d.country ? 'Country: ' + d.country + '<br/>' : ''}
                    ${d.total_revenue ? 'Revenue: $' + d.total_revenue.toLocaleString() + '<br/>' : ''}
                    ${d.gross_margin ? 'Margin: ' + d.gross_margin.toFixed(1) + '%<br/>' : ''}
                    ${d.lead_time ? 'Lead Time: ' + d.lead_time + ' days' : ''}
                `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseout', function(d) {
                tooltip.transition()
                    .duration(500)
                    .style('opacity', 0);
            });
            
            // Update positions on simulation tick
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
            });
            
            // Drag functions
            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }
            
            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }
            
            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
            
            // Update stats
            document.getElementById('stats').innerHTML = 
                `Nodes: ${data.nodes.length} | Edges: ${data.edges.length}`;
        }
        
        function resetZoom() {
            // Reset zoom functionality
            location.reload();
        }
        
        function toggleLabels() {
            // Toggle labels functionality
            console.log('Toggle labels clicked');
        }
    </script>
</body>
</html>
        """
        
        # Save HTML file
        html_file = "fmcg_graph_visualization.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"✅ Web visualization created: {html_file}")
        
        # Open in Chrome
        try:
            subprocess.run(['open', '-a', 'Google Chrome', html_file], check=True)
            print("✅ Opened web visualization in Chrome")
        except:
            print(f"💡 Web visualization saved as {html_file} - open it manually in Chrome")
        
        return True
    
    def run_complete_analysis(self):
        """Run complete analysis pipeline"""
        print("🚀 Enhanced FMCG SOP Dataset - Graph Analysis (No Docker)")
        print("=" * 70)
        
        # Check if Excel file exists
        if not os.path.exists(self.excel_file):
            print(f"❌ Excel file '{self.excel_file}' not found in current directory")
            print("   Please ensure the Enhanced FMCG SOP Dataset Excel file is in the same directory as this script")
            return False
        
        # Load data
        if not self.load_excel_data():
            return False
        
        # Analyze with NetworkX
        if not self.analyze_data_with_networkx():
            return False
        
        # Run sample queries
        self.run_sample_queries()
        
        # Create visualizations
        self.create_visualization()
        self.export_graph_data()
        self.create_web_visualization()
        
        print("\n🎉 Analysis complete!")
        print("\n📁 Generated Files:")
        print("   - fmcg_graph_visualization.png (static image)")
        print("   - fmcg_graph_data.json (graph data)")
        print("   - fmcg_graph_visualization.html (interactive web visualization)")
        
        print("\n🌐 Next Steps:")
        print("   1. Interactive web visualization should be open in Chrome")
        print("   2. Explore the graph structure interactively")
        print("   3. Hover over nodes to see detailed information")
        print("   4. Drag nodes to rearrange the layout")
        
        return True

def main():
    """Main function"""
    analyzer = FMCGGraphAnalyzerNoDocker()
    analyzer.run_complete_analysis()

if __name__ == "__main__":
    main()
