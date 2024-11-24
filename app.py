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
    with driver.session() as session:
        # Simple query to get all labels without filtering
        result = session.run("CALL db.labels()")
        labels = [record[0] for record in result]
        return jsonify(labels)

@app.route('/api/distinct-values', methods=['GET'])
def get_distinct_values():
    label = request.args.get('label')
    is_explore = request.args.get('explore') == 'true'
    
    with driver.session() as session:
        if is_explore:
            # Location tree query with optional label filter
            location_query = """
                MATCH (n)
                WHERE n.location IS NOT NULL
                {}
                WITH DISTINCT n.location as location
                OPTIONAL MATCH (m)
                WHERE m.sublocation IS NOT NULL 
                AND m.location = location
                {}
                RETURN location, collect(DISTINCT m.sublocation) as sublocations
                ORDER BY location
            """.format(
                f"AND n:{label}" if label else "",
                f"AND m:{label}" if label else ""
            )
            
            location_result = session.run(location_query)
            locations_data = [(record["location"], record["sublocations"]) 
                            for record in location_result if record["location"]]

            # System query with optional label filter
            system_query = f"""
                MATCH (n) 
                WHERE n.system IS NOT NULL
                {f"AND n:{label}" if label else ""}
                RETURN DISTINCT n.system 
                ORDER BY n.system
            """
            system_result = session.run(system_query)
            
            return jsonify({
                'locationTree': locations_data,
                'systems': [record[0] for record in system_result if record[0]]
            })
        else:
            # Property queries with optional label filter
            def get_property_values(property_name):
                query = f"""
                    MATCH (n)
                    WHERE n.{property_name} IS NOT NULL
                    {f"AND n:{label}" if label else ""}
                    RETURN DISTINCT n.{property_name}
                    ORDER BY n.{property_name}
                """
                result = session.run(query)
                return [record[0] for record in result if record[0]]

            return jsonify({
                'locations': get_property_values('location'),
                'sublocations': get_property_values('sublocation'),
                'systems': get_property_values('system')
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
                    'size': 'large' if node.get('detail') == 'comprehensive' else 
                           'medium' if node.get('detail') == 'meticulous' else 'small'
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
                        'size': 'large' if target.get('detail') == 'comprehensive' else
                               'medium' if target.get('detail') == 'meticulous' else 'small'
                    }
        
        return jsonify({
            'nodes': list(nodes.values()),
            'relationships': relationships
        })

if __name__ == '__main__':
    app.run(debug=True)