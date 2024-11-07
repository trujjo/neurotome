from flask import Flask, render_template, jsonify, g
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, DatabaseError
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app instance
app = Flask(__name__)

# Neo4j Configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j+s://4e5eeae5.databases.neo4j.io:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Poconoco16!')

# Initialize Neo4j driver with retry logic
def init_driver(max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_timeout=60
            )
            # Verify connectivity
            driver.verify_connectivity()
            return driver
        except ServiceUnavailable as e:
            if attempt == max_retries - 1:
                print(f"Failed to connect to Neo4j after {max_retries} attempts: {str(e)}")
                raise
            print(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

# Initialize driver
try:
    driver = init_driver()
except Exception as e:
    print(f"Failed to initialize Neo4j driver: {str(e)}")
    raise

def get_nodes_by_type(tx, node_type):
    try:
        query = f'''
        MATCH (n:{node_type})-[r]-(m)
        RETURN n, r, m
        '''
        result = tx.run(query)
        return [dict(record) for record in result]
    except (ServiceUnavailable, DatabaseError) as e:
        print(f"Database error in get_nodes_by_type: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/nodes/<node_type>')
def get_nodes(node_type):
    try:
        with driver.session(connection_timeout=60) as session:
            nodes = session.read_transaction(get_nodes_by_type, node_type)
            return jsonify({'success': True, 'data': nodes})
    except Exception as e:
        print(f"Error in get_nodes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/node-types')
def get_node_types():
    node_types = [
        'nerve',
        'bone',
        'neuro',
        'region',
        'viscera',
        'muscle',
        'sense',
        'vein',
        'artery',
        'cv',
        'function',
        'sensory',
        'gland',
        'lymph',
        'head',
        'organ',
        'sensation',
        'skin'
    ]
    return jsonify({'success': True, 'node_types': node_types})

@app.route('/api/graph')
def get_full_graph():
    try:
        with driver.session(connection_timeout=60) as session:
            query = '''
            MATCH (n)-[r]-(m)
            RETURN n, r, m
            '''
            result = session.run(query)
            nodes = [dict(record) for record in result]
            return jsonify({'success': True, 'data': nodes})
    except Exception as e:
        print(f"Error in get_full_graph: {str(e)}")
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
