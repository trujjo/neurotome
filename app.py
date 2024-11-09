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
    return render_template('index.html')

@app.route('/api/nodes/types')
def get_node_types():
    try:
        # Log the request
        logger.info("Fetching node types")
        return jsonify(VALID_LABELS)
    except Exception as e:
        logger.error(f"Error fetching node types: {str(e)}")
        return jsonify({"error": "Failed to fetch node types"}), 500

@app.route('/api/nodes/locations')
def get_locations():
    try:
        # Log the request
        logger.info("Fetching locations")
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WHERE exists(n.location)
                RETURN DISTINCT n.location as location
                ORDER BY location
            ''')
            locations = [record['location'] for record in result if record['location']]
            logger.info(f"Found {len(locations)} locations")
            return jsonify(locations)
    except exceptions.ServiceUnavailable as e:
        logger.error(f"Database connection error: {str(e)}")
        return jsonify({"error": "Database connection failed"}), 503
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        return jsonify({"error": "Failed to fetch locations"}), 500

@app.route('/api/nodes/sublocations')
def get_sublocations():
    try:
        # Log the request
        logger.info("Fetching sublocations")
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WHERE exists(n.sublocation)
                RETURN DISTINCT n.sublocation as sublocation
                ORDER BY sublocation
            ''')
            sublocations = [record['sublocation'] for record in result if record['sublocation']]
            logger.info(f"Found {len(sublocations)} sublocations")
            return jsonify(sublocations)
    except exceptions.ServiceUnavailable as e:
        logger.error(f"Database connection error: {str(e)}")
        return jsonify({"error": "Database connection failed"}), 503
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

        # Log the received filters
        logger.info(f"Received filters - Node Types: {node_types}, Locations: {locations}, Sublocations: {sublocations}")

        # Validate node types
        if node_types and any(node_type not in VALID_LABELS for node_type in node_types):
            logger.error("Invalid node type provided")
            return jsonify({"error": "Invalid node type provided"}), 400

        # Build the Cypher query
        query_parts = []
        where_conditions = []
        params = {}

        # Start with base MATCH clause
        query_parts.append("MATCH (n)")

        # Add label filter if node types are specified
        if node_types:
            where_conditions.append("any(label IN labels(n) WHERE label IN $nodeTypes)")
            params['nodeTypes'] = node_types

        # Add location filters
        if locations:
            where_conditions.append("n.location IN $locations")
            params['locations'] = locations

        if sublocations:
            where_conditions.append("n.sublocation IN $sublocations")
            params['sublocations'] = sublocations

        # Combine WHERE conditions if any exist
        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))

        # Add relationship pattern and return statement
        query_parts.extend([
            "WITH COLLECT(n) as nodes",
            "UNWIND nodes as n",
            "OPTIONAL MATCH (n)-[r]-(m)",
            "WHERE m IN nodes",
            "RETURN COLLECT(DISTINCT n) as nodes, COLLECT(DISTINCT r) as rels"
        ])

        # Combine query parts
        final_query = " ".join(query_parts)
        logger.info(f"Executing query: {final_query}")
        logger.info(f"With parameters: {params}")

        # Execute query
        with get_neo4j_driver().session() as session:
            result = session.run(final_query, params)
            record = result.single()

            if not record:
                logger.info("No results found")
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
                    
                    # Safely convert coordinates
                    for coord in ['x', 'y']:
                        if coord in node_dict:
                            try:
                                node_dict[coord] = float(node_dict[coord])
                            except (ValueError, TypeError):
                                node_dict[coord] = 0.0
                    
                    nodes.append(node_dict)

            # Process relationships
            relationships = []
            for rel in record['rels']:
                if rel is not None:  # Check if relationship exists
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

            response_data = {
                'nodes': nodes,
                'relationships': relationships
            }
            
            logger.info(f"Returning {len(nodes)} nodes and {len(relationships)} relationships")
            return jsonify(response_data)

    except exceptions.ServiceUnavailable as e:
        logger.error(f"Database connection error: {str(e)}")
        return jsonify({"error": "Database connection failed"}), 503
    except Exception as e:
        logger.error(f"Error in get_filtered_graph: {str(e)}")
        return jsonify({"error": "Failed to fetch graph data"}), 500

@app.route('/health')
def health_check():
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
