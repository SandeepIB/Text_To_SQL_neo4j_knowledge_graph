"""
Complete Streamlit Text-to-SQL Application with Google Gemini
File: app.py

Install dependencies:
pip install streamlit pandas openpyxl networkx google-generativeai google-genai python-dotenv plotly matplotlib

Setup:
1. Create a .env file with your GOOGLE_API_KEY
2. Ensure AI_SampleDataStruture.xlsx is in the same directory
3. Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import networkx as nx
from typing import List, Dict, Optional
import json
import os
from pathlib import Path
from google import genai
from dotenv import load_dotenv
import plotly.graph_objects as go
import matplotlib.pyplot as plt
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY


# ============================================
# CONFIGURATION
# ============================================

# Set your API key in environment variable or .env file
# GOOGLE_API_KEY

EXCEL_FILE_PATH = "AI_SampleDataStruture.xlsx"  # Update path as needed
KNOWLEDGE_GRAPH_OUTPUT_DIR = "knowledge_graph_exports"  # Directory for exports


# ============================================
# KNOWLEDGE GRAPH CLASS
# ============================================

class TableKnowledgeGraph:
    def __init__(self, schemas: Dict, relationships: List[Dict]):
        self.graph = nx.MultiDiGraph()  # Use MultiDiGraph to support multiple edges between same nodes
        self.schemas = schemas
        self.relationships = relationships
        self._build_graph()
    
    def _build_graph(self):
        """Build the knowledge graph from schemas and relationships"""
        # Add nodes (tables)
        for table_name, columns in self.schemas.items():
            self.graph.add_node(
                table_name, 
                columns=[col["name"] for col in columns]
            )
        
        # Add edges (relationships)
        for rel in self.relationships:
            table1 = rel['table1']
            table2 = rel['table2']
            
            # Parse composite keys
            source_cols = [col.strip() for col in rel['join_key_1'].split('+')]
            target_cols = [col.strip() for col in rel['join_key_2'].split('+')]
            
            self.graph.add_edge(
                table1,
                table2,
                source_columns=source_cols,
                target_columns=target_cols,
                join_type=rel.get('join_type', 'INNER'),
                context=rel.get('context', 'default'),
                description=rel.get('description', f"Join {table1} with {table2}")
            )
    
    def get_join_relationships(self, tables: List[str], context: Optional[str] = None) -> List[Dict]:
        """Find all join relationships between given tables"""
        relationships = []

        for i in range(len(tables)):
            for j in range(i + 1, len(tables)):
                source = tables[i]
                target = tables[j]

                # Check both directions - MultiDiGraph returns a dict of edge keys
                for start, end in [(source, target), (target, source)]:
                    if self.graph.has_edge(start, end):
                        # Get all edges between these nodes (MultiDiGraph can have multiple)
                        edges_dict = self.graph.get_edge_data(start, end)

                        # Iterate through all edges between these two nodes
                        for edge_key, edge_data in edges_dict.items():
                            # Filter by context if provided
                            edge_context = edge_data.get('context', 'default')

                            # Context filtering logic:
                            # - If no context is specified, include all edges
                            # - If context is specified, prefer context-specific edges but fallback to default if no context-specific edge exists
                            if context:
                                context_lower = context.lower()
                                edge_context_lower = edge_context.lower()

                                # Check if this edge has a context-specific match
                                has_context_match = context_lower in edge_context_lower
                                is_default = edge_context == 'default'

                                # Check if there are any context-specific edges for this table pair
                                has_context_specific_edges = any(
                                    context_lower in ed.get('context', 'default').lower()
                                    for ed in edges_dict.values()
                                    if ed.get('context', 'default') != 'default'
                                )

                                # Include edge if:
                                # 1. It matches the context, OR
                                # 2. It's a default edge AND there are no context-specific edges for this table pair
                                if not has_context_match:
                                    if is_default and not has_context_specific_edges:
                                        pass  # Include default edge as fallback
                                    else:
                                        continue  # Skip this edge

                            # Build join condition
                            source_cols = edge_data['source_columns']
                            target_cols = edge_data['target_columns']

                            join_conditions = [
                                f"{start}.{src} = {end}.{tgt}"
                                for src, tgt in zip(source_cols, target_cols)
                            ]

                            relationships.append({
                                "from_table": start,
                                "to_table": end,
                                "join_condition": " AND ".join(join_conditions),
                                "join_type": edge_data['join_type'],
                                "context": edge_data.get('context', 'default'),
                                "description": edge_data.get('description', '')
                            })

        return relationships
    
    def get_all_tables_needed(self, tables: List[str]) -> List[str]:
        """Find all tables including intermediate ones needed for joins"""
        all_tables = set(tables)
        
        for i in range(len(tables)):
            for j in range(i + 1, len(tables)):
                try:
                    path = nx.shortest_path(
                        self.graph.to_undirected(), 
                        tables[i], 
                        tables[j]
                    )
                    all_tables.update(path)
                except nx.NetworkXNoPath:
                    pass
        
        return list(all_tables)
    
    def get_columns_for_tables(self, tables: List[str]) -> Dict:
        """Get schema information for specified tables"""
        return {table: self.schemas.get(table, []) for table in tables}

    def visualize_graph_plotly(self, highlight_tables: List[str] = None):
        """Create an interactive Plotly visualization of the knowledge graph"""
        # Get graph layout using spring layout
        pos = nx.spring_layout(self.graph, k=2, iterations=50)

        # Create edge traces - handle MultiDiGraph with multiple edges
        edge_traces = []
        for edge in self.graph.edges(keys=True):  # Include keys for MultiDiGraph
            source, target, key = edge
            x0, y0 = pos[source]
            x1, y1 = pos[target]

            # Get specific edge data using the key
            edge_data = self.graph.get_edge_data(source, target, key)
            join_info = f"{source} → {target}<br>"
            join_info += f"Keys: {', '.join(edge_data['source_columns'])} = {', '.join(edge_data['target_columns'])}<br>"
            join_info += f"Type: {edge_data['join_type']}<br>"
            join_info += f"Context: {edge_data.get('context', 'default')}"

            # Color edges differently based on context
            edge_color = '#888'
            if edge_data.get('context') == 'For country level data':
                edge_color = '#4CAF50'  # Green
            elif edge_data.get('context') == 'For sector level data':
                edge_color = '#2196F3'  # Blue
            elif edge_data.get('context') == 'For rating level data':
                edge_color = '#FF9800'  # Orange

            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=2, color=edge_color),
                hoverinfo='text',
                text=join_info,
                showlegend=False
            )
            edge_traces.append(edge_trace)

        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []

        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            # Get column count
            columns = self.graph.nodes[node].get('columns', [])
            node_info = f"<b>{node}</b><br>"
            node_info += f"Columns: {len(columns)}<br>"
            node_info += f"Sample: {', '.join(columns[:5])}"
            if len(columns) > 5:
                node_info += "..."

            node_text.append(node_info)

            # Color nodes based on whether they're highlighted
            if highlight_tables and node in highlight_tables:
                node_colors.append('#FF6B6B')  # Red for highlighted
                node_sizes.append(30)
            else:
                node_colors.append('#4ECDC4')  # Teal for normal
                node_sizes.append(20)

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[node for node in self.graph.nodes()],
            textposition="top center",
            textfont=dict(size=12, color='black'),
            hovertext=node_text,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            showlegend=False
        )

        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace])

        fig.update_layout(
            title=dict(text="Database Knowledge Graph", font=dict(size=16)),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=600
        )

        return fig

    def get_graph_stats(self) -> Dict: 
        """Get statistics about the knowledge graph"""
        return {
            "total_tables": self.graph.number_of_nodes(),
            "total_relationships": self.graph.number_of_edges(),
            "tables": list(self.graph.nodes()),
            "average_connections": sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0,
            "is_connected": nx.is_weakly_connected(self.graph)
        }

    def export_graph_data(self) -> Dict:
        """Export complete graph data for inspection"""
        export_data = {
            "nodes": [],
            "edges": []
        }

        # Export nodes
        for node in self.graph.nodes():
            node_data = {
                "table_name": node,
                "columns": self.graph.nodes[node].get('columns', []),
                "column_count": len(self.graph.nodes[node].get('columns', []))
            }
            export_data["nodes"].append(node_data)

        # Export edges - handle MultiDiGraph with multiple edges
        for edge in self.graph.edges(keys=True):  # Include keys for MultiDiGraph
            source, target, key = edge
            edge_data = self.graph.get_edge_data(source, target, key)
            export_data["edges"].append({
                "from": source,
                "to": target,
                "source_columns": edge_data['source_columns'],
                "target_columns": edge_data['target_columns'],
                "join_type": edge_data['join_type'],
                "context": edge_data.get('context', 'default'),
                "description": edge_data.get('description', '')
            })

        return export_data


# ============================================
# DATA LOADING FUNCTIONS
# ============================================

@st.cache_data
def load_excel_data(file_path: str) -> tuple:
    """Load schemas and relationships from Excel file (cached)"""
    try:
        # Read all sheets
        counterparty_df = pd.read_excel(file_path, sheet_name="Counterparty New")
        trade_df = pd.read_excel(file_path, sheet_name="Trade New")
        concentration_df = pd.read_excel(file_path, sheet_name="Concentration New")
        joins_df = pd.read_excel(file_path, sheet_name="Joins")

        # Build schemas dictionary
        schemas = {
            "Counterparty": [
                {
                    "name": row["Column Name"],
                    "description": row["Description"],
                    "example": row.get("Example Value", "")
                }
                for _, row in counterparty_df.iterrows()
            ],
            "Trade": [
                {
                    "name": row["Column Name"],
                    "description": row["Description"],
                    "example": row.get("Example Value", "")
                }
                for _, row in trade_df.iterrows()
            ],
            "Concentration": [
                {
                    "name": row["Column Name"],
                    "description": row["Description"],
                    "example": row.get("Example Value", "")
                }
                for _, row in concentration_df.iterrows()
            ]
        }

        # Build relationships list
        relationships = []
        for _, row in joins_df.iterrows():
            rel = {
                "table1": row["Table1"],
                "table2": row["Table2"],
                "join_key_1": row["Join Key Table1"],
                "join_key_2": row["Join Key Table2"],
                "join_type": "INNER",
                "context": row.get("Context", "default") if pd.notna(row.get("Context")) else "default",
                "description": f"Join {row['Table1']} with {row['Table2']}"
            }
            relationships.append(rel)

        return schemas, relationships

    except Exception as e:
        st.error(f"Error loading Excel file: {str(e)}")
        return None, None


@st.cache_resource
def build_knowledge_graph(file_path: str) -> TableKnowledgeGraph:
    """Build and cache the knowledge graph (cached as a resource)"""
    schemas, relationships = load_excel_data(file_path)
    if schemas and relationships:
        return TableKnowledgeGraph(schemas, relationships)
    return None


def save_knowledge_graph(kg: TableKnowledgeGraph):
    """Save knowledge graph to files on app startup"""
    from datetime import datetime

    # Create output directory if it doesn't exist
    output_dir = Path(KNOWLEDGE_GRAPH_OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save as JSON
    json_path = output_dir / f"knowledge_graph_{timestamp}.json"
    graph_data = kg.export_graph_data()
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)

    # Also save a "latest" version without timestamp
    latest_json_path = output_dir / "knowledge_graph_latest.json"
    with open(latest_json_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)

    # Save as GraphML
    graphml_path = output_dir / f"knowledge_graph_{timestamp}.graphml"
    latest_graphml_path = output_dir / "knowledge_graph_latest.graphml"

    # Create a new clean graph for GraphML export (lists are not supported)
    export_graph = nx.MultiDiGraph()

    # Add nodes with converted attributes
    for node in kg.graph.nodes():
        node_attrs = {}
        for key, value in kg.graph.nodes[node].items():
            if isinstance(value, list):
                node_attrs[key] = ','.join(str(v) for v in value)
            else:
                node_attrs[key] = str(value) if value is not None else ''
        export_graph.add_node(node, **node_attrs)

    # Add edges with converted attributes
    for source, target, key, edge_data in kg.graph.edges(keys=True, data=True):
        clean_edge_data = {}
        for attr_key, attr_value in edge_data.items():
            if isinstance(attr_value, list):
                clean_edge_data[attr_key] = ','.join(str(v) for v in attr_value)
            else:
                clean_edge_data[attr_key] = str(attr_value) if attr_value is not None else ''
        export_graph.add_edge(source, target, key=key, **clean_edge_data)

    nx.write_graphml(export_graph, str(graphml_path))
    nx.write_graphml(export_graph, str(latest_graphml_path))

    # Save statistics as text file
    stats_path = output_dir / f"knowledge_graph_stats_{timestamp}.txt"
    latest_stats_path = output_dir / "knowledge_graph_stats_latest.txt"

    stats = kg.get_graph_stats()
    stats_content = f"""Knowledge Graph Statistics
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{'=' * 60}

