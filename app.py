# Create the app.py file with direct Flask code
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
                END as name,
                CASE
                    WHEN n.location IS NOT NULL THEN n.location
                    ELSE ''
                END as location,
                CASE
                    WHEN n.sublocation IS NOT NULL THEN n.sublocation
                    ELSE ''
                END as sublocation
        ''')
        
        nodes = []
        for record in nodes_result:
            # Get node type from labels
            node_types = [label.lower() for label in record["labels"]]
            node_type = next((t for t in [
                'nerve', 'bone', 'neuro', 'region', 'viscera', 'muscle', 
                'sense', 'vein', 'artery', 'cv', 'function', 'sensory',
                'gland', 'lymph', 'head', 'organ', 'sensation', 'skin'
            ] if t in node_types), 'other')
            
            nodes.append({
                "id": record["id"],
                "label": record["name"],
                "labels": record["labels"],
                "properties": record["properties"],
                "type": node_type,
                "location": record["location"],
                "sublocation": record["sublocation"]
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

def get_locations():
    with driver.session() as session:
        result = session.run('''
            MATCH (n)
            WHERE n.location IS NOT NULL
            RETURN DISTINCT n.location as location, 
                   collect(DISTINCT n.sublocation) as sublocations
            ORDER BY location
        ''')
        locations = {}
        for record in result:
            locations[record["location"]] = sorted([s for s in record["sublocations"] if s])
        return locations

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

@app.route('/api/locations')
def locations():
    try:
        data = get_locations()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/filter')
def filter_nodes():
    node_type = request.args.get('type', '')
    location = request.args.get('location', '')
    sublocation = request.args.get('sublocation', '')
    
    try:
        data = get_graph_data()
        
        if node_type and node_type != 'all':
            data['nodes'] = [node for node in data['nodes'] if node['type'] == node_type]
        
        if location:
            data['nodes'] = [node for node in data['nodes'] 
                           if node.get('location') == location]
        
        if sublocation:
            data['nodes'] = [node for node in data['nodes'] 
                           if node.get('sublocation') == sublocation]
        
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

# Write the Flask application code directly to app.py
with open('app.py', 'w') as f:
    f.write(flask_app_content)

print("Created new app.py with direct Flask code")
