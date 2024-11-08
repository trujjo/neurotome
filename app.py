from flask import Flask, jsonify, request, render_template
from neo4j import GraphDatabase
import os

app = Flask(__name__)

# Neo4j connection settings - using the repository variables directly
uri = "neo4j+s://4e5eeae5.databases.neo4j.io"
user = "neo4j"
password = "Poconoco16!"

# Create the driver
driver = GraphDatabase.driver(uri, auth=(user, password))

@app.route('/')
def index():
    return render_template('visualization.html')

@app.route('/graph')
def get_graph():
    try:
        with driver.session() as session:
            # Updated query to include x, y coordinates
            result = session.run("""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]-(m)
                RETURN collect(distinct {
                    id: id(n), 
                    labels: labels(n), 
                    properties: properties(n),
                    x: n.x,
                    y: n.y
                }) as nodes, 
                collect(distinct r) as relationships
            """)
            
            data = result.single()
            nodes = [{
                "id": node["id"], 
                "labels": node["labels"], 
                "properties": node["properties"],
                "x": node["x"],
                "y": node["y"]
            } for node in data["nodes"]]
            
            rels = [{"source": rel.start_node.id, "target": rel.end_node.id, 
                    "type": rel.type} for rel in data["relationships"]]
            
            return jsonify({"nodes": nodes, "relationships": rels})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    if len(query) < 3:
        return jsonify({'nodes': [], 'relationships': []})

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE toLower(n.name) CONTAINS $query 
                   OR any(label IN labels(n) WHERE toLower(label) CONTAINS $query)
                WITH n
                OPTIONAL MATCH (n)-[r]-(m)
                RETURN collect(distinct {
                    id: id(n), 
                    labels: labels(n), 
                    properties: properties(n),
                    x: n.x,
                    y: n.y
                }) as nodes, 
                collect(distinct r) as relationships
            """, query=query)
            
            data = result.single()
            nodes = [{
                "id": node["id"], 
                "labels": node["labels"], 
                "properties": node["properties"],
                "x": node["x"],
                "y": node["y"]
            } for node in data["nodes"]]
            
            rels = [{"source": rel.start_node.id, "target": rel.end_node.id, 
                    "type": rel.type} for rel in data["relationships"]]
            
            return jsonify({"nodes": nodes, "relationships": rels})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