Total Tables: {stats['total_tables']}
Total Relationships: {stats['total_relationships']}
Average Connections per Table: {stats['average_connections']:.2f}
Is Connected: {'Yes' if stats['is_connected'] else 'No'}

Tables:
{chr(10).join(f"  - {table}" for table in stats['tables'])}

Detailed Relationships:
"""

    for edge_data in graph_data['edges']:
        stats_content += f"\n{edge_data['from']} → {edge_data['to']}\n"
        stats_content += f"  Join: {', '.join(edge_data['source_columns'])} = {', '.join(edge_data['target_columns'])}\n"
        stats_content += f"  Type: {edge_data['join_type']} | Context: {edge_data['context']}\n"
        stats_content += f"  Description: {edge_data['description']}\n"

    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write(stats_content)

    with open(latest_stats_path, 'w', encoding='utf-8') as f:
        f.write(stats_content)

    return {
        'json_path': json_path,
        'graphml_path': graphml_path,
        'stats_path': stats_path,
        'timestamp': timestamp
    }


# ============================================
# GEMINI LLM INTEGRATION
# ============================================

class GeminiClient:
    def __init__(self):
        """Initialize Gemini client using the new google-genai SDK"""
        api_key = GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        # Use the new Client API (REST-based, no gRPC issues)
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.0-flash-exp'  # Use available model

        # Configure generation settings
        self.generation_config = {
            'temperature': 0.1,  # Low temperature for more deterministic outputs
            'max_output_tokens': 2048,
        }

    def call(self, prompt: str, system_instruction: str = None) -> str:
        """Make Gemini API call"""
        try:
            # Combine system instruction with prompt if provided
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"
            else:
                full_prompt = prompt

            # Generate response using the new SDK
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=self.generation_config
            )

            return response.text

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


# ============================================
# TEXT-TO-SQL PIPELINE
# ============================================

class TextToSQLPipeline:
    def __init__(self, kg: TableKnowledgeGraph, llm_client: GeminiClient):
        self.kg = kg
        self.llm = llm_client
    
    def identify_tables(self, user_query: str) -> Dict:
        """Step 1: Identify required tables using LLM"""
        # Build schema context
        schema_context = "Available tables and their descriptions:\n\n"

        for table_name, columns in self.kg.schemas.items():
            schema_context += f"Table: {table_name}\n"
            schema_context += "Key columns:\n"
            for col in columns[:15]:  # Show first 15 columns
                schema_context += f"  - {col['name']}: {col['description']}\n"
            schema_context += "\n"

        print(schema_context)

        prompt = f"""{schema_context}

        

