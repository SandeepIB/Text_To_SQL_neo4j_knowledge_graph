"""
Quick test to verify knowledge graph visualization works
"""

import pandas as pd
import networkx as nx
from app import TableKnowledgeGraph, load_excel_data
import plotly.graph_objects as go

# Load data
print("Loading data from Excel...")
schemas, relationships = load_excel_data("AI_SampleDataStruture.xlsx")

if schemas and relationships:
    print(f"✓ Loaded {len(schemas)} tables")
    print(f"✓ Loaded {len(relationships)} relationships")

    # Create knowledge graph
    print("\nBuilding knowledge graph...")
    kg = TableKnowledgeGraph(schemas, relationships)

    # Get stats
    stats = kg.get_graph_stats()
    print(f"\n📊 Graph Statistics:")
    print(f"  - Total Tables: {stats['total_tables']}")
    print(f"  - Total Relationships: {stats['total_relationships']}")
    print(f"  - Average Connections: {stats['average_connections']:.2f}")
    print(f"  - Is Connected: {stats['is_connected']}")
    print(f"  - Tables: {', '.join(stats['tables'])}")

    # Create visualization
    print("\n🎨 Creating visualization...")
    fig = kg.visualize_graph_plotly()

    # Save to HTML
    output_file = "knowledge_graph_visualization.html"
    fig.write_html(output_file)
    print(f"✓ Visualization saved to: {output_file}")
    print(f"  Open this file in your browser to view the interactive graph!")

    # Export graph data
    print("\n📦 Exporting graph data...")
    graph_data = kg.export_graph_data()

    import json
    with open("knowledge_graph_data.json", "w", encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)
    print("✓ Graph data exported to: knowledge_graph_data.json")

    # Save as GraphML
    nx.write_graphml(kg.graph, "knowledge_graph.graphml")
    print("✓ Graph exported to: knowledge_graph.graphml")

    print("\n✅ All tests passed!")

else:
    print("❌ Failed to load data")
