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

def get_graph_metadata():
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Get node types with their locations and sublocations
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

            # Get relationship types
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
                'relationship_types': sorted(relationship_types)
            }
    except Exception as e:
        logger.error(f"Error fetching metadata: {str(e)}")
        raise

def get_filtered_graph_data(selected_labels=None, selected_relationships=None):
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Build query based on filters
            query = """
            MATCH (n)-[r]->(m)
            WHERE 1=1
            """
            if selected_labels:
                query += " AND any(label IN labels(n) WHERE label IN $selected_labels)"
            if selected_relationships:
                query += " AND type(r) IN $selected_relationships"
            query += """
            RETURN 
                id(n) as source_id, labels(n) as source_labels, properties(n) as source_props,
                type(r) as relationship,
                id(m) as target_id, labels(m) as target_labels, properties(m) as target_props
            """
            result = session.run(query, selected_labels=selected_labels, selected_relationships=selected_relationships)
            
            nodes = {}
            edges = []
            for record in result:
                source_id = record['source_id']
                target_id = record['target_id']
                if source_id not in nodes:
                    nodes[source_id] = {
                        'id': source_id,
                        'label': record['source_props'].get('name', str(source_id)),
                        'title': str(record['source_props']),
                        'x': record['source_props'].get('x', None),
                        'y': record['source_props'].get('y', None)
                    }
                if target_id not in nodes:
                    nodes[target_id] = {
                        'id': target_id,
                        'label': record['target_props'].get('name', str(target_id)),
                        'title': str(record['target_props']),
                        'x': record['target_props'].get('x', None),
                        'y': record['target_props'].get('y', None)
                    }
                edges.append({
                    'from': source_id,
                    'to': target_id,
                    'label': record['relationship']
                })
            return {'nodes': list(nodes.values()), 'edges': edges}
    except Exception as e:
        logger.error(f"Error fetching graph data: {str(e)}")
        raise

@app.route('/')
def index():
    try:
        metadata = get_graph_metadata()
        return render_template('index.html', metadata=metadata)
    except Exception as e:
        return render_template('index.html', error=str(e))

@app.route('/get_nodes', methods=['POST'])
def get_nodes():
    try:
        data = request.json
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
                query += " AND $node_type IN labels(n)"
            if location:
                query += " AND n.location = $location"
            if sublocation:
                query += " AND n.sublocation = $sublocation"
            query += " RETURN id(n) as id, labels(n) as labels, properties(n) as props"
            result = session.run(query, node_type=node_type, location=location, sublocation=sublocation)
            nodes = []
            for record in result:
                nodes.append({
                    'id': record['id'],
                    'label': record['props'].get('name', str(record['id'])),
                    'title': str(record['props']),
                    'x': record['props'].get('x', None),
                    'y': record['props'].get('y', None)
                })
            return jsonify(nodes)
    except Exception as e:
        logger.error(f"Error fetching nodes: {str(e)}")
        return jsonify([])

@app.route('/get_relationships', methods=['POST'])
def get_relationships():
    try:
        data = request.json
        relationship_type = data.get('relationship_type')
        driver = get_neo4j_driver()
        with driver.session() as session:
            query = """
            MATCH (n)-[r]->(m)
            WHERE type(r) = $relationship_type
            RETURN id(n) as source_id, id(m) as target_id, type(r) as type
            """
            result = session.run(query, relationship_type=relationship_type)
            edges = []
            for record in result:
                edges.append({
                    'from': record['source_id'],
                    'to': record['target_id'],
                    'label': record['type']
                })
            return jsonify(edges)
    except Exception as e:
        logger.error(f"Error fetching relationships: {str(e)}")
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