User Query: "{user_query}"

Based on the query, identify which tables are needed. Follow these guidelines:

1. If the query asks about "concentration", you typically need BOTH the "Counterparty" and "Concentration" tables joined together.
2. If the query asks about "trades", you typically need BOTH the "Counterparty" and "Trade" tables joined together.
3. If the query specifically asks only about counterparty attributes, you may only need the "Counterparty" table.

Also identify if there's a specific context mentioned:
- If the query mentions "country" or "countries" or "by country", set context to "Country"
- If the query mentions "rating" or "ratings" or "by rating", set context to "Rating"
- If the query mentions "sector" or "sectors" or "by sector", set context to "Sector"
- Otherwise, set context to null

IMPORTANT: Use the EXACT table names as shown above (e.g., "Counterparty", "Concentration", "Trade"), not descriptive names.

Return ONLY a JSON object with this exact structure (no additional text, no markdown formatting):
{{
    "tables": ["Counterparty", "Concentration"],
    "context": "Country",
    "reasoning": "brief explanation"
}}

The table names in the "tables" array must match exactly the table names shown in the schema above."""

        system_instruction = "You are a database expert. Analyze queries and identify required tables. Return only valid JSON without any markdown formatting or additional text."

        response = self.llm.call(prompt, system_instruction)
        
        # Parse JSON from response
        try:
            # Clean up response - remove markdown code blocks if present
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            # Try to extract JSON if there's extra text
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                result = json.loads(json_str)
                return result
            else:
                result = json.loads(response)
                return result
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse LLM response: {response}")
            raise e
    
    def get_join_info(self, tables: List[str], context: Optional[str]) -> Dict:
        """Step 2: Get join information from Knowledge Graph"""
        # Get all tables including intermediate ones
        all_tables = self.kg.get_all_tables_needed(tables)

        # Get join relationships
        joins = self.kg.get_join_relationships(all_tables, context)

        # Get schemas
        schemas = self.kg.get_columns_for_tables(all_tables)

        return {
            "requested_tables": tables,
            "all_tables_needed": all_tables,
            "joins": joins,
            "schemas": schemas,
            "context": context
        }
    
    def generate_sql(self, user_query: str, join_info: Dict) -> str:
        """Step 3: Generate SQL query using LLM"""
        # Build comprehensive context
        context = f"""Generate a SQL query for the following request.

