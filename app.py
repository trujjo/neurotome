from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Neo4j connection details
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

# Initialize Neo4j driver
driver = GraphDatabase.driver(uri, auth=(username, password))

def get_metadata():
    with driver.session() as session:
        # Get unique locations
        locations = session.run('''
            MATCH (n)
            WHERE exists(n.location)
            RETURN DISTINCT n.location AS location
            ORDER BY location
        ''').values()
        
        # Get unique sublocations
        sublocations = session.run('''
            MATCH (n)
            WHERE exists(n.sublocation)
            RETURN DISTINCT n.sublocation AS sublocation
            ORDER BY sublocation
        ''').values()
        
        # Get relationship types
        relationships = session.run('''
            MATCH ()-[r]->()
            RETURN DISTINCT type(r) AS relationship
            ORDER BY relationship
        ''').values()
        
        return {
            "locations": [loc[0] for loc in locations if loc[0]],
            "sublocations": [subloc[0] for subloc in sublocations if subloc[0]],
            "relationships": [rel[0] for rel in relationships if rel[0]]
        }

def get_filtered_graph_data(location=None, sublocation=None, relationship_types=None):
    with driver.session() as session:
        # Build the node matching clause based on filters
        node_filters = []
        if location:
            node_filters.append("n.location = $location")
        if sublocation:
            node_filters.append("n.sublocation = $sublocation")
        
        node_where_clause = " AND ".join(node_filters) if node_filters else "true"
        
        # Get nodes with filters
        nodes_query = f'''
            MATCH (n)
            WHERE {node_where_clause}
            RETURN 
                id(n) as id, 
                labels(n) as labels, 
                properties(n) as properties,
                CASE
                    WHEN n.name IS NOT NULL THEN n.name
                    WHEN n.title IS NOT NULL THEN n.title
                    ELSE toString(id(n))
                END as name
        '''
        
        nodes_result = session.run(
            nodes_query,
            location=location,
            sublocation=sublocation
        )
        
        nodes = []
        node_ids = set()  # Keep track of node IDs for filtering edges
        
        for record in nodes_result:
            node_type = "hidden"  # default type
            if any(label.lower() == "input" for label in record["labels"]):
                node_type = "input"
            elif any(label.lower() == "output" for label in record["labels"]):
                node_type = "output"
            
            nodes.append({
                "id": record["id"],
                "label": record["name"],
                "labels": record["labels"],
                "properties": record["properties"],
                "type": node_type
            })
            node_ids.add(record["id"])
        
        # Build relationship type filter
        rel_type_filter = ""
        if relationship_types:
            rel_types = [f"type(r) = '{r}'" for r in relationship_types]
            rel_type_filter = f"AND ({' OR '.join(rel_types)})"
        
        # Get relationships between filtered nodes
        edges_query = f'''
            MATCH (start)-[r]->(end)
            WHERE id(start) IN $node_ids 
            AND id(end) IN $node_ids
            {rel_type_filter}
            RETURN 
                id(r) as id,
                id(start) as from,
                id(end) as to,
                type(r) as type,
                properties(r) as properties
        '''
        
        edges_result = session.run(edges_query, node_ids=list(node_ids))
        
        edges = []
        for record in edges_result:
            edges.append({
                "id": record["id"],
                "from": record["from"],
                "to": record["to"],
                "type": record["type"],
                "properties": record["properties"]
            })

        return {"nodes": nodes, "edges": edges}

def search_nodes(search_term):
    with driver.session() as session:
        result = session.run('''
            MATCH (n)
            WHERE any(label IN labels(n) WHERE toLower(label) CONTAINS toLower($term))
            OR any(key IN keys(n) WHERE toLower(toString(n[key])) CONTAINS toLower($term))
            RETURN 
                id(n) as id,
                labels(n) as labels,
                properties(n) as properties,
                CASE
                    WHEN n.name IS NOT NULL THEN n.name
                    WHEN n.title IS NOT NULL THEN n.title
                    ELSE toString(id(n))
                END as name
            LIMIT 10
        ''', term=search_term)
        
        nodes = []
        for record in result:
            node_type = "hidden"
            if any(label.lower() == "input" for label in record["labels"]):
                node_type = "input"
            elif any(label.lower() == "output" for label in record["labels"]):
                node_type = "output"
            
            nodes.append({
                "id": record["id"],
                "label": record["name"],
                "labels": record["labels"],
                "properties": record["properties"],
                "type": node_type
            })
        
        return nodes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metadata')
def get_meta():
    try:
        return jsonify(get_metadata())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/graph')
def get_graph():
    try:
        # Get filter parameters
        location = request.args.get('location')
        sublocation = request.args.get('sublocation')
        relationship_types = request.args.getlist('relationships[]')
        
        data = get_filtered_graph_data(
            location=location,
            sublocation=sublocation,
            relationship_types=relationship_types if relationship_types else None
        )
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search')
def search():
    search_term = request.args.get('term', '')
    if not search_term:
        return jsonify([])
    
    try:
        results = search_nodes(search_term)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
