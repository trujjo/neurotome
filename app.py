from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase
import os
import logging
import json

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

@app.route('/get_nodes', methods=['POST'])
def get_nodes():
    try:
        node_type = request.json.get('node_type')
        location = request.json.get('location')
        sublocation = request.json.get('sublocation')
        
        driver = get_neo4j_driver()
        with driver.session() as session:
            query = """
            MATCH (n)
            WHERE $node_type IN labels(n)
            AND (n.location = $location OR $location IS NULL)
            AND (n.sublocation = $sublocation OR $sublocation IS NULL)
            RETURN n, ID(n) as id
            """
            result = session.run(query, 
                               node_type=node_type, 
                               location=location, 
                               sublocation=sublocation)
            
            nodes = []
            for record in result:
                node = record['n']
                nodes.append({
                    'id': record['id'],
                    'label': str(node.get('name', '')),
                    'title': str(dict(node)),
                    'group': node_type
                })
            
            return jsonify(nodes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_relationships', methods=['POST'])
def get_relationships():
    try:
        rel_type = request.json.get('relationship_type')
        
        driver = get_neo4j_driver()
        with driver.session() as session:
            query = """
            MATCH (n)-[r]->(m)
            WHERE type(r) = $rel_type
            RETURN ID(n) as from, ID(m) as to, type(r) as label
            """
            result = session.run(query, rel_type=rel_type)
            
            edges = []
            for record in result:
                edges.append({
                    'from': record['from'],
                    'to': record['to'],
                    'label': record['label'],
                    'arrows': 'to'
                })
            
            return jsonify(edges)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    try:
        metadata = get_graph_metadata()
        return render_template('index.html', metadata=metadata)
    except Exception as e:
        return render_template('index.html', error=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
