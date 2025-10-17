"""
Knowledge Graph Visualization Script
Visualizes the knowledge graph from JSON file
"""
import json
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from pathlib import Path

# Load the knowledge graph data
with open('knowledge_graph_data.json', 'r') as f:
    kg_data = json.load(f)

print("="*60)
print("KNOWLEDGE GRAPH VISUALIZATION")
print("="*60)

# Build NetworkX graph
G = nx.MultiDiGraph()

# Add nodes
for node in kg_data['nodes']:
    G.add_node(
        node['table_name'],
        columns=node['columns'],
        column_count=node['column_count']
    )
    print(f"\nTable: {node['table_name']}")
    print(f"  Columns: {node['column_count']}")
    print(f"  Sample: {', '.join(node['columns'][:5])}...")

# Add edges
print("\n" + "="*60)
print("RELATIONSHIPS")
print("="*60)

for edge in kg_data['edges']:
    G.add_edge(
        edge['from'],
        edge['to'],
        source_columns=edge['source_columns'],
        target_columns=edge['target_columns'],
        join_type=edge['join_type'],
        context=edge['context'],
        description=edge['description']
    )

    join_condition = " AND ".join([
        f"{edge['from']}.{src} = {edge['to']}.{tgt}"
        for src, tgt in zip(edge['source_columns'], edge['target_columns'])
    ])

    print(f"\n{edge['from']} -> {edge['to']}")
    print(f"  Context: {edge['context']}")
    print(f"  Join Type: {edge['join_type']}")
    print(f"  Condition: {join_condition}")

# Create Plotly interactive visualization
print("\n" + "="*60)
print("GENERATING INTERACTIVE VISUALIZATION")
print("="*60)

# Get layout positions
pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

# Create edge traces
edge_traces = []
for edge in G.edges(keys=True):
    source, target, key = edge
    x0, y0 = pos[source]
    x1, y1 = pos[target]

    edge_data = G.get_edge_data(source, target, key)

    # Build hover text
    join_info = f"<b>{source} → {target}</b><br>"
    join_info += f"<br><b>Join Keys:</b><br>"
    for src, tgt in zip(edge_data['source_columns'], edge_data['target_columns']):
        join_info += f"  {source}.{src} = {target}.{tgt}<br>"
    join_info += f"<br><b>Type:</b> {edge_data['join_type']}<br>"
    join_info += f"<b>Context:</b> {edge_data['context']}"

    # Color by context
    edge_color = '#888'
    line_width = 2
    if edge_data.get('context') == 'For country level data':
        edge_color = '#4CAF50'  # Green
        line_width = 3
    elif edge_data.get('context') == 'For sector level data':
        edge_color = '#2196F3'  # Blue
        line_width = 3
    elif edge_data.get('context') == 'For rating level data':
        edge_color = '#FF9800'  # Orange
        line_width = 3

    edge_trace = go.Scatter(
        x=[x0, x1, None],
        y=[y0, y1, None],
        mode='lines',
        line=dict(width=line_width, color=edge_color),
        hoverinfo='text',
        text=join_info,
        showlegend=False
    )
    edge_traces.append(edge_trace)

    # Add arrow annotation
    # Calculate midpoint for arrow
    mid_x = (x0 + x1) / 2
    mid_y = (y0 + y1) / 2

# Create node trace
node_x = []
node_y = []
node_text = []
node_hover = []
node_colors = []
node_sizes = []

for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    node_text.append(node)

    # Build hover text
    columns = G.nodes[node].get('columns', [])
    node_info = f"<b>{node}</b><br><br>"
    node_info += f"<b>Total Columns:</b> {len(columns)}<br><br>"
    node_info += f"<b>Columns:</b><br>"

    # Show first 10 columns in hover
    for col in columns[:10]:
        node_info += f"  • {col}<br>"
    if len(columns) > 10:
        node_info += f"  • ... and {len(columns) - 10} more"

    node_hover.append(node_info)

    # Node styling
    node_colors.append('#FF6B6B')  # Red for all nodes
    # Size based on number of columns
    node_sizes.append(20 + (len(columns) / 10))

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode='markers+text',
    hoverinfo='text',
    text=node_text,
    textposition="top center",
    textfont=dict(size=14, color='black', family='Arial Black'),
    hovertext=node_hover,
    marker=dict(
        size=node_sizes,
        color=node_colors,
        line=dict(width=3, color='white'),
        symbol='circle'
    ),
    showlegend=False
)

# Create figure
fig = go.Figure(data=edge_traces + [node_trace])

# Add legend for edge colors
legend_traces = [
    go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(width=3, color='#888'),
        name='Default Join',
        showlegend=True
    ),
    go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(width=3, color='#4CAF50'),
        name='Country Level',
        showlegend=True
    ),
    go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(width=3, color='#2196F3'),
        name='Sector Level',
        showlegend=True
    ),
    go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(width=3, color='#FF9800'),
        name='Rating Level',
        showlegend=True
    )
]

fig.add_traces(legend_traces)

