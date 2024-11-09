from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase, exceptions
import os
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app instance
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
    """Create and return a Neo4j driver instance."""
    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        # Test the connection
        with driver.session() as session:
            session.run("RETURN 1")
        return driver
    except exceptions.ServiceUnavailable as e:
        logger.error(f"Failed to connect to Neo4j database: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating Neo4j driver: {str(e)}")
        raise

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/nodes/types')
def get_node_types():
    """Return the list of valid node types."""
    try:
        return jsonify(VALID_LABELS)
    except Exception as e:
        logger.error(f"Error fetching node types: {str(e)}")
        return jsonify({"error": "Failed to fetch node types"}), 500

@app.route('/api/nodes/locations')
def get_locations():
    """Fetch distinct locations from the database."""
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WHERE exists(n.location)
                RETURN DISTINCT n.location as location
                ORDER BY location
            ''')
            locations = [record['location'] for record in result if record['location']]
            return jsonify(locations)
    except exceptions.ServiceUnavailable as e:
        logger.error(f"Database connection error: {str(e)}")
        return jsonify({"error": "Database connection failed"}), 503
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        return jsonify({"error": "Failed to fetch locations"}), 500

@app.route('/api/nodes/sublocations')
def get_sublocations():
    """Fetch distinct sublocations from the database."""
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WHERE exists(n.sublocation)
                RETURN DISTINCT n.sublocation as sublocation
                ORDER BY sublocation
            ''')
            sublocations = [record['sublocation'] for record in result if record['sublocation']]
            return jsonify(sublocations)
    except exceptions.ServiceUnavailable as e:
        logger.error(f"Database connection error: {str(e)}")
        return jsonify({"error": "Database connection failed"}), 503
    except Exception as e:
        logger.error(f"Error fetching sublocations: {str(e)}")
        return jsonify({"error": "Failed to fetch sublocations"}), 500

@app.route('/api/graph/filtered')
def get_filtered_graph():
    """Fetch filtered graph data based on selected criteria."""
    try:
        # Get filter parameters
        node_types = request.args.getlist('nodeTypes[]')
        locations = request.args.getlist('locations[]')
        sublocations = request.args.getlist('sublocations[]')

        # Validate node types
        if node_types and any(node_type not in VALID_LABELS for node_type in node_types):
            return jsonify({"error": "Invalid node type provided"}), 400

        # Build the Cypher query dynamically
        query_parts = []
        where_conditions = []
        params = {}

        # Base MATCH clause
        if node_types:
            query_parts.append("MATCH (n) WHERE any(label IN labels(n) WHERE label IN $nodeTypes)")
            params['nodeTypes'] = node_types
        else:
            query_parts.append("MATCH (n)")

        # Add location filters
        if locations:
            where_conditions.append("n.location IN $locations")
            params['locations'] = locations

        if sublocations:
            where_conditions.append("n.sublocation IN $sublocations")
            params['sublocations'] = sublocations

        # Combine WHERE conditions
        if where_conditions:
            query_parts.append("AND " + " AND ".join(where_conditions))

        # Add relationship pattern
        query_parts.append("""
        WITH COLLECT(n) as nodes
        UNWIND nodes as n
        MATCH (n)-[r]-(m)
        WHERE m IN nodes
        RETURN COLLECT(DISTINCT n) as nodes, COLLECT(DISTINCT r) as rels
        """)

        # Execute query
        with get_neo4j_driver().session() as session:
            result = session.run(" ".join(query_parts), params)
            record = result.single()

            if not record:
                return jsonify({"nodes": [], "relationships": []})

            # Process nodes
            nodes = []
            nodes_set = set()
            for node in record['nodes']:
                node_dict = dict(node)
                node_id = node_dict.get('name', str(node.id))
                
                if node_id not in nodes_set:
                    nodes_set.add(node_id)
                    node_dict['id'] = node_id
                    node_dict['labels'] = list(node.labels)
                    
                    # Safely convert coordinates to float if they exist
                    if 'x' in node_dict:
                        try:
                            node_dict['x'] = float(node_dict['x'])
                        except (ValueError, TypeError):
                            node_dict['x'] = 0.0
                    
                    if 'y' in node_dict:
                        try:
                            node_dict['y'] = float(node_dict['y'])
                        except (ValueError, TypeError):
                            node_dict['y'] = 0.0
                            
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
                    'type': rel.type,
                    'properties': dict(rel)
                })

            return jsonify({
                'nodes': nodes,
                'relationships': relationships
            })

    except exceptions.ServiceUnavailable as e:
        logger.error(f"Database connection error: {str(e)}")
        return jsonify({"error": "Database connection failed"}), 503
    except Exception as e:
        logger.error(f"Error in get_filtered_graph: {str(e)}")
        return jsonify({"error": "Failed to fetch graph data"}), 500

@app.route('/health')
def health_check():
    """Perform a health check of the application and database connection."""
    try:
        with get_neo4j_driver().session() as session:
            session.run("RETURN 1")
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        })
    except exceptions.ServiceUnavailable as e:
        logger.error(f"Database health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 503
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
