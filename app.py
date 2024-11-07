from flask import Flask, render_template, jsonify
from datetime import datetime
import logging
from neo4j import GraphDatabase

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Neo4j connection configuration
NEO4J_URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Poconoco16!"

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Define node types
NODE_TYPES = [
    'nerve', 'bone', 'neuro', 'region', 'viscera', 'muscle', 'sense',
    'vein', 'artery', 'cv', 'function', 'sensory', 'gland', 'lymph',
    'head', 'organ', 'sensation', 'skin'
]

def get_graph_data():
    with driver.session() as session:
        # Fetch nodes
        nodes_result = session.run("""
            MATCH (n)
            RETURN 
                id(n) as id, 
                labels(n) as labels, 
                properties(n) as properties
        """)
        nodes = [
            {
                'id': str(record['id']),
                'label': record['labels'][0] if record['labels'] else 'Node',
                'properties': record['properties']
            } for record in nodes_result
        ]

        # Fetch relationships
        edges_result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN 
                id(a) as from, 
                id(b) as to, 
                type(r) as type,
                properties(r) as properties
        """)
        edges = [
            {
                'from': str(record['from']),
                'to': str(record['to']),
                'label': record['type'],
                'properties': record['properties']
            } for record in edges_result
        ]

        return nodes, edges

@app.route('/')
def index():
    """Main visualization page"""
    return render_template('visualization.html', node_types=NODE_TYPES)

@app.route('/refresh-data')
def refresh_data():
    try:
        nodes, edges = get_graph_data()
        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'graph_data': {'nodes': nodes, 'edges': edges}
        })
    except Exception as e:
        logging.error(f"Error in refresh_data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/nodes/<node_type>')
def get_nodes_by_type(node_type):
    try:
        with driver.session() as session:
            query = """
            MATCH (n:%s)
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN n, collect(DISTINCT {relationship: type(r), node: m}) as connections
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

if __name__ == '__main__':
    try:
        # Test database connection
        with driver.session() as session:
            session.run("MATCH (n) RETURN count(n) LIMIT 1")
        logging.info("Successfully connected to Neo4j database")
        app.run(host='0.0.0.0', port=10000, debug=True)
    except Exception as e:
        logging.error(f"Failed to connect to Neo4j: {str(e)}")
    finally:
        driver.close()