# Update layout
fig.update_layout(
    title=dict(
        text="<b>Database Knowledge Graph</b><br><sub>Hover over nodes and edges for details</sub>",
        font=dict(size=20),
        x=0.5,
        xanchor='center'
    ),
    showlegend=True,
    legend=dict(
        title=dict(text="<b>Join Contexts</b>"),
        x=1.02,
        y=1,
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor='black',
        borderwidth=1
    ),
    hovermode='closest',
    margin=dict(b=40, l=40, r=200, t=100),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    plot_bgcolor='#F5F5F5',
    width=1200,
    height=700
)

# Add arrows using annotations
for edge in G.edges(keys=True):
    source, target, key = edge
    x0, y0 = pos[source]
    x1, y1 = pos[target]

    # Calculate arrow position (80% along the line)
    arrow_x = x0 + 0.8 * (x1 - x0)
    arrow_y = y0 + 0.8 * (y1 - y0)

    edge_data = G.get_edge_data(source, target, key)

    # Color by context
    arrow_color = '#888'
    if edge_data.get('context') == 'For country level data':
        arrow_color = '#4CAF50'
    elif edge_data.get('context') == 'For sector level data':
        arrow_color = '#2196F3'
    elif edge_data.get('context') == 'For rating level data':
        arrow_color = '#FF9800'

    fig.add_annotation(
        x=arrow_x,
        y=arrow_y,
        ax=x0,
        ay=y0,
        xref='x',
        yref='y',
        axref='x',
        ayref='y',
        showarrow=True,
        arrowhead=2,
        arrowsize=1.5,
        arrowwidth=2,
        arrowcolor=arrow_color,
        opacity=0.7
    )

# Save as HTML
output_file = "knowledge_graph_visualization.html"
fig.write_html(output_file)
print(f"\n[OK] Interactive visualization saved to: {output_file}")

# Also create a static matplotlib version
print("\nGenerating static visualization...")

plt.figure(figsize=(14, 10))
plt.title("Database Knowledge Graph\n", fontsize=18, fontweight='bold')

# Draw edges with different colors
for edge in G.edges(keys=True):
    source, target, key = edge
    edge_data = G.get_edge_data(source, target, key)

    # Determine edge color
    edge_color = 'gray'
    edge_width = 2
    edge_style = 'solid'

    if edge_data.get('context') == 'For country level data':
        edge_color = '#4CAF50'
        edge_width = 3
    elif edge_data.get('context') == 'For sector level data':
        edge_color = '#2196F3'
        edge_width = 3
    elif edge_data.get('context') == 'For rating level data':
        edge_color = '#FF9800'
        edge_width = 3

    # Draw edge
    x0, y0 = pos[source]
    x1, y1 = pos[target]
    plt.plot([x0, x1], [y0, y1], color=edge_color, linewidth=edge_width,
             linestyle=edge_style, alpha=0.6)

    # Add arrow
    dx = x1 - x0
    dy = y1 - y0
    plt.arrow(x0 + 0.7*dx, y0 + 0.7*dy, 0.1*dx, 0.1*dy,
              head_width=0.05, head_length=0.05, fc=edge_color, ec=edge_color,
              alpha=0.7)

# Draw nodes
node_colors_list = []
for node in G.nodes():
    columns = G.nodes[node].get('columns', [])
    # Color based on number of columns
    if len(columns) > 100:
        node_colors_list.append('#FF6B6B')  # Red for large tables
    elif len(columns) > 30:
        node_colors_list.append('#FFD93D')  # Yellow for medium tables
    else:
        node_colors_list.append('#6BCB77')  # Green for small tables

nx.draw_networkx_nodes(G, pos, node_color=node_colors_list, node_size=3000,
                       node_shape='o', edgecolors='black', linewidths=3)

# Draw labels
nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold',
                        font_family='sans-serif')

# Add legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#FF6B6B', edgecolor='black', label='Large Table (>100 cols)'),
    Patch(facecolor='#FFD93D', edgecolor='black', label='Medium Table (30-100 cols)'),
    Patch(facecolor='#6BCB77', edgecolor='black', label='Small Table (<30 cols)'),
    plt.Line2D([0], [0], color='gray', linewidth=2, label='Default Join'),
    plt.Line2D([0], [0], color='#4CAF50', linewidth=3, label='Country Level Join'),
    plt.Line2D([0], [0], color='#2196F3', linewidth=3, label='Sector Level Join'),
    plt.Line2D([0], [0], color='#FF9800', linewidth=3, label='Rating Level Join')
]

plt.legend(handles=legend_elements, loc='upper left', fontsize=10,
          frameon=True, fancybox=True, shadow=True)

plt.axis('off')
plt.tight_layout()

# Save static image
static_file = "knowledge_graph_static.png"
plt.savefig(static_file, dpi=300, bbox_inches='tight', facecolor='white')
print(f"[OK] Static visualization saved to: {static_file}")

# Don't show the plot interactively, just save it
# plt.show()

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Total Tables: {len(kg_data['nodes'])}")
print(f"Total Relationships: {len(kg_data['edges'])}")
print(f"\nFiles created:")
print(f"  1. {output_file} (interactive HTML)")
print(f"  2. {static_file} (static PNG)")
print("\nOpen the HTML file in your browser for an interactive experience!")
print("="*60)
