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

def get_graph_data():
    with driver.session() as session:
        # Get nodes
        nodes_result = session.run('''
            MATCH (n)
            RETURN 
                id(n) as id, 
                labels(n) as labels, 
                properties(n) as properties,
                CASE
                    WHEN n.name IS NOT NULL THEN n.name
                    WHEN n.title IS NOT NULL THEN n.title
                    ELSE toString(id(n))
                END as name
        ''')
        
        nodes = []
        for record in nodes_result:
            # Determine node type based on labels
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

        # Get relationships
        edges_result = session.run('''
            MATCH ()-[r]->()
            RETURN 
                id(r) as id,
                id(startNode(r)) as from,
                id(endNode(r)) as to,
                type(r) as type,
                properties(r) as properties
        ''')
        
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
        # Search in node properties and labels
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
            # Determine node type based on labels
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
        
        return nodes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/graph')
def get_graph():
    try:
        data = get_graph_data()
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

@app.route('/api/filter')
def filter_nodes():
    node_type = request.args.get('type', '')
    try:
        data = get_graph_data()
        if node_type and node_type != 'all':
            data['nodes'] = [node for node in data['nodes'] if node['type'] == node_type]
            # Filter edges to only include connections between visible nodes
            visible_node_ids = {node['id'] for node in data['nodes']}
            data['edges'] = [edge for edge in data['edges'] 
                           if edge['from'] in visible_node_ids 
                           and edge['to'] in visible_node_ids]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
