# app.py
from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Neo4j connection details
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(username, password))

def get_graph_data():
    with driver.session() as session:
        # Get all nodes with their properties
        nodes_query = """
        MATCH (n)
        RETURN 
            id(n) as id, 
            labels(n) as labels, 
            properties(n) as properties,
            COALESCE(n.name, '') as name
        """
        
        # Get all relationships
        rels_query = """
        MATCH (a)-[r]->(b)
        RETURN 
            id(r) as id, 
            id(a) as source, 
            id(b) as target, 
            type(r) as type, 
            properties(r) as properties
        """
        
        nodes = []
        for record in session.run(nodes_query):
            node = {
                'id': record['id'],
                'label': record['name'],  # Use name as label
                'labels': record['labels'],
                'properties': record['properties']
            }
            nodes.append(node)
        
        edges = []
        for record in session.run(rels_query):
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
        return jsonify(get_graph_data())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search():
    search_term = request.args.get('term', '').lower()
    if not search_term:
        return jsonify([])
    
    with driver.session() as session:
        # Search nodes by name and properties
        query = """
        MATCH (n)
        WHERE toLower(toString(n.name)) CONTAINS $term 
           OR ANY(prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS $term)
        RETURN DISTINCT id(n) as id, n.name as name, properties(n) as properties
        LIMIT 10
        """
        
        result = session.run(query, term=search_term)
        matches = [{"id": record["id"], 
                   "name": record["name"],
                   "properties": record["properties"]} 
                  for record in result]
        return jsonify(matches)

@app.route('/api/locations')
def get_locations():
    with driver.session() as session:
        query = """
        MATCH (n)
        WHERE exists(n.location)
        RETURN DISTINCT n.location AS location
        ORDER BY location
        """
        result = session.run(query)
        locations = [record["location"] for record in result]
        return jsonify(locations)

@app.route('/api/sublocations')
def get_sublocations():
    with driver.session() as session:
        query = """
        MATCH (n)
        WHERE exists(n.sublocation)
        RETURN DISTINCT n.sublocation AS sublocation
        ORDER BY sublocation
        """
        result = session.run(query)
        sublocations = [record["sublocation"] for record in result]
        return jsonify(sublocations)

if __name__ == '__main__':
    app.run(debug=True)
