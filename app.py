from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))

def get_graph_data():
    with driver.session() as session:
        # Query to get nodes with their properties and labels
        nodes_query = """
        MATCH (n)
        RETURN 
            id(n) as id, 
            labels(n) as labels, 
            properties(n) as properties,
            CASE
                WHEN exists(n.x) THEN n.x
                ELSE 0
            END as x,
            CASE
                WHEN exists(n.y) THEN n.y
                ELSE 0
            END as y
        """
        
        # Query to get relationships
        rels_query = """
        MATCH (a)-[r]->(b)
        RETURN id(a) as source, id(b) as target, type(r) as type
        """
        
        # Execute queries
        nodes_result = session.run(nodes_query)
        rels_result = session.run(rels_query)
        
        # Process nodes
        nodes = []
        for record in nodes_result:
            node = {
                "id": record["id"],
                "labels": record["labels"],
                "properties": record["properties"],
                "x": record["x"],
                "y": record["y"]
            }
            nodes.append(node)
        
        # Process relationships
        relationships = []
        for record in rels_result:
            rel = {
                "source": record["source"],
                "target": record["target"],
                "type": record["type"]
            }
            relationships.append(rel)
        
        # Get unique node types, locations, and sublocations
        node_types = list(set([label for node in nodes for label in node["labels"]]))
        locations = list(set([node["properties"].get("location", "") for node in nodes if "location" in node["properties"]]))
        sublocations = list(set([node["properties"].get("sublocation", "") for node in nodes if "sublocation" in node["properties"]]))
        
        return {
            "nodes": nodes,
            "relationships": relationships,
            "nodeTypes": node_types,
            "locations": locations,
            "sublocations": sublocations
        }

@app.route('/')
def index():
    return render_template('visualization.html')

@app.route('/graph')
def get_graph():
    try:
        data = get_graph_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    
    with driver.session() as session:
        # Search query
        search_query = """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS $query
        OR toLower(n.description) CONTAINS $query
        WITH n
        OPTIONAL MATCH (n)-[r]-(m)
        RETURN 
            collect(distinct {
                id: id(n),
                labels: labels(n),
                properties: properties(n),
                x: CASE WHEN exists(n.x) THEN n.x ELSE 0 END,
                y: CASE WHEN exists(n.y) THEN n.y ELSE 0 END
            }) as nodes,
            collect(distinct {
                source: id(startNode(r)),
                target: id(endNode(r)),
                type: type(r)
            }) as relationships
        """
        
        result = session.run(search_query, query=query)
        record = result.single()
        
        if record:
            return jsonify({
                "nodes": record["nodes"],
                "relationships": record["relationships"]
            })
        return jsonify({"nodes": [], "relationships": []})

if __name__ == '__main__':
    app.run(debug=True)
