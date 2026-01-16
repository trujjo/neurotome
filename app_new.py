"""
Artery Mapping Application - Clean Backend
Flask + Neo4j for finding paths between arteries
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from neo4j import GraphDatabase
import os

# Initialize Flask app
app = Flask(__name__, static_folder='public')
CORS(app)

# Neo4j connection setup
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j+s://415ed9b1.databases.neo4j.io:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', '7GBG6XDYOFdwcfgkdcNyDgbtMk6jnZXWxxoAT5vBPVU')

try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    # Test connection
    with driver.session() as session:
        session.run("RETURN 1")
    print("✓ Connected to Neo4j")
except Exception as e:
    print(f"✗ Neo4j connection failed: {e}")
    driver = None


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    """Serve the main index page"""
    return send_from_directory('public', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, etc.)"""
    return send_from_directory('public', path)


@app.route('/api/arteries/search', methods=['GET'])
def search_arteries():
    """Search for arteries by name (case-insensitive)"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 50, type=int)

    if not query or len(query) < 1:
        return jsonify([])

    if not driver:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with driver.session() as session:
            neo4j_query = """
            MATCH (a:structure)
            WHERE toLower(a.name) CONTAINS toLower($search)
            RETURN a.name AS name, elementId(a) AS id
            ORDER BY a.name
            LIMIT $limit
            """
            result = session.run(neo4j_query, search=query, limit=limit)
            arteries = [{'id': record['id'], 'name': record['name']} for record in result]
            return jsonify(arteries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/arteries/all', methods=['GET'])
def get_all_arteries():
    """Get all nodes regardless of label for nerves/structures tab"""
    if not driver:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with driver.session() as session:
            query = """
            MATCH (a)
            WHERE a.name IS NOT NULL
            RETURN DISTINCT a.name AS name, elementId(a) AS id
            ORDER BY a.name
            """
            result = session.run(query)
            arteries = [{'id': record['id'], 'name': record['name']} for record in result]
            return jsonify(arteries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/arteries/only', methods=['GET'])
def get_arteries_only():
    """Get only nodes with Artery label for arteries tab"""
    if not driver:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with driver.session() as session:
            query = """
            MATCH (a:artery)
            WHERE a.name IS NOT NULL
            RETURN DISTINCT a.name AS name, elementId(a) AS id
            ORDER BY a.name
            """
            result = session.run(query)
            arteries = [{'id': record['id'], 'name': record['name']} for record in result]
            return jsonify(arteries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/path/find', methods=['POST'])
def find_artery_path():
    """Find shortest path between two structures"""
    data = request.json
    start_artery = data.get('start', '').strip()
    end_artery = data.get('end', '').strip()
    label = data.get('label', 'structure')  # Default to structure, can specify artery

    if not start_artery or not end_artery:
        return jsonify({'error': 'Start and end structures required'}), 400

    if start_artery == end_artery:
        return jsonify({'error': 'Start and end structures must be different'}), 400

    if not driver:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with driver.session() as session:
            # Query to find shortest path using only supplies relationships in forward direction
            query = f"""
            MATCH (start:{label} {{name: $start_name}}), (end:{label} {{name: $end_name}})
            MATCH path = shortestPath((start)-[:supplies*]->(end))
            WITH path, nodes(path) AS pathNodes, relationships(path) AS pathRels
            RETURN 
                [node IN pathNodes | {{name: node.name, id: elementId(node)}}] AS arteries,
                [rel IN pathRels | type(rel)] AS relationships,
                [i IN range(0, size(pathRels)-1) | 'forward'] AS directions,
                length(path) AS distance
            LIMIT 1
            """
            
            result = session.run(query, start_name=start_artery, end_name=end_artery)
            records = list(result)

            if not records:
                return jsonify({
                    'found': False,
                    'message': f'No path found between {start_artery} and {end_artery}'
                }), 404

            record = records[0]
            return jsonify({
                'found': True,
                'arteries': record['arteries'],
                'relationships': record['relationships'],
                'directions': record['directions'],
                'distance': record['distance'],
                'message': f'Path found: {start_artery} → {end_artery}'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get basic database statistics"""
    if not driver:
        return jsonify({'error': 'Database connection failed'}), 500
    
    label = request.args.get('label', 'structure')  # Can specify artery or structure

    try:
        with driver.session() as session:
            # Count nodes with specific label
            artery_count = session.run(f"MATCH (a:{label}) RETURN count(a) AS count")
            arteries = artery_count.single()['count']

            # Count relationships
            rel_count = session.run("MATCH ()-[r]-() RETURN count(r) AS count")
            relationships = rel_count.single()['count']

            return jsonify({
                'arteries': arteries,
                'relationships': relationships
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/connections/upstream', methods=['POST'])
def get_upstream_connections():
    """Get all upstream (incoming) connections to a node"""
    data = request.json
    node_name = data.get('node', '').strip()
    label = data.get('label', 'artery')

    if not node_name:
        return jsonify({'error': 'Node name required'}), 400

    if not driver:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with driver.session() as session:
            query = f"""
            MATCH (target:{label} {{name: $name}})<-[rel]-(source:{label})
            RETURN 
                source.name AS source_name,
                elementId(source) AS source_id,
                type(rel) AS relationship,
                target.name AS target_name,
                elementId(target) AS target_id
            ORDER BY source.name
            """
            
            result = session.run(query, name=node_name)
            connections = [
                {
                    'source': record['source_name'],
                    'source_id': record['source_id'],
                    'target': record['target_name'],
                    'relationship': record['relationship']
                }
                for record in result
            ]

            return jsonify({
                'node': node_name,
                'direction': 'upstream',
                'connections': connections,
                'count': len(connections)
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/connections/downstream', methods=['POST'])
def get_downstream_connections():
    """Get all downstream (outgoing) connections from a node"""
    data = request.json
    node_name = data.get('node', '').strip()
    label = data.get('label', 'artery')

    if not node_name:
        return jsonify({'error': 'Node name required'}), 400

    if not driver:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with driver.session() as session:
            query = f"""
            MATCH (source:{label} {{name: $name}})-[rel]->(target:{label})
            RETURN 
                source.name AS source_name,
                elementId(source) AS source_id,
                type(rel) AS relationship,
                target.name AS target_name,
                elementId(target) AS target_id
            ORDER BY target.name
            """
            
            result = session.run(query, name=node_name)
            connections = [
                {
                    'source': record['source_name'],
                    'target': record['target_name'],
                    'target_id': record['target_id'],
                    'relationship': record['relationship']
                }
                for record in result
            ]

            return jsonify({
                'node': node_name,
                'direction': 'downstream',
                'connections': connections,
                'count': len(connections)
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/graph/all', methods=['GET'])
def get_full_graph():
    """Get all nodes and edges for complete graph visualization"""
    if not driver:
        return jsonify({'error': 'Database connection failed'}), 500
    
    label = request.args.get('label', 'structure')  # Can specify artery or all
    limit = request.args.get('limit', 100, type=int)  # Limit nodes to prevent overwhelming the browser

    try:
        with driver.session() as session:
            # Query to get all nodes and their relationships
            if label == 'all':
                query = """
                MATCH (n)
                WHERE n.name IS NOT NULL
                WITH n
                LIMIT $limit
                OPTIONAL MATCH (n)-[r]-(m)
                WHERE m.name IS NOT NULL
                RETURN 
                    collect(DISTINCT {id: elementId(n), name: n.name, labels: labels(n)}) AS nodes,
                    collect(DISTINCT {
                        source: elementId(startNode(r)), 
                        target: elementId(endNode(r)), 
                        type: type(r),
                        id: elementId(r)
                    }) AS edges
                """
            else:
                query = f"""
                MATCH (n:{label})
                WHERE n.name IS NOT NULL
                WITH n
                LIMIT $limit
                OPTIONAL MATCH (n)-[r]-(m:{label})
                WHERE m.name IS NOT NULL
                RETURN 
                    collect(DISTINCT {{id: elementId(n), name: n.name, labels: labels(n)}}) AS nodes,
                    collect(DISTINCT {{
                        source: elementId(startNode(r)), 
                        target: elementId(endNode(r)), 
                        type: type(r),
                        id: elementId(r)
                    }}) AS edges
                """
            
            result = session.run(query, limit=limit)
            record = result.single()
            
            if not record:
                return jsonify({
                    'nodes': [],
                    'edges': [],
                    'message': 'No data found'
                })
            
            # Clean up None values from edges (from OPTIONAL MATCH)
            nodes = [n for n in record['nodes'] if n]
            edges = [e for e in record['edges'] if e and e['id'] is not None]
            
            return jsonify({
                'nodes': nodes,
                'edges': edges,
                'nodeCount': len(nodes),
                'edgeCount': len(edges)
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001)
