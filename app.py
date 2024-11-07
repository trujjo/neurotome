from flask import Flask, render_template, jsonify
from neo4j import GraphDatabase
import os
from contextlib import contextmanager

app = Flask(__name__)

# Configuration
URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
AUTH = ("neo4j", "Poconoco16!")

# Predefined node types
NODE_TYPES = [
    'nerve', 'bone', 'neuro', 'region', 'viscera', 'muscle', 'sense',
    'vein', 'artery', 'cv', 'function', 'sensory', 'gland', 'lymph',
    'head', 'organ', 'sensation', 'skin'
]

@contextmanager
def get_db_connection():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        yield driver
    finally:
        driver.close()

@app.route('/')
def index():
    """Main visualization page with node type buttons"""
    return render_template('visualization.html', node_types=NODE_TYPES)

@app.route('/nodes/<node_type>')
def get_nodes_by_type(node_type):
    """API endpoint to fetch nodes by type with their coordinates"""
    try:
        with get_db_connection() as driver:
            with driver.session() as session:
                query = """
                MATCH (n:%s)
                RETURN n.name as name, 
                       n.x as x, 
                       n.y as y, 
                       n.z as z,
                       labels(n) as labels,
                       properties(n) as properties
                """ % node_type
                
                result = session.run(query)
                nodes = [dict(record) for record in result]
                return jsonify(nodes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/graph/labels')
def get_available_labels():
    """API endpoint to fetch all available labels in the database"""
    try:
        with get_db_connection() as driver:
            with driver.session() as session:
                # Using the built-in Neo4j procedure to get all labels
                query = "CALL db.labels()"
                result = session.run(query)
                labels = [record["label"] for record in result]
                return jsonify(labels)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
