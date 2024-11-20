from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Neo4j connection configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_neo4j_driver():
    return driver

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/nodes/random')
def get_random_nodes():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WITH n, rand() as random
                ORDER BY random
                LIMIT 25
                RETURN n
            ''')
            nodes = []
            for record in result:
                node = record['n']
                nodes.append({
                    'id': node.id,
                    'labels': list(node.labels),
                    'properties': dict(node)
                })
            return jsonify(nodes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/neo4j/status')
def neo4j_status():
    try:
        with get_neo4j_driver().session() as session:
            session.run("RETURN 1")
        return jsonify({"status": "connected"})
    except Exception as e:
        return jsonify({"status": "disconnected"}), 500

if __name__ == "__main__":
    app.run(debug=True)