import os
from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Neo4j connection details
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

# Initialize Neo4j driver
driver = GraphDatabase.driver(uri, auth=(username, password))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/graph')
def get_graph():
    try:
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
                node_types = [label.lower() for label in record["labels"]]
                node_type = next((t for t in [
                    'nerve', 'bone', 'neuro', 'region', 'viscera', 'muscle', 
                    'sense', 'vein', 'artery', 'cv', 'function', 'sensory',
                    'gland', 'lymph', 'head', 'organ', 'sensation', 'skin'
                ] if t in node_types), 'other')
                
                nodes.append({
                    "id": record["id"],
                    "label": record["name"],
                    "type": node_type
                })

            # Get relationships
            edges_result = session.run('''
                MATCH ()-[r]->()
                RETURN 
                    id(r) as id,
                    id(startNode(r)) as from,
                    id(endNode(r)) as to,
                    type(r) as type
            ''')
            
            edges = []
            for record in edges_result:
                edges.append({
                    "id": record["id"],
                    "from": record["from"],
                    "to": record["to"],
                    "type": record["type"]
                })

            return jsonify({"nodes": nodes, "edges": edges})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/filter')
def filter_nodes():
    node_type = request.args.get('type', '')
    
    try:
        with driver.session() as session:
            # Get filtered nodes
            query = '''
                MATCH (n)
                WHERE $node_type = '' OR any(label IN labels(n) WHERE toLower(label) = $node_type)
                RETURN 
                    id(n) as id, 
                    labels(n) as labels,
                    CASE
                        WHEN n.name IS NOT NULL THEN n.name
                        WHEN n.title IS NOT NULL THEN n.title
                        ELSE toString(id(n))
                    END as name
            '''
            
            nodes_result = session.run(query, node_type=node_type.lower())
            
            nodes = []
            node_ids = set()
            for record in nodes_result:
                node_ids.add(record["id"])
                nodes.append({
                    "id": record["id"],
                    "label": record["name"],
                    "type": node_type if node_type else 'other'
                })

            # Get relationships between filtered nodes
            edges_result = session.run('''
                MATCH (n1)-[r]->(n2)
                WHERE id(n1) IN $node_ids AND id(n2) IN $node_ids
                RETURN 
                    id(r) as id,
                    id(n1) as from,
                    id(n2) as to,
                    type(r) as type
            ''', node_ids=list(node_ids))
            
            edges = []
            for record in edges_result:
                edges.append({
                    "id": record["id"],
                    "from": record["from"],
                    "to": record["to"],
                    "type": record["type"]
                })

            return jsonify({"nodes": nodes, "edges": edges})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