USER QUERY: "{user_query}"

TABLES TO USE: {', '.join(join_info['all_tables_needed'])}

JOIN RELATIONSHIPS:
"""

        for join in join_info['joins']:
            context += f"\n{join['from_table']} {join['join_type']} JOIN {join['to_table']}"
            context += f"\nON {join['join_condition']}"

            # Emphasize multi-part joins
            if " AND " in join['join_condition']:
                context += f"\n*** THIS IS A COMPOSITE JOIN - YOU MUST USE ALL CONDITIONS: {join['join_condition']} ***"

            if join.get('description'):
                context += f"\n({join['description']})"
            context += "\n"
        
        context += "\n\nTABLE SCHEMAS (with all columns and descriptions):\n"
        
        for table, columns in join_info['schemas'].items():
            context += f"\n{table}:\n"
            for col in columns:
                context += f"  - {col['name']}: {col['description']}\n"
        
        context += """

INSTRUCTIONS FOR SQL GENERATION:

1. JOIN CONDITIONS - ABSOLUTELY CRITICAL:
   - Copy the EXACT join condition from above into your ON clause
   - If you see " AND " in the join condition, that means MULTIPLE conditions - use ALL of them
   - DO NOT simplify or omit any part of the join condition
   - DO NOT use only one part of a multi-part join condition

