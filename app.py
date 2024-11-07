from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase
import os
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

uri = "bolt://4e5eeae5.databases.neo4j.io:7687"
user = "neo4j"
password = "Poconoco16!"

# Add color mapping for node types
NODE_COLORS = {
    'Artery': '#FF6B6B',
    'Nerve': '#4ECDC4',
    'Muscle': '#45B7D1',
    'Bone': '#96CEB4',
    'Organ': '#FFEEAD',
    # Add more colors for other node types
}

def get_neo4j_driver():
    try:
        driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            encrypted=True
        )
        with driver.session() as session:
            result = session.run("RETURN 1")
            result.single()
            logger.info("Successfully connected to Neo4j")
        return driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        raise

# Add new route for node search/autocomplete
@app.route('/search_nodes', methods=['POST'])
def search_nodes():
    try:
        search_term = request.json.get('search_term', '')
        driver = get_neo4j_driver()
        with driver.session() as session:
            query = """
            MATCH (n)
            WHERE n.name =~ $search_term
            RETURN n.name as name
            LIMIT 10
            """
            result = session.run(query, search_term=f"(?i).*{search_term}.*")
            suggestions = [record["name"] for record in result]
            return jsonify(suggestions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add new route for finding shortest path
@app.route('/find_shortest_path', methods=['POST'])
def find_shortest_path():
    try:
        source = request.json.get('source')
        target = request.json.get('target')
        
        driver = get_neo4j_driver()
        with driver.session() as session:
            # First, find the shortest path
            path_query = """
            MATCH path = shortestPath((source:Artery {name: $source})-[*]-(target:Artery {name: $target}))
            RETURN path
            """
            result = session.run(path_query, source=source, target=target)
            
            path_data = []
            for record in result:
                path = record["path"]
                nodes = []
                relationships = []
                
                # Extract nodes
                for node in path.nodes:
                    node_data = {
                        'id': str(node.id),
                        'label': node.get('name', ''),
                        'title': str(dict(node)),
                        'color': NODE_COLORS.get(list(node.labels)[0], '#97C2FC')
                    }
                    nodes.append(node_data)
                
                # Extract relationships
                for rel in path.relationships:
                    rel_data = {
                        'from': str(rel.start_node.id),
                        'to': str(rel.end_node.id),
                        'label': type(rel)
                    }
                    relationships.append(rel_data)
                
                path_data.append({
                    'nodes': nodes,
                    'relationships': relationships
                })
            
            return jsonify(path_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_graph_metadata():
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            query = """
            MATCH (n)
            WITH DISTINCT labels(n) as labels, n.location as location, n.sublocation as sublocation
            RETURN labels, location, sublocation
            """
            result = session.run(query)
            
            node_types = set()
            locations = set()
            sublocations = set()
            
            for record in result:
                node_types.update(record['labels'])
                if record['location']:
                    locations.add(record['location'])
                if record['sublocation']:
                    sublocations.add(record['sublocation'])

            rel_query = """
            MATCH ()-[r]->()
            RETURN DISTINCT type(r) as type
            """
            rel_result = session.run(rel_query)
            relationship_types = [record['type'] for record in rel_result]

            return {
                'node_types': sorted(list(node_types)),
                'locations': sorted(list(locations)),
                'sublocations': sorted(list(sublocations)),
                'relationship_types': sorted(relationship_types),
                'node_colors': NODE_COLORS  # Add colors to metadata
            }
    except Exception as e:
        logger.error(f"Error fetching metadata: {str(e)}")
        raise
    finally:
        if 'driver' in locals():
            driver.close()

@app.route('/')
def index():
    try:
        metadata = get_graph_metadata()
        return render_template('index.html', metadata=metadata)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in index route: {error_msg}")
        return render_template('index.html', error=error_msg)

@app.route('/get_nodes', methods=['POST'])
def get_nodes():
    try:
        data = request.get_json()
        node_type = data.get('node_type')
        location = data.get('location')
        sublocation = data.get('sublocation')
        
        driver = get_neo4j_driver()
        with driver.session() as session:
            query = """
            MATCH (n)
            WHERE 1=1
            """
            if node_type:
                query += f" AND any(label IN labels(n) WHERE label = '{node_type}')"
            if location:
                query += f" AND n.location = '{location}'"
            if sublocation:
                query += f" AND n.sublocation = '{sublocation}'"
            
            query += " RETURN id(n) as id, labels(n) as labels, properties(n) as props"
            
            result = session.run(query)
            nodes = []
            for record in result:
                name = record['props'].get('name', record['labels'][0])
                font_size = min(8, max(4, int(24 / len(name))))
                
                # Get coordinates and flip y-axis
                x_coord = float(record['props'].get('x', 0)) * 100
                y_coord = float(record['props'].get('y', 0)) * 100
                flipped_y = -y_coord  # Flip the y-coordinate
                
                # Get color based on node type
                node_type = record['labels'][0]
                color = NODE_COLORS.get(node_type, '#97C2FC')
                
                node = {
                    'id': str(record['id']),
                    'label': name,
                    'title': str(record['props']),
                    'x': x_coord,
                    'y': flipped_y,
                    'color': color,
                    'font': {
                        'size': font_size
                    }
                }
                nodes.append(node)
            return jsonify(nodes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_relationships', methods=['POST'])
def get_relationships():
    try:
        data = request.get_json()
        rel_type = data.get('relationship_type')
        
        driver = get_neo4j_driver()
        with driver.session() as session:
            query = """
            MATCH (n)-[r]->(m)
            WHERE type(r) = $rel_type
            RETURN id(n) as source_id, id(m) as target_id, type(r) as type
            """
            result = session.run(query, rel_type=rel_type)
            edges = []
            for record in result:
                edge = {
                    'from': str(record['source_id']),
                    'to': str(record['target_id']),
                    'label': record['type']
                }
                edges.append(edge)
            return jsonify(edges)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
