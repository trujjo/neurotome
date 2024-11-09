# Create updated app.py with fixes and new endpoints
from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
import os

app = Flask(__name__)

# Neo4j connection configuration
NEO4J_URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Poconoco16!"

def get_neo4j_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/nodes/types')
def get_node_types():
    with get_neo4j_driver().session() as session:
        result = session.run('''
            MATCH (n)
            UNWIND labels(n) as label
            RETURN DISTINCT label
            ORDER BY label
        ''')
        types = [record['label'] for record in result]
        return jsonify(types)

@app.route('/api/nodes/locations')
def get_locations():
    with get_neo4j_driver().session() as session:
        result = session.run('''
            MATCH (n)
            WHERE exists(n.location)
            RETURN DISTINCT n.location as location
            ORDER BY location
        ''')
        locations = [record['location'] for record in result]
        return jsonify(locations)

@app.route('/api/nodes/sublocations')
def get_sublocations():
    with get_neo4j_driver().session() as session:
        result = session.run('''
            MATCH (n)
            WHERE exists(n.sublocation)
            RETURN DISTINCT n.sublocation as sublocation
            ORDER BY sublocation
        ''')
        sublocations = [record['sublocation'] for record in result]
        return jsonify(sublocations)

@app.route('/api/nodes/by-type/<node_type>')
def get_nodes_by_type(node_type):
    with get_neo4j_driver().session() as session:
        result = session.run('''
            MATCH (n)
            WHERE any(label IN labels(n) WHERE label = $type)
            RETURN n
        ''', type=node_type)
        nodes = [dict(record['n']) for record in result]
        return jsonify(nodes)

@app.route('/api/nodes/by-location/<location>')
def get_nodes_by_location(location):
    with get_neo4j_driver().session() as session:
        result = session.run('''
            MATCH (n)
            WHERE n.location = $location
            RETURN n
        ''', location=location)
        nodes = [dict(record['n']) for record in result]
        return jsonify(nodes)

@app.route('/api/relationships')
def get_relationships():
    with get_neo4j_driver().session() as session:
        result = session.run('''
            MATCH (n)-[r]->(m)
            RETURN type(r) as type, count(r) as count
        ''')
        relationships = [dict(record) for record in result]
        return jsonify(relationships)

@app.route('/api/graph/filtered')
def get_filtered_graph():
    node_types = request.args.getlist('nodeTypes[]')
    locations = request.args.getlist('locations[]')
    sublocations = request.args.getlist('sublocations[]')
    
    query = '''
    MATCH (n)-[r]->(m)
    WHERE 
        (size($nodeTypes) = 0 OR any(label IN labels(n) WHERE label IN $nodeTypes))
        AND (size($locations) = 0 OR n.location IN $locations)
        AND (size($sublocations) = 0 OR n.sublocation IN $sublocations)
    RETURN n, r, m
    '''
    
    with get_neo4j_driver().session() as session:
        result = session.run(query, 
                           nodeTypes=node_types,
                           locations=locations,
                           sublocations=sublocations)
        
        nodes = []
        relationships = []
        nodes_set = set()

        for record in result:
            # Process source node
            source = dict(record['n'])
            source_id = source.get('id', str(id(source)))
            if source_id not in nodes_set:
                nodes_set.add(source_id)
                source['id'] = source_id
                source['labels'] = list(record['n'].labels)
                nodes.append(source)

            # Process target node
            target = dict(record['m'])
            target_id = target.get('id', str(id(target)))
            if target_id not in nodes_set:
                nodes_set.add(target_id)
                target['id'] = target_id
                target['labels'] = list(record['m'].labels)
                nodes.append(target)

            # Process relationship
            rel = {
                'source': source_id,
                'target': target_id,
                'type': type(record['r']).__name__,
                'properties': dict(record['r'])
            }
            relationships.append(rel)

        return jsonify({
            'nodes': nodes,
            'relationships': relationships
        })

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


with open('app.py', 'w') as f:
    f.write(updated_code)

print("Updated app.py has been created with the following changes:")
print("1. Added new endpoints for populating filters (/api/nodes/types, /api/nodes/locations, /api/nodes/sublocations)")
print("2. Removed duplicate implementation of get_filtered_graph()")
print("3. Organized imports and routes more cleanly")
