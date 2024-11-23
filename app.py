from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from neo4j import GraphDatabase
import os

app = Flask(__name__)
CORS(app)

# Neo4j connection
driver = GraphDatabase.driver(
    "neo4j+s://4e5eeae5.databases.neo4j.io:7687",
    auth=("neo4j", "Poconoco16!")
)

# Serve static files
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('public', path)

# API Endpoints
@app.route('/api/labels', methods=['GET'])
def get_labels():
    location = request.args.get('location')
    
    with driver.session() as session:
        if location:
            query = """
                MATCH (n) 
                WHERE n.location = $location 
                WITH DISTINCT labels(n) as nodeLabels 
                UNWIND nodeLabels as label 
                RETURN DISTINCT label
            """
            result = session.run(query, {"location": location})
        else:
            result = session.run("CALL db.labels()")
            
        labels = [record[0] for record in result]
        return jsonify(labels)

@app.route('/api/distinct-values', methods=['GET'])
def get_distinct_values():
    label = request.args.get('label')
    location = request.args.get('location')
    
    with driver.session() as session:
        location_query = "MATCH (n) WHERE n.location IS NOT NULL"
        system_query = "MATCH (n) WHERE n.system IS NOT NULL"
        params = {}
        
        if label:
            location_query += f" AND n:{label}"
            system_query += f" AND n:{label}"
            
        if location:
            system_query += " AND n.location = $location"
            params['location'] = location
            
        location_query += " RETURN DISTINCT n.location"
        system_query += " RETURN DISTINCT n.system"
        
        location_result = session.run(location_query, params)
        system_result = session.run(system_query, params)
        
        return jsonify({
            'locations': [record[0] for record in location_result if record[0]],
            'systems': [record[0] for record in system_result if record[0]]
        })

@app.route('/api/nodes', methods=['POST'])
def get_nodes():
    data = request.get_json()
    labels = data.get('labels', [])
    location = data.get('location')
    system = data.get('system')
    
    with driver.session() as session:
        query = 'MATCH (n)'
        conditions = []
        params = {}
        
        if labels:
            conditions.append(' AND '.join(f"n:{label}" for label in labels))
        if location:
            conditions.append('n.location = $location')
            params['location'] = location
        if system:
            conditions.append('n.system = $system')
            params['system'] = system
            
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
            
        query += ' MATCH (n)-[r]->(m) RETURN n, labels(n), collect({rel: r, target: m}) as relationships'
        
        result = session.run(query, params)
        nodes = {}
        relationships = []
        
        for record in result:
            node = record['n']
            node_id = str(node.id)
            
            if node_id not in nodes:
                nodes[node_id] = {
                    'id': node_id,
                    'labels': record['labels(n)'],
                    'properties': dict(node.items()),
                    'size': 'large' if node.get('detail') == 'major' else 
                           'medium' if node.get('detail') == 'intermediate' else 'small'
                }
            
            for rel in record['relationships']:
                target = rel['target']
                target_id = str(target.id)
                relationships.append({
                    'source': node_id,
                    'target': target_id,
                    'type': rel['rel'].type,
                    'properties': dict(rel['rel'].items())
                })
                
                if target_id not in nodes:
                    nodes[target_id] = {
                        'id': target_id,
                        'labels': list(target.labels),
                        'properties': dict(target.items()),
                        'size': 'large' if target.get('detail') == 'major' else
                               'medium' if target.get('detail') == 'intermediate' else 'small'
                    }
        
        return jsonify({
            'nodes': list(nodes.values()),
            'relationships': relationships
        })

if __name__ == '__main__':
    app.run(debug=True)