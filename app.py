from flask import Flask, render_template, jsonify
from neo4j import GraphDatabase
import os
from contextlib import contextmanager

app = Flask(__name__)

# Configuration
URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
AUTH = ("neo4j", "Poconoco16!")

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
    return render_template('visualization.html', node_types=NODE_TYPES)

@app.route('/nodes/<node_type>')
def get_nodes_by_type(node_type):
    try:
        with get_db_connection() as driver:
            with driver.session() as session:
                # Enhanced query to get nodes with their relationships
                query = """
                MATCH (n:%s)
                OPTIONAL MATCH (n)-[r]-(m)
                RETURN DISTINCT n, 
                       collect(DISTINCT {
                           relationship: type(r),
                           node: m
                       }) as connections
                """ % node_type
                
                result = session.run(query)
                nodes_data = []
                for record in result:
                    node = record['n']
                    connections = record['connections']
                    nodes_data.append({
                        'id': node.id,
                        'properties': dict(node),
                        'connections': [
                            {
                                'type': conn['relationship'],
                                'connected_node': dict(conn['node'])
                            } for conn in connections if conn['node'] is not None
                        ]
                    })
                return jsonify(nodes_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/graph/relationships/<node_type>')
def get_relationships(node_type):
    try:
        with get_db_connection() as driver:
            with driver.session() as session:
                query = """
                MATCH (n:%s)-[r]-(m)
                RETURN DISTINCT type(r) as relationship_type,
                       count(r) as count
                """ % node_type
                
                result = session.run(query)
                relationships = [dict(record) for record in result]
                return jsonify(relationships)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
