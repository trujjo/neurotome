# Create improved app.py with proper label handling
improved_code = """from flask import Flask, render_template, jsonify, request
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

# Define valid node labels
VALID_LABELS = [
    'nerve', 'bone', 'neuro', 'region', 'viscera', 'muscle', 
    'sense', 'vein', 'artery', 'cv', 'function', 'sensory',
    'gland', 'lymph', 'head', 'organ', 'sensation', 'skin'
]

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
        # Return the predefined valid labels instead of querying
        return jsonify(VALID_LABELS)
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
        # Get filter parameters
        node_types = request.args.getlist('nodeTypes[]')
        locations = request.args.getlist('locations[]')
        sublocations = request.args.getlist('sublocations[]')
        
        # Validate node types against valid labels
        valid_node_types = [label for label in node_types if label in VALID_LABELS]
        
        # Build the Cypher query
        query = '''
        MATCH (n)
        WHERE (size($nodeTypes) = 0 OR any(label IN labels(n) WHERE label IN $nodeTypes))
        AND (size($locations) = 0 OR n.location IN $locations)
        AND (size($sublocations) = 0 OR n.sublocation IN $sublocations)
        WITH COLLECT(n) as nodes
        MATCH (n1)-[r]->(n2)
        WHERE n1 IN nodes AND n2 IN nodes
        RETURN nodes, COLLECT(r) as rels
        '''
        
        with get_neo4j_driver().session() as session:
            result = session.run(query,
                               nodeTypes=valid_node_types,
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
                # Use name as the primary identifier, fallback to neo4j internal id
                node_id = node_dict.get('name', str(node.id))
                if node_id not in nodes_set:
                    nodes_set.add(node_id)
                    node_dict['id'] = node_id
                    node_dict['labels'] = list(node.labels)
                    # Include x, y coordinates if they exist
                    if 'x' in node_dict and 'y' in node_dict:
                        node_dict['x'] = float(node_dict['x'])
                        node_dict['y'] = float(node_dict['y'])
                    nodes.append(node_dict)
            
            # Process relationships
            relationships = []
            for rel in record['rels']:
                source_node = dict(rel.start_node)
                target_node = dict(rel.end_node)
                source_id = source_node.get('name', str(rel.start_node.id))
                target_id = target_node.get('name', str(rel.end_node.id))
                
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
        with get_neo4j_driver().session() as session:
            session.run("RETURN 1")
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""

with open('app.py', 'w') as f:
    f.write(improved_code)

print("Created improved app.py with the following updates:")
print("1. Added predefined list of valid node labels")
print("2. Improved node type filtering")
print("3. Enhanced Cypher query to properly handle label filtering")
print("4. Added proper handling of node coordinates")
print("5. Improved node identification using name property")
print("6. Added validation for node types against valid labels")
