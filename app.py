from flask import Flask, render_template, jsonify, g
from neo4j import GraphDatabase
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app instance
app = Flask(__name__)

# Neo4j Configuration
URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
AUTH = ("neo4j", "Poconoco16!")

# Initialize Neo4j driver
try:
    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
    logger.info("Connected to Neo4j successfully!")
except Exception as e:
    logger.error(f"Failed to connect to Neo4j: {str(e)}")
    driver = None

def get_nodes_by_type(tx, node_type):
    try:
        query = f'''
        MATCH (n:{node_type})-[r]-(m)
        RETURN n, r, m
        '''
        result = tx.run(query)
        records = [dict(record) for record in result]
        logger.info(f"Retrieved {len(records)} records for node type: {node_type}")
        return records
    except Exception as e:
        logger.error(f"Query error in get_nodes_by_type: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/nodes/<node_type>')
def get_nodes(node_type):
    if not driver:
        logger.error("No database connection available")
        return jsonify({'success': False, 'error': 'Database connection not available'}), 503
    
    try:
        with driver.session() as session:
            nodes = session.read_transaction(get_nodes_by_type, node_type)
            return jsonify({'success': True, 'data': nodes})
    except Exception as e:
        logger.error(f"Error in get_nodes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/node-types')
def get_node_types():
    node_types = [
        'nerve', 'bone', 'neuro', 'region', 'viscera', 'muscle', 'sense',
        'vein', 'artery', 'cv', 'function', 'sensory', 'gland', 'lymph',
        'head', 'organ', 'sensation', 'skin'
    ]
    return jsonify({'success': True, 'node_types': node_types})

@app.route('/api/graph')
def get_full_graph():
    if not driver:
        logger.error("No database connection available")
        return jsonify({'success': False, 'error': 'Database connection not available'}), 503
    
    try:
        with driver.session() as session:
            query = '''
            MATCH (n)-[r]-(m)
            RETURN n, r, m
            '''
            result = session.run(query)
            nodes = [dict(record) for record in result]
            logger.info(f"Retrieved {len(nodes)} records for full graph")
            return jsonify({'success': True, 'data': nodes})
    except Exception as e:
        logger.error(f"Error in get_full_graph: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handling
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Cleanup
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j_driver'):
        g.neo4j_driver.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
