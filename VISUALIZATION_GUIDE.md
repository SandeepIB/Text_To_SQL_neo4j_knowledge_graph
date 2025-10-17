# Knowledge Graph Visualization Guide

## Overview

The Text-to-SQL application now includes an interactive Knowledge Graph visualization feature that allows you to visually inspect the database schema and relationships.

## Features

### 1. **Interactive Graph Visualization**
- Visual representation of all tables (nodes) and their relationships (edges)
- Interactive hover tooltips showing:
  - Table names and column counts
  - Join keys and relationship types
  - Context information

### 2. **Graph Statistics**
- Total number of tables
- Total number of relationships
- Average connections per table
- Connectivity status

### 3. **Table Highlighting**
- Select specific tables to highlight in red
- Helps identify important tables in complex schemas

### 4. **Export Options**

#### JSON Export
Complete graph data including:
- All table names and columns
- All relationships with join keys
- Join types and contexts
- Column descriptions

#### GraphML Export
NetworkX-compatible format that can be:
- Imported into graph analysis tools
- Used in other Python scripts
- Analyzed with NetworkX algorithms

## How to Use

### In the Streamlit App

1. **Launch the application:**
   ```bash
   streamlit run app.py
   ```

2. **Navigate to the "Knowledge Graph" tab**
   - Click on the "🕸️ Knowledge Graph" tab at the top

3. **View the Interactive Graph**
   - Pan: Click and drag
   - Zoom: Use mouse wheel
   - Hover: See details about nodes and edges

4. **Highlight Tables**
   - Use the multiselect dropdown to choose tables to highlight
   - Highlighted tables appear in red

5. **Export Data**
   - Click "📥 Download as JSON" for complete graph data
   - Click "📥 Download as GraphML" for NetworkX format

6. **View Detailed Information**
   - Expand "🔍 View Detailed Graph Data" to see:
     - All table columns
     - All relationship details

### Standalone Visualization

You can also generate a standalone HTML visualization:

```bash
python test_visualization.py
```

This creates:
- `knowledge_graph_visualization.html` - Interactive graph (4.6MB)
- `knowledge_graph_data.json` - Complete graph data (6KB)
- `knowledge_graph.graphml` - NetworkX format

Open the HTML file in any browser to view the interactive graph without running the Streamlit app.

## Understanding the Graph

### Nodes (Tables)
- **Teal circles**: Regular tables
- **Red circles**: Highlighted tables (when selected)
- **Size**: Indicates table importance
- **Labels**: Table names displayed above nodes

### Edges (Relationships)
- **Gray lines**: Join relationships between tables
- **Direction**: Arrow indicates relationship flow
- **Hover**: Shows join keys and relationship type

### Graph Layout
- Uses spring layout algorithm for optimal positioning
- Tables with more connections appear more central
- Related tables cluster together

## Example Use Cases

### 1. **Schema Documentation**
Export the visualization to document your database schema for team members.

### 2. **Query Planning**
Identify the tables and relationships needed for complex queries before writing SQL.

### 3. **Data Lineage**
Trace how data flows between tables using the visual connections.

### 4. **Schema Analysis**
- Identify central tables (high connectivity)
- Find isolated tables
- Discover relationship patterns

## Visualization Options

The graph can be customized by modifying the `visualize_graph_plotly()` method in [app.py:142-231](app.py#L142-L231):

- **Colors**: Change node and edge colors
- **Layout**: Use different NetworkX layout algorithms
- **Size**: Adjust node sizes based on column count
- **Labels**: Customize label positions and fonts

## Technical Details

### Dependencies
- `plotly`: Interactive visualization
- `networkx`: Graph data structure and algorithms
- `matplotlib`: Backend support

### Data Structure
- **Graph Type**: NetworkX DiGraph (directed graph)
- **Node Attributes**: table name, columns list
- **Edge Attributes**: source/target columns, join type, context, description

### Performance
- Optimized for small to medium schemas (< 50 tables)
- Uses spring layout with 50 iterations
- Caches data using Streamlit's @st.cache_data

## Troubleshooting

### Issue: Graph is too cluttered
- Use table highlighting to focus on specific areas
- Export to GraphML and use specialized graph visualization tools like Gephi

### Issue: Labels overlapping
- Zoom in using mouse wheel
- Modify layout parameters in the code

### Issue: Export fails
- Check file permissions in the directory
- Ensure all dependencies are installed

## Future Enhancements

Possible improvements:
- Different layout algorithms (circular, hierarchical, etc.)
- Filter relationships by context (Country, Rating, Sector)
- Show shortest path between selected tables
- Export as PNG/SVG images
- Dark mode support
- Schema comparison (diff between versions)

## Resources

- [NetworkX Documentation](https://networkx.org/)
- [Plotly Graph Objects](https://plotly.com/python/graph-objects/)
- [Streamlit Documentation](https://docs.streamlit.io/)
