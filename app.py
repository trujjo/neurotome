from flask import Flask, render_template_string, jsonify
from datetime import datetime
import logging
from neo4j import GraphDatabase  # Add this import

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Neo4j connection configuration
NEO4J_URI = "your_neo4j_uri"  # e.g., "neo4j+s://xxx.databases.neo4j.io"
NEO4J_USER = "your_username"
NEO4J_PASSWORD = "your_password"

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

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

@app.route('/refresh-data')
def refresh_data():
    try:
        nodes, edges = get_graph_data()
        
        # Get unique locations and types from nodes
        locations = list(set(
            node['properties'].get('location') 
            for node in nodes 
            if 'location' in node['properties']
        ))
        types = list(set(
            node['properties'].get('type') 
            for node in nodes 
            if 'type' in node['properties']
        ))
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'graph_data': {'nodes': nodes, 'edges': edges},
            'filters': {
                'locations': locations,
                'types': types
            }
        })
    except Exception as e:
        logging.error(f"Error in refresh_data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# The rest of your code (html_template and other routes) remains the same

if __name__ == '__main__':
    try:
        # Test database connection
        with driver.session() as session:
            session.run("MATCH (n) RETURN count(n) LIMIT 1")
        logging.info("Successfully connected to Neo4j database")
        app.run(host='0.0.0.0', port=10000, debug=False)
    except Exception as e:
        logging.error(f"Failed to connect to Neo4j: {str(e)}")
    finally:
        driver.close()
