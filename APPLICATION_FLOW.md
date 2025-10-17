# Text-to-SQL Application - Complete Flow Documentation

## Table of Contents
1. [Application Overview](#application-overview)
2. [Architecture Components](#architecture-components)
3. [Detailed Flow](#detailed-flow)
4. [Step-by-Step Process](#step-by-step-process)
5. [Code Walkthrough](#code-walkthrough)
6. [Example Execution](#example-execution)

---

## Application Overview

This is a **Natural Language to SQL Query Generator** that converts user questions in plain English into valid SQL queries using:
- **Google Gemini AI** (LLM) for natural language understanding
- **Knowledge Graph** for database schema and relationship management
- **Streamlit** for the web interface

### High-Level Flow
```
User Query (Natural Language)
    ↓
[Step 1] LLM identifies required tables
    ↓
[Step 2] Knowledge Graph finds join relationships
    ↓
[Step 3] LLM generates SQL with proper joins
    ↓
SQL Query Output
```

---

## Architecture Components

### 1. **Data Layer** (`AI_SampleDataStruture.xlsx`)
Excel file containing:
- **Counterparty New**: 129 columns about counterparties (companies, ratings, countries, sectors)
- **Trade New**: 38 columns about financial trades
- **Concentration New**: 7 columns about risk concentration metrics
- **Joins**: Defines how tables should be joined with context-specific relationships

### 2. **Knowledge Graph** (`TableKnowledgeGraph` class)
- **Technology**: NetworkX MultiDiGraph
- **Nodes**: Database tables (Counterparty, Trade, Concentration)
- **Edges**: Join relationships with:
  - Source columns (e.g., Entity, Counterparty ID)
  - Target columns (e.g., Entity, Reporting Counterparty ID)
  - Context (default, "For country level data", "For sector level data", etc.)

### 3. **LLM Client** (`GeminiClient` class)
- Uses Google's Gemini 2.0 Flash model
- Low temperature (0.1) for deterministic outputs
- Handles two main tasks:
  1. Table identification
  2. SQL generation

### 4. **Text-to-SQL Pipeline** (`TextToSQLPipeline` class)
Orchestrates the three-step process:
1. `identify_tables()` - Uses LLM to find relevant tables
2. `get_join_info()` - Queries knowledge graph for relationships
3. `generate_sql()` - Uses LLM to create final SQL

### 5. **Streamlit UI**
Two tabs:
- **Query Generator**: Main interface for SQL generation
- **Knowledge Graph**: Interactive visualization of database schema

---

## Detailed Flow

### Phase 1: Application Startup

```
┌─────────────────────────────────────────┐
│ 1. Streamlit Server Starts             │
│    - Loads environment (.env)           │
│    - Imports dependencies               │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 2. main() function executes             │
│    - Sets page config                   │
│    - Creates UI layout                  │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 3. build_knowledge_graph() (CACHED)     │
│    ├─> load_excel_data()                │
│    │   ├─> Read Excel sheets            │
│    │   ├─> Parse schemas                │
│    │   └─> Parse relationships          │
│    └─> TableKnowledgeGraph()            │
│        ├─> Create NetworkX graph        │
│        ├─> Add table nodes              │
│        └─> Add join edges               │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 4. save_knowledge_graph()               │
│    - Export to JSON                     │
│    - Export to GraphML                  │
│    - Generate statistics                │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 5. Display UI                           │
│    - Show sidebar with info             │
│    - Show tabs (Query Gen, KG Viz)     │
│    - Wait for user interaction          │
└─────────────────────────────────────────┘
```

### Phase 2: Query Processing (When User Clicks "Generate SQL")

```
┌────────────────────────────────────────────────────────┐
│ USER INPUTS QUERY                                      │
│ Example: "Show all trades for counterparties          │
│          with AAA rating"                              │
└──────────────────┬─────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────────────────┐
│ STEP 1: IDENTIFY TABLES (LLM Call #1)                 │
│ ┌────────────────────────────────────────────────────┐ │
│ │ pipeline.identify_tables(user_query)               │ │
│ └──┬─────────────────────────────────────────────────┘ │
│    │                                                    │
│    │ Prompt sent to Gemini LLM:                        │
│    │ ┌────────────────────────────────────────────┐   │
│    │ │ Available tables and their descriptions:   │   │
│    │ │                                            │   │
│    │ │ Table: Counterparty                        │   │
│    │ │   - Entity: Entity identifier              │   │
│    │ │   - Counterparty ID: Unique ID             │   │
│    │ │   - Internal Rating: Credit rating         │   │
│    │ │   ...                                      │   │
│    │ │                                            │   │
│    │ │ Table: Trade                               │   │
│    │ │   - Trade ID: Unique trade identifier      │   │
│    │ │   - Reporting Counterparty ID: CP ID       │   │
│    │ │   ...                                      │   │
│    │ │                                            │   │
│    │ │ User Query: "Show all trades for           │   │
│    │ │ counterparties with AAA rating"            │   │
│    │ │                                            │   │
│    │ │ Identify tables needed and context.        │   │
│    │ └────────────────────────────────────────────┘   │
│    │                                                    │
│    ↓                                                    │
│    LLM Response (JSON):                                │
│    ┌────────────────────────────────────────────┐     │
│    │ {                                          │     │
│    │   "tables": ["Counterparty", "Trade"],     │     │
│    │   "context": null,                         │     │
│    │   "reasoning": "Need both Counterparty     │     │
│    │                 for rating and Trade       │     │
│    │                 for trade data"            │     │
│    │ }                                          │     │
│    └────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────────────────┐
│ STEP 2: GET JOIN INFORMATION (Knowledge Graph Query)  │
│ ┌────────────────────────────────────────────────────┐ │
│ │ pipeline.get_join_info(tables, context)            │ │
│ └──┬─────────────────────────────────────────────────┘ │
│    │                                                    │
│    │ A. get_all_tables_needed()                        │
│    │    - Check if intermediate tables needed          │
│    │    - Use NetworkX shortest path algorithm         │
│    │    Result: ["Counterparty", "Trade"]              │
│    │                                                    │
│    │ B. get_join_relationships()                       │
│    │    ┌───────────────────────────────────────┐     │
│    │    │ For each table pair:                  │     │
│    │    │   1. Check graph.has_edge()           │     │
│    │    │   2. Get edge data (MultiDiGraph)     │     │
│    │    │   3. Apply context filtering:         │     │
│    │    │      - If context specified:          │     │
│    │    │        * Use context-specific edge    │     │
│    │    │      - If no context:                 │     │
│    │    │        * Use default edge as fallback │     │
│    │    │   4. Build join condition string      │     │
│    │    └───────────────────────────────────────┘     │
│    │                                                    │
│    │    Result: [                                      │
│    │      {                                            │
│    │        "from_table": "Counterparty",              │
│    │        "to_table": "Trade",                       │
│    │        "join_condition":                          │
│    │          "Counterparty.Entity = Trade.Entity      │
│    │           AND Counterparty.Counterparty ID =      │
│    │           Trade.Reporting Counterparty ID",       │
│    │        "join_type": "INNER",                      │
│    │        "context": "default"                       │
│    │      }                                            │
│    │    ]                                              │
│    │                                                    │
│    │ C. get_columns_for_tables()                       │
│    │    - Retrieve full schema for each table          │
│    │                                                    │
│    ↓                                                    │
│    Return join_info dict with:                         │
│      - requested_tables                                │
│      - all_tables_needed                               │
│      - joins (with conditions)                         │
│      - schemas (column details)                        │
│      - context                                         │
└────────────────────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────────────────┐
│ STEP 3: GENERATE SQL (LLM Call #2)                    │
│ ┌────────────────────────────────────────────────────┐ │
│ │ pipeline.generate_sql(user_query, join_info)       │ │
│ └──┬─────────────────────────────────────────────────┘ │
│    │                                                    │
│    │ Prompt sent to Gemini LLM:                        │
│    │ ┌────────────────────────────────────────────┐   │
│    │ │ USER QUERY: "Show all trades for           │   │
│    │ │ counterparties with AAA rating"            │   │
│    │ │                                            │   │
│    │ │ TABLES TO USE: Counterparty, Trade         │   │
│    │ │                                            │   │
│    │ │ JOIN RELATIONSHIPS:                        │   │
│    │ │ Counterparty INNER JOIN Trade              │   │
│    │ │ ON Counterparty.Entity = Trade.Entity      │   │
│    │ │    AND Counterparty.Counterparty ID =      │   │
│    │ │    Trade.Reporting Counterparty ID         │   │
│    │ │ *** THIS IS A COMPOSITE JOIN -             │   │
│    │ │     YOU MUST USE ALL CONDITIONS ***        │   │
│    │ │                                            │   │
│    │ │ TABLE SCHEMAS:                             │   │
│    │ │ Counterparty:                              │   │
│    │ │   - Entity: Entity identifier              │   │
│    │ │   - Counterparty ID: Unique ID             │   │
│    │ │   - Internal Rating: Credit rating         │   │
│    │ │   ...                                      │   │
│    │ │ Trade:                                     │   │
│    │ │   - Trade ID: Unique trade identifier      │   │
│    │ │   - Entity: Entity identifier              │   │
│    │ │   - Reporting Counterparty ID: CP ID       │   │
│    │ │   ...                                      │   │
│    │ │                                            │   │
│    │ │ INSTRUCTIONS:                              │   │
│    │ │ 1. Use COMPLETE join conditions            │   │
│    │ │ 2. Select relevant columns                 │   │
│    │ │ 3. Add WHERE clause for AAA rating         │   │
│    │ │ 4. Use table aliases                       │   │
│    │ │ 5. Format properly                         │   │
│    │ └────────────────────────────────────────────┘   │
│    │                                                    │
│    ↓                                                    │
│    LLM Response (SQL):                                 │
│    ┌────────────────────────────────────────────┐     │
│    │ SELECT t.*                                 │     │
│    │ FROM Counterparty AS c                     │     │
│    │ INNER JOIN Trade AS t                      │     │
│    │   ON c.Entity = t.Entity                   │     │
│    │   AND c."Counterparty ID" =                │     │
│    │       t."Reporting Counterparty ID"        │     │
│    │ WHERE c."Internal Rating" = 'AAA';         │     │
│    └────────────────────────────────────────────┘     │
│    │                                                    │
│    │ Clean up response (remove markdown if present)    │
│    ↓                                                    │
│    Return final SQL query                              │
└────────────────────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────────────────┐
│ DISPLAY RESULTS                                        │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 1. Show SQL query with syntax highlighting         │ │
│ │ 2. Add download button                             │ │
│ │ 3. Show processing details in expander:            │ │
│ │    - Table identification info                     │ │
│ │    - Join relationships found                      │ │
│ │    - Context used                                  │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Process

### Startup Phase

#### Step 1: Load Environment
```python
# .env file loaded
GOOGLE_API_KEY=your_api_key_here
```

#### Step 2: Build Knowledge Graph (CACHED)
```python
@st.cache_resource
def build_knowledge_graph(file_path: str):
    # Read Excel file
    schemas, relationships = load_excel_data(file_path)

    # Create graph
    kg = TableKnowledgeGraph(schemas, relationships)
    # - Adds 3 nodes (tables)
    # - Adds 4 edges (relationships)

    return kg
```

**Graph Structure Created:**
```
Nodes:
  - Counterparty (129 columns)
  - Trade (38 columns)
  - Concentration (7 columns)

Edges:
  1. Counterparty → Trade
     Keys: Entity+Counterparty ID = Entity+Reporting Counterparty ID
     Context: default

  2. Counterparty → Concentration
     Keys: Entity+Counterparty Country = Entity+Concentration Value
     Context: "For country level data"

  3. Counterparty → Concentration
     Keys: Entity+Counterparty Sector = Entity+Concentration Value
     Context: "For sector level data"

  4. Counterparty → Concentration
     Keys: Entity+Internal Rating = Entity+Concentration Value
     Context: "For rating level data"
```

### Query Processing Phase

#### Step 1: Table Identification

**Input:**
```
User Query: "What is the concentration by country?"
```

**Process:**
1. Build prompt with:
   - All table schemas (first 15 columns each)
   - User query
   - Context detection rules
   - Instructions for JSON output

2. Send to LLM

3. Parse JSON response

**Output:**
```json
{
  "tables": ["Counterparty", "Concentration"],
  "context": "Country",
  "reasoning": "Need Counterparty for country info and Concentration for concentration data"
}
```

#### Step 2: Join Information Retrieval

**Input:**
```python
tables = ["Counterparty", "Concentration"]
context = "Country"
```

**Process:**

**2A. Find All Tables Needed**
```python
def get_all_tables_needed(tables):
    # Check if direct connection exists
    # If not, find shortest path through graph
    # Returns: ["Counterparty", "Concentration"]
```

**2B. Get Join Relationships**
```python
def get_join_relationships(tables, context):
    relationships = []

    # For each pair of tables
    for Counterparty, Concentration:
        # Check if edge exists
        if graph.has_edge("Counterparty", "Concentration"):
            edges = graph.get_edge_data("Counterparty", "Concentration")

            # edges is a dict with 3 items (3 edges between these tables):
            # {
            #   0: {context: "For country level data", ...},
            #   1: {context: "For sector level data", ...},
            #   2: {context: "For rating level data", ...}
            # }

            # Apply context filtering
            for edge in edges:
                if context == "Country":
                    if "country" in edge['context'].lower():
                        # MATCH! Use this edge
                        relationships.append({
                            "from_table": "Counterparty",
                            "to_table": "Concentration",
                            "join_condition": "Counterparty.Entity = Concentration.Entity AND Counterparty.Counterparty Country = Concentration.Concentration Value",
                            "join_type": "INNER",
                            "context": "For country level data"
                        })

    return relationships
```

**2C. Get Schemas**
```python
def get_columns_for_tables(tables):
    return {
        "Counterparty": [129 columns with descriptions],
        "Concentration": [7 columns with descriptions]
    }
```

**Output:**
```python
join_info = {
    "requested_tables": ["Counterparty", "Concentration"],
    "all_tables_needed": ["Counterparty", "Concentration"],
    "joins": [
        {
            "from_table": "Counterparty",
            "to_table": "Concentration",
            "join_condition": "Counterparty.Entity = Concentration.Entity AND Counterparty.Counterparty Country = Concentration.Concentration Value",
            "join_type": "INNER",
            "context": "For country level data",
            "description": "Join Counterparty with Concentration"
        }
    ],
    "schemas": { ... },
    "context": "Country"
}
```

#### Step 3: SQL Generation

**Input:**
```python
user_query = "What is the concentration by country?"
join_info = { ... }  # From step 2
```

**Process:**
1. Build comprehensive context string:
   ```
   USER QUERY: "..."
   TABLES TO USE: Counterparty, Concentration
   JOIN RELATIONSHIPS:
     Counterparty INNER JOIN Concentration
     ON Counterparty.Entity = Concentration.Entity
        AND Counterparty.Counterparty Country = Concentration.Concentration Value
     *** THIS IS A COMPOSITE JOIN - YOU MUST USE ALL CONDITIONS ***

   TABLE SCHEMAS:
     Counterparty:
       - Entity: ...
       - Counterparty Country: ...
       ...
     Concentration:
       - Entity: ...
       - Concentration Value: ...
       - MPE: ...
       ...

   INSTRUCTIONS:
     1. Use COMPLETE join conditions
     2. Select relevant columns
     3. Add WHERE/GROUP BY as needed
   ```

2. Send to LLM with system instruction emphasizing join completeness

3. Clean up response (remove markdown code blocks)

**Output:**
```sql
SELECT
  c."Counterparty Country",
  SUM(conc.MPE) AS TotalMPE
FROM Counterparty AS c
INNER JOIN Concentration AS conc
  ON c.Entity = conc.Entity
  AND c."Counterparty Country" = conc."Concentration Value"
WHERE conc."Concentration group" = 'Country'
GROUP BY c."Counterparty Country";
```

---

## Code Walkthrough

### Key Classes and Their Roles

#### 1. `TableKnowledgeGraph` (Lines 47-288)

**Purpose:** Manages database schema and relationships as a graph

**Key Methods:**

**`__init__()` and `_build_graph()`:**
```python
def _build_graph(self):
    # Add nodes for tables
    for table_name, columns in self.schemas.items():
        self.graph.add_node(
            table_name,
            columns=[col["name"] for col in columns]
        )

    # Add edges for relationships
    for rel in self.relationships:
        source_cols = rel['join_key_1'].split('+')  # e.g., "Entity+Counterparty ID"
        target_cols = rel['join_key_2'].split('+')

        self.graph.add_edge(
            rel['table1'],
            rel['table2'],
            source_columns=source_cols,
            target_columns=target_cols,
            join_type=rel['join_type'],
            context=rel['context']
        )
```

**`get_join_relationships()` - Most Complex Method:**
```python
def get_join_relationships(self, tables, context=None):
    relationships = []

    # Check all pairs of tables
    for i in range(len(tables)):
        for j in range(i + 1, len(tables)):
            source = tables[i]
            target = tables[j]

            # Check both directions
            for start, end in [(source, target), (target, source)]:
                if self.graph.has_edge(start, end):
                    edges_dict = self.graph.get_edge_data(start, end)

                    # Iterate through all edges (MultiDiGraph can have multiple)
                    for edge_key, edge_data in edges_dict.items():
                        edge_context = edge_data.get('context', 'default')

                        # Context filtering logic
                        if context:
                            # Check if context matches
                            has_context_match = context.lower() in edge_context.lower()
                            is_default = edge_context == 'default'

                            # Check if there are context-specific edges
                            has_context_specific_edges = any(
                                context.lower() in ed.get('context', '').lower()
                                for ed in edges_dict.values()
                                if ed.get('context') != 'default'
                            )

                            # Decision tree:
                            # - If context matches → include
                            # - If default AND no context-specific edges exist → include
                            # - Otherwise → skip
                            if not has_context_match:
                                if not (is_default and not has_context_specific_edges):
                                    continue

                        # Build join condition
                        join_conditions = [
                            f"{start}.{src} = {end}.{tgt}"
                            for src, tgt in zip(
                                edge_data['source_columns'],
                                edge_data['target_columns']
                            )
                        ]

                        relationships.append({
                            "from_table": start,
                            "to_table": end,
                            "join_condition": " AND ".join(join_conditions),
                            "join_type": edge_data['join_type'],
                            "context": edge_context
                        })

    return relationships
```

#### 2. `GeminiClient` (Lines 449-486)

**Purpose:** Interface to Google's Gemini AI

```python
class GeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.model_name = 'gemini-2.0-flash-exp'
        self.generation_config = {
            'temperature': 0.1,      # Low = more deterministic
            'max_output_tokens': 2048
        }

    def call(self, prompt: str, system_instruction: str = None) -> str:
        # Combine system instruction with prompt
        full_prompt = f"{system_instruction}\n\n{prompt}"

        # Call Gemini API
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            config=self.generation_config
        )

        return response.text
```

#### 3. `TextToSQLPipeline` (Lines 501-705)

**Purpose:** Orchestrates the three-step process

**Step 1 - `identify_tables()`:**
```python
def identify_tables(self, user_query: str) -> Dict:
    # Build schema context (all tables with first 15 columns)
    schema_context = "Available tables and their descriptions:\n\n"
    for table_name, columns in self.kg.schemas.items():
        schema_context += f"Table: {table_name}\n"
        for col in columns[:15]:
            schema_context += f"  - {col['name']}: {col['description']}\n"

    # Build prompt with guidelines
    prompt = f"""{schema_context}

    User Query: "{user_query}"

    Guidelines:
    1. If query mentions "concentration", need Counterparty + Concentration
    2. If query mentions "trades", need Counterparty + Trade
    3. Detect context: Country/Rating/Sector

    Return JSON:
    {{
        "tables": ["Counterparty", "Concentration"],
        "context": "Country",
        "reasoning": "..."
    }}
    """

    # Call LLM
    response = self.llm.call(prompt, system_instruction)

    # Parse JSON (with cleanup for markdown)
    result = json.loads(clean_response(response))
    return result
```

**Step 2 - `get_join_info()`:**
```python
def get_join_info(self, tables: List[str], context: Optional[str]) -> Dict:
    # Get all tables (including intermediate ones)
    all_tables = self.kg.get_all_tables_needed(tables)

    # Get join relationships with context filtering
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
```

**Step 3 - `generate_sql()`:**
```python
def generate_sql(self, user_query: str, join_info: Dict) -> str:
    # Build context with ALL information
    context = f"""
    USER QUERY: "{user_query}"

    TABLES TO USE: {', '.join(join_info['all_tables_needed'])}

    JOIN RELATIONSHIPS:
    """

    # Add each join with emphasis on composite joins
    for join in join_info['joins']:
        context += f"\n{join['from_table']} {join['join_type']} JOIN {join['to_table']}"
        context += f"\nON {join['join_condition']}"

        # Emphasize if composite
        if " AND " in join['join_condition']:
            context += f"\n*** COMPOSITE JOIN - USE ALL CONDITIONS ***"

    # Add all schemas
    context += "\n\nTABLE SCHEMAS:\n"
    for table, columns in join_info['schemas'].items():
        context += f"\n{table}:\n"
        for col in columns:
            context += f"  - {col['name']}: {col['description']}\n"

    # Add explicit instructions
    context += """

    INSTRUCTIONS:
    1. Use COMPLETE join conditions - ALL parts
    2. Select relevant columns
    3. Add WHERE/GROUP BY as needed
    4. Use table aliases

    EXAMPLE:
    ON c.Entity = t.Entity AND c."Counterparty ID" = t."Reporting Counterparty ID"
    NOT: ON c.Entity = t.Entity  (WRONG - missing second condition)
    """

    # Call LLM
    sql_query = self.llm.call(context, system_instruction)

    # Clean up
    return clean_sql(sql_query)
```

---

## Example Execution

Let's trace a complete execution with the query: **"Show all trades for counterparties with AAA rating"**

### Initial State
```
Knowledge Graph (already cached):
  Nodes: Counterparty(129 cols), Trade(38 cols), Concentration(7 cols)
  Edges:
    - Counterparty → Trade: Entity+Counterparty ID = Entity+Reporting Counterparty ID
    - Counterparty → Concentration (3 context-specific edges)
```

### Execution Timeline

**T=0ms: User enters query and clicks "Generate SQL"**
```
Input: "Show all trades for counterparties with AAA rating"
```

**T=10ms: Initialize components**
```python
# Reuse cached knowledge graph
kg = build_knowledge_graph(EXCEL_FILE_PATH)  # From cache

# Create new LLM client
llm_client = GeminiClient()

# Create pipeline
pipeline = TextToSQLPipeline(kg, llm_client)
```

**T=20ms: STEP 1 - Call LLM for table identification**
```python
table_info = pipeline.identify_tables(user_query)
```

Prompt sent to Gemini:
```
Available tables and their descriptions:

Table: Counterparty
  - Entity: Entity identifier
  - Counterparty ID: Unique counterparty identifier
  - Internal Rating: Credit rating (AAA, AA, A, BBB, etc.)
  ... (12 more columns)

Table: Trade
  - Trade ID: Unique trade identifier
  - Entity: Entity identifier
  - Reporting Counterparty ID: Counterparty ID for this trade
  ... (12 more columns)

Table: Concentration
  - Entity: Entity identifier
  - Concentration Value: Value being measured
  ... (5 more columns)

User Query: "Show all trades for counterparties with AAA rating"

Guidelines:
1. If query mentions "concentration", need Counterparty + Concentration
2. If query mentions "trades", need Counterparty + Trade
...

Return JSON: {"tables": [...], "context": ..., "reasoning": ...}
```

**T=1500ms: LLM Response received**
```json
{
  "tables": ["Counterparty", "Trade"],
  "context": null,
  "reasoning": "Query asks for trades (Trade table) filtered by counterparty rating (Counterparty table). Need both tables joined."
}
```

**T=1510ms: STEP 2 - Get join information from Knowledge Graph**
```python
join_info = pipeline.get_join_info(
    tables=["Counterparty", "Trade"],
    context=None
)
```

**2A. Find all tables needed:**
```python
all_tables = kg.get_all_tables_needed(["Counterparty", "Trade"])
# Direct edge exists, no intermediate tables needed
# Result: ["Counterparty", "Trade"]
```

**2B. Get join relationships:**
```python
joins = kg.get_join_relationships(
    tables=["Counterparty", "Trade"],
    context=None
)

# Process:
# 1. Check if Counterparty → Trade edge exists: YES
# 2. Get edge data:
#    {
#      0: {
#        source_columns: ['Entity', 'Counterparty ID'],
#        target_columns: ['Entity', 'Reporting Counterparty ID'],
#        join_type: 'INNER',
#        context: 'default'
#      }
#    }
# 3. Context filtering:
#    - No context specified, so include all edges
# 4. Build join condition:
#    "Counterparty.Entity = Trade.Entity AND
#     Counterparty.Counterparty ID = Trade.Reporting Counterparty ID"

# Result:
joins = [
  {
    "from_table": "Counterparty",
    "to_table": "Trade",
    "join_condition": "Counterparty.Entity = Trade.Entity AND Counterparty.Counterparty ID = Trade.Reporting Counterparty ID",
    "join_type": "INNER",
    "context": "default",
    "description": "Join Counterparty with Trade"
  }
]
```

**2C. Get schemas:**
```python
schemas = kg.get_columns_for_tables(["Counterparty", "Trade"])
# Returns full schema for both tables (129 + 38 columns)
```

**Result:**
```python
join_info = {
  "requested_tables": ["Counterparty", "Trade"],
  "all_tables_needed": ["Counterparty", "Trade"],
  "joins": [ ... ],  # 1 join with complete condition
  "schemas": { ... },  # Full schemas
  "context": None
}
```

**T=1520ms: STEP 3 - Call LLM for SQL generation**
```python
sql_query = pipeline.generate_sql(user_query, join_info)
```

Prompt sent to Gemini:
```
Generate a SQL query for the following request.

USER QUERY: "Show all trades for counterparties with AAA rating"

TABLES TO USE: Counterparty, Trade

JOIN RELATIONSHIPS:

Counterparty INNER JOIN Trade
ON Counterparty.Entity = Trade.Entity AND Counterparty.Counterparty ID = Trade.Reporting Counterparty ID
*** THIS IS A COMPOSITE JOIN - YOU MUST USE ALL CONDITIONS: Counterparty.Entity = Trade.Entity AND Counterparty.Counterparty ID = Trade.Reporting Counterparty ID ***
(Join Counterparty with Trade)


TABLE SCHEMAS (with all columns and descriptions):

Counterparty:
  - As Of Date: As of date for the data
  - Entity: Entity identifier
  - Reporting Group: Reporting group name
  - Counterparty ID: Unique counterparty identifier
  - Counterparty Name: Name of the counterparty
  - Internal Rating: Credit rating assigned internally
  ... (123 more columns)

Trade:
  - As Of Date: As of date for the data
  - Trade ID: Unique trade identifier
  - Entity: Entity identifier
  - Legal Entity: Legal entity name
  - Reporting Counterparty ID: Counterparty ID for this trade
  ... (33 more columns)

INSTRUCTIONS FOR SQL GENERATION:

1. JOIN CONDITIONS - ABSOLUTELY CRITICAL:
   - Copy the EXACT join condition from above into your ON clause
   - If you see " AND " in the join condition, that means MULTIPLE conditions - use ALL of them
   - DO NOT simplify or omit any part of the join condition

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

Return ONLY the SQL query without any explanations, markdown formatting, or code blocks.
```

**T=3000ms: LLM Response received**
```sql
SELECT
  t.*
FROM Counterparty AS c
INNER JOIN Trade AS t
  ON c.Entity = t.Entity
  AND c."Counterparty ID" = t."Reporting Counterparty ID"
WHERE
  c."Internal Rating" = 'AAA';
```

**T=3010ms: Clean up response**
```python
# Remove markdown code blocks if present
sql_query = sql_query.strip()
if sql_query.startswith('```sql'):
    sql_query = sql_query[6:]
if sql_query.endswith('```'):
    sql_query = sql_query[:-3]
sql_query = sql_query.strip()
```

**T=3020ms: Display results to user**
```python
st.success("✅ SQL query generated successfully!")
st.code(result['sql_query'], language='sql')
st.download_button("📥 Download SQL", ...)

# Show details in expander
with st.expander("🔍 View Processing Details"):
    st.json(result['table_info'])
    st.write("Join Details:")
    for join in result['join_info']['joins']:
        st.code(join['join_condition'])
```

### Final Output Displayed

```sql
SELECT
  t.*
FROM Counterparty AS c
INNER JOIN Trade AS t
  ON c.Entity = t.Entity
  AND c."Counterparty ID" = t."Reporting Counterparty ID"
WHERE
  c."Internal Rating" = 'AAA';
```

**Processing Details:**
- Tables identified: Counterparty, Trade
- Context: None
- Joins found: 1
- Join condition: Complete (both Entity AND Counterparty ID)

---

## Key Design Decisions

### 1. **Why MultiDiGraph?**
Regular graphs allow only ONE edge between two nodes. MultiDiGraph allows MULTIPLE edges, which is essential because:
- Counterparty → Concentration has 3 different edges (country, sector, rating contexts)
- Each edge represents a different way to join the same two tables

### 2. **Why Two LLM Calls?**
Separation of concerns:
- **Call 1**: High-level reasoning (which tables are needed?)
- **Call 2**: Technical generation (create syntactically correct SQL)

This approach:
- Reduces hallucination (each task is simpler)
- Allows debugging (can inspect intermediate results)
- Enables caching (table identification could be cached in future)

### 3. **Why Context Filtering?**
Same table pair can have different join conditions based on analysis type:
- Country analysis: Join on Counterparty Country
- Sector analysis: Join on Counterparty Sector
- Rating analysis: Join on Internal Rating

Context filtering selects the right join for the query.

### 4. **Why Cache Knowledge Graph?**
Building the graph is expensive:
- Read Excel file (~1-2 seconds)
- Parse relationships
- Build NetworkX graph

Caching reduces query time from ~5 seconds to ~2 seconds.

### 5. **Why Emphasize Composite Joins?**
LLMs sometimes simplify:
- See: `Entity = Entity AND ID = ID`
- Generate: `Entity = Entity` (omitting second condition)

The emphasis forces the LLM to include all conditions.

---

## Performance Characteristics

### Cold Start (First Query)
```
Excel Load:        ~1000ms (cached after first load)
Graph Build:       ~100ms (cached after first build)
LLM Call 1:        ~1500ms (table identification)
Graph Query:       ~10ms
LLM Call 2:        ~1500ms (SQL generation)
Total:             ~4100ms
```

### Warm Query (Subsequent Queries)
```
Excel Load:        ~0ms (from cache)
Graph Build:       ~0ms (from cache)
LLM Call 1:        ~1500ms
Graph Query:       ~10ms
LLM Call 2:        ~1500ms
Total:             ~3010ms
```

### Bottlenecks
1. **LLM Calls**: ~75% of total time
2. **Excel Loading**: ~25% (first query only)
3. **Graph Operations**: <1%

---

## Error Handling

### 1. Excel File Not Found
```python
try:
    df = pd.read_excel(file_path, sheet_name="Counterparty New")
except FileNotFoundError:
    st.error("Excel file not found!")
    return None, None
```

### 2. Invalid JSON from LLM
```python
try:
    result = json.loads(response)
except json.JSONDecodeError:
    # Try to extract JSON from text
    start = response.find('{')
    end = response.rfind('}') + 1
    json_str = response[start:end]
    result = json.loads(json_str)
```

### 3. No Join Path Found
```python
try:
    path = nx.shortest_path(graph, table1, table2)
except nx.NetworkXNoPath:
    # Tables not connected - will return empty joins list
    pass
```

### 4. API Key Missing
```python
if not GOOGLE_API_KEY:
    st.error("Google API key not found!")
    st.info("Please add GOOGLE_API_KEY to your .env file")
    return
```

---

## Future Enhancements

### 1. Query Result Execution
Currently generates SQL only. Could add:
```python
def execute_query(sql_query: str, connection_string: str):
    conn = create_connection(connection_string)
    df = pd.read_sql(sql_query, conn)
    return df
```

### 2. Query History
```python
@st.cache_data
def save_query_history(query: str, sql: str):
    history = load_history()
    history.append({
        "timestamp": datetime.now(),
        "query": query,
        "sql": sql
    })
    save_history(history)
```

### 3. Query Optimization
```python
def optimize_sql(sql_query: str) -> str:
    # Analyze query plan
    # Suggest indexes
    # Rewrite for performance
    return optimized_sql
```

### 4. Multi-Database Support
```python
class DatabaseConfig:
    def __init__(self, db_type: str):
        self.db_type = db_type  # 'postgres', 'mysql', 'mssql'
        self.dialect = get_dialect(db_type)

    def generate_sql(self, query_plan):
        # Generate database-specific SQL
        return dialect_specific_sql
```

---

## Conclusion

This application demonstrates a sophisticated AI-powered query generation system that:

1. **Understands natural language** using state-of-the-art LLMs
2. **Manages complex schemas** with a graph-based approach
3. **Handles context-specific logic** for different analysis scenarios
4. **Generates accurate SQL** with complete join conditions
5. **Provides transparency** through detailed processing information
6. **Optimizes performance** through strategic caching

The three-step pipeline (Identify → Query → Generate) provides a clear separation of concerns and makes the system maintainable and extensible.
