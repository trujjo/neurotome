def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 10000))
        # Test database connection
        with driver.session() as session: from flask import Flask, render_template, jsonify
from datetime import datetime
import logging
from neo4j import GraphDatabase
import os

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
            # Enhanced query to get nodes of specific type with their relationships
            query = f"""
            MATCH (n:{node_type})
            OPTIONAL MATCH (n)-[r]-(m)
            WITH n, r, m
            RETURN DISTINCT 
                id(n) as id,
                labels(n) as labels,
                properties(n) as properties,
                collect(DISTINCT {{
                    relationshipType: type(r),
                    nodeId: id(m),
                    nodeLabels: labels(m),
                    nodeProperties: properties(m)
                }}) as connections
            """
            
            result = session.run(query)
            nodes_data = []
            relationships_data = []
            
            for record in result:
                # Add the main node
                nodes_data.append({
                    'id': str(record['id']),
                    'label': record['labels'][0],
                    'properties': record['properties']
                })
                
                # Add connected nodes and relationships
                for conn in record['connections']:
                    if conn['nodeId'] is not None:
                        # Add connected node
                        nodes_data.append({
                            'id': str(conn['nodeId']),
                            'label': conn['nodeLabels'][0],
                            'properties': conn['nodeProperties']
                        })
                        # Add relationship
                        relationships_data.append({
                            'from': str(record['id']),
                            'to': str(conn['nodeId']),
                            'type': conn['relationshipType']
                        })

            # Remove duplicate nodes while preserving order
            unique_nodes = list({node['id']: node for node in nodes_data}.values())
            
            return jsonify({
                'nodes': unique_nodes,
                'relationships': relationships_data,
                'nodeCount': len(unique_nodes),
                'relationshipCount': len(relationships_data)
            })

    except Exception as e:
        logging.error(f"Error in get_nodes_by_type: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        with driver.session() as session:
            result = session.run("RETURN 1")
            return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/search')
def search_nodes():
    query = request.args.get('q', '').lower()
    if len(query) < 3:
        return jsonify({'nodes': [], 'relationships': []})
    
    try:
        with driver.session() as session:
            # Search in node properties and labels
            result = session.run('''
                MATCH (n)
                WHERE any(prop in keys(n) WHERE toString(n[prop]) CONTAINS $query)
                   OR any(label in labels(n) WHERE toLower(label) CONTAINS $query)
                WITH n
                OPTIONAL MATCH (n)-[r]-(connected)
                RETURN 
                    id(n) as nodeId,
                    labels(n) as nodeLabels,
                    properties(n) as nodeProperties,
                    id(connected) as connectedId,
                    labels(connected) as connectedLabels,
                    properties(connected) as connectedProperties,
                    type(r) as relationType
            ''', query=query)
            
            nodes_data = []
            relationships_data = []
            processed_nodes = set()
            
            for record in result:
                # Add main node if not already added
                if str(record['nodeId']) not in processed_nodes:
                    nodes_data.append({
                        'id': str(record['nodeId']),
                        'label': record['nodeLabels'][0] if record['nodeLabels'] else 'Node',
                        'properties': record['nodeProperties']
                    })
                    processed_nodes.add(str(record['nodeId']))
                
                # Add connected node and relationship if they exist
                if record['connectedId'] is not None:
                    if str(record['connectedId']) not in processed_nodes:
                        nodes_data.append({
                            'id': str(record['connectedId']),
                            'label': record['connectedLabels'][0] if record['connectedLabels'] else 'Node',
                            'properties': record['connectedProperties']
                        })
                        processed_nodes.add(str(record['connectedId']))
                    
                    relationships_data.append({
                        'from': str(record['nodeId']),
                        'to': str(record['connectedId']),
                        'type': record['relationType']
                    })
            
            return jsonify({
                'nodes': nodes_data,
                'relationships': relationships_data
            })
            
    except Exception as e:
        logging.error(f"Error in search_nodes: {str(e)}")
        return jsonify({'error': str(e)}), 500

from flask import request

@app.route('/search')
def search_nodes():
    query = request.args.get('q', '').lower()
    if len(query) < 3:
        return jsonify({'nodes': [], 'relationships': []})
    
    try:
        with driver.session() as session:
            # Search in node properties and labels
            result = session.run('''
                MATCH (n)
                WHERE any(prop in keys(n) WHERE toString(n[prop]) CONTAINS $query)
                   OR any(label in labels(n) WHERE toLower(label) CONTAINS $query)
                WITH n
                OPTIONAL MATCH (n)-[r]-(connected)
                RETURN 
                    id(n) as nodeId,
                    labels(n) as nodeLabels,
                    properties(n) as nodeProperties,
                    id(connected) as connectedId,
                    labels(connected) as connectedLabels,
                    properties(connected) as connectedProperties,
                    type(r) as relationType
            ''', query=query)
            
            nodes_data = []
            relationships_data = []
            processed_nodes = set()
            
            for record in result:
                # Add main node if not already added
                if str(record['nodeId']) not in processed_nodes:
                    nodes_data.append({
                        'id': str(record['nodeId']),
                        'label': record['nodeLabels'][0] if record['nodeLabels'] else 'Node',
                        'properties': record['nodeProperties']
                    })
                    processed_nodes.add(str(record['nodeId']))
                
                # Add connected node and relationship if they exist
                if record['connectedId'] is not None:
                    if str(record['connectedId']) not in processed_nodes:
                        nodes_data.append({
                            'id': str(record['connectedId']),
                            'label': record['connectedLabels'][0] if record['connectedLabels'] else 'Node',
                            'properties': record['connectedProperties']
                        })
                        processed_nodes.add(str(record['connectedId']))
                    
                    relationships_data.append({
                        'from': str(record['nodeId']),
                        'to': str(record['connectedId']),
                        'type': record['relationType']
                    })
            
            return jsonify({
                'nodes': nodes_data,
                'relationships': relationships_data
            })
            
    except Exception as e:
        logging.error(f"Error in search_nodes: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)

            session.run("MATCH (n) RETURN count(n) LIMIT 1")
        logging.info("Successfully connected to Neo4j database")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logging.error(f"Failed to connect to Neo4j: {str(e)}")
    finally:
        driver.close()
