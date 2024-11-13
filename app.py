from flask import Flask, render_template, jsonify
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import logging

load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j connection configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

def get_neo4j_driver():
    return driver

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    config = {
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_USER": NEO4J_USER,
        "NEO4J_PASSWORD": NEO4J_PASSWORD
    }
    return jsonify(config)

@app.route('/api/nodes/random')
def get_random_nodes():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WITH n, rand() as random
                ORDER BY random
                LIMIT 100
                MATCH (n)-[rel]-(m)
                RETURN DISTINCT n, rel, m
                LIMIT 100
            ''')
            nodes = []
            for record in result:
                node = record['n']
                related_node = record['m']
                relationship = record['rel']
                nodes.append({
                    'n': {
                        'id': node.id,
                        'labels': list(node.labels),
                        'properties': dict(node)
                    },
                    'm': {
                        'id': related_node.id,
                        'labels': list(related_node.labels),
                        'properties': dict(related_node)
                    },
                    'rel': {
                        'type': relationship.type
                    }
                })
            logger.info(f"Fetched nodes: {nodes}")
            return jsonify(nodes)
    except Exception as e:
        logger.error(f"Error fetching random nodes: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/api/neo4j/status')
def neo4j_status():
    try:
        with get_neo4j_driver().session() as session:
            session.run("RETURN 1")
        return jsonify({"status": "connected"})
    except Exception as e:
        logger.error(f"Neo4j connection error: {e}")
        return jsonify({"status": "disconnected"}), 500

if __name__ == "__main__":
    app.run(debug=True)