2. SELECT relevant columns based on the user query

3. Include appropriate WHERE clauses if needed

4. Use table aliases for readability

5. Format properly with indentation

EXAMPLE OF CORRECT JOIN USAGE:
If the join condition provided is:
"Counterparty.Entity = Trade.Entity AND Counterparty.Counterparty ID = Trade.Reporting Counterparty ID"

Your ON clause MUST be:
ON c.Entity = t.Entity AND c."Counterparty ID" = t."Reporting Counterparty ID"

NOT just: ON c."Counterparty ID" = t."Reporting Counterparty ID"  (WRONG - missing Entity)
NOT just: ON c.Entity = t.Entity  (WRONG - missing Counterparty ID)

Return ONLY the SQL query without any explanations, markdown formatting, or code blocks."""
        
        system_instruction = "You are a SQL expert. Generate accurate, well-formatted SQL queries based on provided schema and join information. CRITICAL: You MUST use ALL parts of every join condition provided - never omit any condition. Return only the SQL query without any markdown formatting or explanations."
        
        sql_query = self.llm.call(context, system_instruction)
        
        # Clean up the response
        sql_query = sql_query.strip()
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        elif sql_query.startswith('```'):
            sql_query = sql_query[3:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        
        return sql_query.strip()
    
    def process(self, user_query: str) -> Dict:
        """Execute complete pipeline"""
        # Step 1: Identify tables
        table_info = self.identify_tables(user_query)
        
        # Step 2: Get join information
        join_info = self.get_join_info(
            table_info['tables'], 
            table_info.get('context')
        )
        
        # Step 3: Generate SQL
        sql_query = self.generate_sql(user_query, join_info)
        
        return {
            "user_query": user_query,
            "table_info": table_info,
            "join_info": join_info,
            "sql_query": sql_query
        }


# ============================================
# STREAMLIT UI
# ============================================

def main():
    st.set_page_config(
        page_title="Text-to-SQL Generator",
        page_icon="🔍",
        layout="wide"
    )

    st.title("🔍 Natural Language to SQL Query Generator")
    st.markdown("Convert your natural language questions into SQL queries using Google Gemini!")

    # Create tabs
    tab1, tab2 = st.tabs(["🚀 Query Generator", "🕸️ Knowledge Graph"])

    # Sidebar configuration
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This app converts natural language queries to SQL using:
        1. **Google Gemini** to identify required tables
        2. **Knowledge Graph** to fetch join relationships
        3. **Google Gemini** to generate final SQL query

        **Powered by:** Gemini 2.0 Flash
        """)

        st.divider()

        # Model info
        with st.expander("🤖 Model Information"):
            st.markdown("""
            **Model:** Gemini 2.0 Flash (Experimental)

            **Features:**
            - Advanced reasoning
            - Fast response time
            - JSON mode support
            - Low latency
            """)

        st.divider()

        # Data source info
        with st.expander("📁 Data Source"):
            st.markdown(f"""
            **Schema File:** `{EXCEL_FILE_PATH}`

            Using predefined database schema with tables:
            - Counterparty
            - Trade
            - Concentration
            - Joins configuration
            """)

    # Build knowledge graph once (cached)
    kg = build_knowledge_graph(EXCEL_FILE_PATH)

    if kg:
        # Auto-save knowledge graph on app startup
        try:
            saved_files = save_knowledge_graph(kg)
            st.sidebar.success(f"Knowledge graph exported!")
            with st.sidebar.expander("View Export Details"):
                st.markdown(f"**Timestamp:** {saved_files['timestamp']}")
                st.markdown(f"**JSON:** `{saved_files['json_path']}`")
                st.markdown(f"**GraphML:** `{saved_files['graphml_path']}`")
                st.markdown(f"**Stats:** `{saved_files['stats_path']}`")
        except Exception as e:
            st.sidebar.warning(f"Could not auto-save knowledge graph: {e}")

    # TAB 1: Query Generator
    with tab1:
        # Main content
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📝 Enter Your Query")

            # Example queries
            example_queries = [
                "Show all trades for counterparties with AAA rating",
                "What is the concentration by country?",
                "List all counterparties in the Financial Services sector",
                "Show trades grouped by counterparty country",
            ]

            selected_example = st.selectbox(
                "Try an example query:",
                [""] + example_queries,
                help="Select an example or write your own"
            )

            user_query = st.text_area(
                "Your natural language query:",
                value=selected_example,
                height=100,
                placeholder="e.g., Show me all trades for counterparties rated AAA"
            )

            generate_button = st.button("🚀 Generate SQL", type="primary", use_container_width=True)

        with col2:
            st.subheader("💡 Tips")
            st.info("""
            **Be specific in your queries:**
            - Mention table names if you know them
            - Specify filters (e.g., "with AAA rating")
            - Indicate grouping or aggregation needs
            - Mention if you want data by country, rating, or sector
            """)

        # Process query
        if generate_button:
            if not user_query:
                st.warning("Please enter a query first!")
                return

            if not GOOGLE_API_KEY:
                st.error("Google API key not found in environment!")
                st.info("Please add GOOGLE_API_KEY to your .env file")
                return

            try:
                with st.spinner("🔄 Processing your query with Gemini..."):
                    # Reuse the knowledge graph already loaded at app startup
                    if not kg:
                        st.error("Failed to load knowledge graph!")
                        return

                    # Initialize components
                    llm_client = GeminiClient()
                    pipeline = TextToSQLPipeline(kg, llm_client)

                    # Process query
                    result = pipeline.process(user_query)

                    # Display results
                    st.success("✅ SQL query generated successfully!")

                    # Show the SQL query prominently
                    st.subheader("📊 Generated SQL Query")
                    st.code(result['sql_query'], language='sql')

                    # Download button
                    st.download_button(
                        label="📥 Download SQL",
                        data=result['sql_query'],
                        file_name="generated_query.sql",
                        mime="text/plain"
                    )

                    # Show details in expander
                    with st.expander("🔍 View Processing Details"):
                        col_a, col_b = st.columns(2)

                        with col_a:
                            st.markdown("### Step 1: Table Identification")
                            st.json(result['table_info'])

                        with col_b:
                            st.markdown("### Step 2: Join Information")
                            st.write(f"**Tables needed:** {', '.join(result['join_info']['all_tables_needed'])}")
                            st.write(f"**Number of joins:** {len(result['join_info']['joins'])}")

                        st.markdown("### Join Details")
                        for i, join in enumerate(result['join_info']['joins'], 1):
                            st.markdown(f"**Join {i}:** {join['from_table']} → {join['to_table']}")
                            st.code(join['join_condition'], language='sql')

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                with st.expander("View Error Details"):
                    st.exception(e)

    # TAB 2: Knowledge Graph Visualization
    with tab2:
        st.subheader("🕸️ Database Knowledge Graph Visualization")
        st.markdown("""
        This interactive graph shows the relationships between tables in your database.
        - **Nodes** represent tables
        - **Edges** represent join relationships
        - Hover over nodes and edges to see details
        """)

        if not kg:
            st.error("Failed to load knowledge graph. Please check your data file.")
            return

        # Display graph statistics
        stats = kg.get_graph_stats()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tables", stats['total_tables'])
        with col2:
            st.metric("Total Relationships", stats['total_relationships'])
        with col3:
            st.metric("Avg Connections", f"{stats['average_connections']:.1f}")
        with col4:
            st.metric("Connected", "Yes" if stats['is_connected'] else "No")

        st.divider()

        # Option to highlight specific tables
        st.markdown("#### Highlight Specific Tables")
        selected_tables = st.multiselect(
            "Select tables to highlight in red:",
            options=stats['tables'],
            default=[]
        )

        # Display the graph
        fig = kg.visualize_graph_plotly(highlight_tables=selected_tables if selected_tables else None)
        st.plotly_chart(fig, use_container_width=True)

        # Export options
        st.divider()
        st.markdown("#### Export Graph Data")

        col_a, col_b = st.columns(2)

        with col_a:
            # Export as JSON
            graph_data = kg.export_graph_data()
            graph_json = json.dumps(graph_data, indent=2)

            st.download_button(
                label="📥 Download as JSON",
                data=graph_json,
                file_name="knowledge_graph.json",
                mime="application/json",
                use_container_width=True
            )

        with col_b:
            # Export as GraphML (NetworkX format)
            # Convert list attributes to strings for GraphML compatibility
            import io
            buffer = io.BytesIO()

            # Create a copy of the graph for export
            export_graph = kg.graph.copy()
            for node in export_graph.nodes():
                if 'columns' in export_graph.nodes[node]:
                    export_graph.nodes[node]['columns'] = ','.join(export_graph.nodes[node]['columns'])
            # Handle MultiDiGraph edges
            for edge in export_graph.edges(keys=True):
                source, target, key = edge
                edge_data = export_graph.get_edge_data(source, target, key)
                if 'source_columns' in edge_data:
                    edge_data['source_columns'] = ','.join(edge_data['source_columns'])
                if 'target_columns' in edge_data:
                    edge_data['target_columns'] = ','.join(edge_data['target_columns'])

            nx.write_graphml(export_graph, buffer)
            buffer.seek(0)

            st.download_button(
                label="📥 Download as GraphML",
                data=buffer.getvalue(),
                file_name="knowledge_graph.graphml",
                mime="application/xml",
                use_container_width=True
            )

        # Show detailed graph information
        with st.expander("🔍 View Detailed Graph Data"):
            st.markdown("### Tables (Nodes)")
            for node_data in graph_data['nodes']:
                st.markdown(f"**{node_data['table_name']}** ({node_data['column_count']} columns)")
                with st.container():
                    cols_str = ", ".join(node_data['columns'])
                    st.text(cols_str)
                st.divider()

            st.markdown("### Relationships (Edges)")
            for edge_data in graph_data['edges']:
                st.markdown(f"**{edge_data['from']}** → **{edge_data['to']}**")
                st.text(f"Join: {', '.join(edge_data['source_columns'])} = {', '.join(edge_data['target_columns'])}")
                st.text(f"Type: {edge_data['join_type']} | Context: {edge_data['context']}")
                st.caption(edge_data['description'])
                st.divider()


if __name__ == "__main__":
    main()