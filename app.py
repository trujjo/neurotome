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
    
    # Updated query to handle node properties and relationships better
    query = '''
    MATCH (n)
    WHERE (size($nodeTypes) = 0 OR any(label IN labels(n) WHERE label IN $nodeTypes))
    AND (size($locations) = 0 OR n.location IN $locations)
    WITH collect(distinct n) as nodes
    MATCH (n1)-[r]->(n2)
    WHERE n1 IN nodes AND n2 IN nodes
    RETURN {
        nodes: [node IN nodes | {
            id: id(node),
            labels: labels(node),
            properties: properties(node),
            name: coalesce(node.name, head(labels(node))),
            type: head(labels(node))
        }],
        relationships: [{
            id: id(r),
            source: id(startNode(r)),
            target: id(endNode(r)),
            type: type(r),
            properties: properties(r)
        } | r in collect(distinct r)]
    } as graph
    '''
    
    with get_neo4j_driver().session() as session:
        try:
            result = session.run(query, nodeTypes=node_types, locations=locations)
            graph_data = result.single()['graph']
            return jsonify(graph_data)
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
