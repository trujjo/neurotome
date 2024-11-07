app_code = """
from flask import Flask, render_template, jsonify, g
from neo4j import GraphDatabase
from neo4j.exceptions import ResultFailedError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Neo4j Configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j+s://4e5eeae5.databases.neo4j.io:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Poconoco16!')

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Verify Neo4j connectivity
try:
    driver.verify_connectivity()
except Exception as e:
    print(f"Failed to connect to Neo4j: {str(e)}")
    raise

def get_nodes_by_type(tx, node_type):
    try:
        query = f'''
        MATCH (n:{node_type})-[r]-(m)
        RETURN n, r, m
        '''
        result = tx.run(query)
        return [dict(record) for record in result]
    except Exception as e:
        raise ResultFailedError(f"Failed to execute query: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/nodes/<node_type>')
def get_nodes(node_type):
    with driver.session() as session:
        try:
            nodes = session.read_transaction(get_nodes_by_type, node_type)
            return jsonify({'success': True, 'data': nodes})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

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
    return jsonify({'success': True, 'node_types': node_types
