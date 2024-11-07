# app.py
from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Neo4j connection details from environment variables
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(username, password))

def get_graph_data():
    with driver.session() as session:
        # Query to get nodes and their properties
        nodes_query = """
        MATCH (n)
        RETURN id(n) as id, labels(n) as labels, properties(n) as properties
        """
        
        # Query to get relationships
        rels_query = """
        MATCH (a)-[r]->(b)
        RETURN id(r) as id, id(a) as source, id(b) as target, type(r) as type, properties(r) as properties
        """
        
        # Execute queries
        nodes_result = session.run(nodes_query)
        rels_result = session.run(rels_query)
        
        # Process nodes
        nodes = []
        for record in nodes_result:
            node = {
                'id': record['id'],
                'label': record['properties'].get('name', ''),  # Use name as label if exists
                'labels': record['labels'],
                'properties': record['properties']
            }
            nodes.append(node)
        
        # Process relationships
        edges = []
        for record in rels_result:
            edge = {
                'id': record['id'],
                'from': record['source'],
                'to': record['target'],
                'type': record['type'],
                'properties': record['properties']
            }
            edges.append(edge)
        
        return {'nodes': nodes, 'edges': edges}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/graph')
def get_graph():
    try:
        graph_data = get_graph_data()
        return jsonify(graph_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search():
    search_term = request.args.get('term', '').lower()
    if len(search_term) < 2:
        return jsonify([])
    
    with driver.session() as session:
        query = """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS $search_term 
        OR ANY(prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS $search_term)
        RETURN id(n) as id, labels(n) as labels, properties(n) as properties
        LIMIT 10
        """
        result = session.run(query, search_term=search_term)
        nodes = []
        for record in result:
            nodes.append({
                'id': record['id'],
                'label': record['properties'].get('name', ''),
                'labels': record['labels'],
                'properties': record['properties']
            })
        return jsonify(nodes)

@app.route('/api/node_types')
def get_node_types():
    with driver.session() as session:
        query = "CALL db.labels()"
        result = session.run(query)
        types = [record['label'] for record in result]
        return jsonify(types)

@app.route('/api/locations')
def get_locations():
    with driver.session() as session:
        query = """
        MATCH (n)
        WHERE exists(n.location)
        RETURN DISTINCT n.location as location
        ORDER BY location
        """
        result = session.run(query)
        locations = [record['location'] for record in result]
        return jsonify(locations)

@app.route('/api/sublocations')
def get_sublocations():
    with driver.session() as session:
        query = """
        MATCH (n)
        WHERE exists(n.sublocation)
        RETURN DISTINCT n.sublocation as sublocation
        ORDER BY sublocation
        """
        result = session.run(query)
        sublocations = [record['sublocation'] for record in result]
        return jsonify(sublocations)

@app.route('/api/relationship_types')
def get_relationship_types():
    with driver.session() as session:
        query = "CALL db.relationshipTypes()"
        result = session.run(query)
        types = [record['relationshipType'] for record in result]
        return jsonify(types)

if __name__ == '__main__':
    app.run(debug=True)
