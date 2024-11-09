# Create improved app.py with hardcoded credentials
from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Neo4j connection configuration
NEO4J_URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Poconoco16!"

def get_neo4j_driver():
    try:
        return GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    except Exception as e:
        logger.error(f"Failed to create Neo4j driver: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/nodes/types')
def get_node_types():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                UNWIND labels(n) as label
                RETURN DISTINCT label
                ORDER BY label
            ''')
            types = [record['label'] for record in result]
            return jsonify(types)
    except Exception as e:
        logger.error(f"Error fetching node types: {str(e)}")
        return jsonify({"error": "Failed to fetch node types"}), 500

@app.route('/api/nodes/locations')
def get_locations():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WHERE exists(n.location)
                RETURN DISTINCT n.location as location
                ORDER BY location
            ''')
            locations = [record['location'] for record in result]
            return jsonify(locations)
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        return jsonify({"error": "Failed to fetch locations"}), 500

@app.route('/api/nodes/sublocations')
def get_sublocations():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WHERE exists(n.sublocation)
                RETURN DISTINCT n.sublocation as sublocation
                ORDER BY sublocation
            ''')
            sublocations = [record['sublocation'] for record in result]
            return jsonify(sublocations)
    except Exception as e:
        logger.error(f"Error fetching sublocations: {str(e)}")
        return jsonify({"error": "Failed to fetch sublocations"}), 500

@app.route('/api/graph/filtered')
def get_filtered_graph():
    try:
        node_types = request.args.getlist('nodeTypes[]')
        locations = request.args.getlist('locations[]')
        sublocations = request.args.getlist('sublocations[]')
        
        # Validate input parameters
        if not all(isinstance(item, str) for item in node_types + locations + sublocations):
            return jsonify({"error": "Invalid input parameters"}), 400
        
        query = '''
        MATCH (n)-[r]->(m)
        WHERE 
            (size($nodeTypes) = 0 OR any(label IN labels(n) WHERE label IN $nodeTypes))
            AND (size($locations) = 0 OR n.location IN $locations)
            AND (size($sublocations) = 0 OR n.sublocation IN $sublocations)
        WITH collect(DISTINCT n) as nodes, collect(DISTINCT r) as rels
        RETURN nodes, rels
        '''
        
        with get_neo4j_driver().session() as session:
            result = session.run(query, 
                               nodeTypes=node_types,
                               locations=locations,
                               sublocations=sublocations)
            
            record = result.single()
            if not record:
                return jsonify({"nodes": [], "relationships": []})
            
            # Process nodes
            nodes = []
            nodes_set = set()
            for node in record['nodes']:
                node_dict = dict(node)
                node_id = node_dict.get('id', str(id(node_dict)))
                if node_id not in nodes_set:
                    nodes_set.add(node_id)
                    node_dict['id'] = node_id
                    node_dict['labels'] = list(node.labels)
                    nodes.append(node_dict)
            
            # Process relationships
            relationships = []
            for rel in record['rels']:
                source_id = dict(rel.start_node).get('id', str(id(rel.start_node)))
                target_id = dict(rel.end_node).get('id', str(id(rel.end_node)))
                relationships.append({
                    'source': source_id,
                    'target': target_id,
                    'type': type(rel).__name__,
                    'properties': dict(rel)
                })
            
            return jsonify({
                'nodes': nodes,
                'relationships': relationships
            })
            
    except Exception as e:
        logger.error(f"Error in get_filtered_graph: {str(e)}")
        return jsonify({"error": "Failed to fetch graph data"}), 500

@app.route('/health')
def health_check():
    try:
        # Test database connection
        with get_neo4j_driver().session() as session:
            session.run("RETURN 1")
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
