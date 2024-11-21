from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
from flask_cors import CORS
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Neo4j connection configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_neo4j_driver():
    return driver

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/nodes/random')
def get_random_nodes():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WITH n, rand() as random
                ORDER BY random
                LIMIT 5
                MATCH (n)-[r]-(m)
                RETURN DISTINCT n, r, m
                LIMIT 100
            ''')
            nodes = []
            relationships = []
            node_ids = set()
            
            for record in result:
                source = record['n']
                target = record['m']
                rel = record['r']
                
                for node in (source, target):
                    if node.id not in node_ids:
                        nodes.append({
                            'id': node.id,
                            'labels': list(node.labels),
                            'properties': dict(node)
                        })
                        node_ids.add(node.id)
                
                relationships.append({
                    'source': source.id,
                    'target': target.id,
                    'type': rel.type
                })
            
            # Move logging statements inside the function
            logger.debug(f"Returned nodes: {nodes}")
            logger.debug(f"Returned relationships: {relationships}")
            
            return jsonify({
                'nodes': nodes,
                'relationships': relationships
            })
    except Exception as e:
        logger.error(f"Error in get_random_nodes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/neo4j/status')
def neo4j_status():
    try:
        with get_neo4j_driver().session() as session:
            session.run("RETURN 1")
        return jsonify({"status": "connected"})
    except Exception as e:
        return jsonify({"status": "disconnected"}), 500

if __name__ == "__main__":
    app.run(debug=True)

@app.route('/api/nodes/filtered', methods=['GET'])
def get_filtered_nodes():
    try:
        labels = request.args.getlist('labels')
        relationships = request.args.getlist('relationships')
        location = request.args.get('location')

        query = """
        MATCH (n)
        WHERE 1=1
        """
        params = {}

        if labels:
            query += " AND any(label IN $labels WHERE label in labels(n))"
            params['labels'] = labels

        if location:
            query += " AND n.location = $location"
            params['location'] = location

        if relationships:
            query += """
            WITH n
            MATCH (n)-[r]->(m)
            WHERE type(r) IN $relationships
            """
            params['relationships'] = relationships
        else:
            query += """
            WITH n
            MATCH (n)-[r]->(m)
            """

        query += " RETURN DISTINCT n, r, m LIMIT 100"

        with get_neo4j_driver().session() as session:
            result = session.run(query, params)
            nodes = []
            relationships = []
            node_ids = set()
            
            for record in result:
                source = record['n']
                target = record['m']
                rel = record['r']
                
                for node in (source, target):
                    if node.id not in node_ids:
                        nodes.append({
                            'id': node.id,
                            'labels': list(node.labels),
                            'properties': dict(node)
                        })
                        node_ids.add(node.id)
                
                relationships.append({
                    'source': source.id,
                    'target': target.id,
                    'type': rel.type
                })

            logger.debug(f"Filtered nodes: {nodes}")
            logger.debug(f"Filtered relationships: {relationships}")
            
            return jsonify({
                'nodes': nodes,
                'relationships': relationships
            })

    except Exception as e:
        logger.error(f"Error in get_filtered_nodes: {str(e)}")
        return jsonify({"error": str(e)}), 500