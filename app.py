from flask import Flask, jsonify, request
import logging
from datetime import datetime
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Neo4j driver
uri = os.getenv('NEO4J_URI')
username = os.getenv('NEO4J_USER')
password = os.getenv('NEO4J_PASSWORD')
driver = GraphDatabase.driver(uri, auth=(username, password))

@app.route('/search')
def search_nodes():
    query = request.args.get('q', '').lower()
    if len(query) < 3:
        return jsonify({'nodes': [], 'relationships': []})
    
    try:
        with driver.session() as session:
            # Your existing query code here
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
            
            # Process results
            nodes_data = []
            relationships_data = []
            processed_nodes = set()
            
            for record in result:
                if str(record['nodeId']) not in processed_nodes:
                    nodes_data.append({
                        'id': str(record['nodeId']),
                        'label': record['nodeLabels'][0] if record['nodeLabels'] else 'Node',
                        'properties': record['nodeProperties']
                    })
                    processed_nodes.add(str(record['nodeId']))
                
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

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 10000))
        with driver.session() as session:
            session.run("MATCH (n) RETURN count(n) LIMIT 1")
            logging.info("Successfully connected to Neo4j database")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logging.error(f"Failed to connect to Neo4j: {str(e)}")
    finally:
        driver.close()
