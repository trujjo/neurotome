from flask import Flask, jsonify, request
import logging
from neo4j import GraphDatabase
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# Neo4j connection configuration
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD")
port = int(os.getenv("PORT", 5000))

# Initialize Neo4j driver
try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
except Exception as e:
    logging.error(f"Failed to create Neo4j driver: {str(e)}")
    driver = None

@app.route('/search')
def search_nodes():
    query = request.args.get('q', '').lower()
    if len(query) < 3:
        return jsonify({'nodes': [], 'relationships': []})
    
    try:
        with driver.session() as session:
            # Search in node properties and labels
            result = session.run("""
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
            """, query=query)
            
            nodes_data = []
            relationships_data = []
            processed_nodes = set()
            
            for record in result:
                if str(record['nodeId']) not in processed_nodes:
                    nodes_data.append({
                        'id': str(record['nodeId']),
                        'labels': record['nodeLabels'],
                        'properties': record['nodeProperties']
                    })
                    processed_nodes.add(str(record['nodeId']))
                
                if record['connectedId'] is not None and str(record['connectedId']) not in processed_nodes:
                    nodes_data.append({
                        'id': str(record['connectedId']),
                        'labels': record['connectedLabels'],
                        'properties': record['connectedProperties']
                    })
                    processed_nodes.add(str(record['connectedId']))
                
                if record['connectedId'] is not None:
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
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        with driver.session() as session:
            session.run("MATCH (n) RETURN count(n) LIMIT 1")
        logging.info("Successfully connected to Neo4j database")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logging.error(f"Failed to connect to Neo4j: {str(e)}")
    finally:
        if driver:
            driver.close()
