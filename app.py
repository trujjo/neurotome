from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase

app = Flask(__name__)

# Hardcoded Neo4j credentials
uri = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
user = "neo4j"
password = "Poconoco16!"

driver = GraphDatabase.driver(uri, auth=(user, password))

@app.route('/')
def index():
    return render_template('visualization.html')

@app.route('/graph')
def get_graph():
    with driver.session() as session:
        # Get nodes, relationships, and metadata for filters
        result = session.run("""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            WITH n, r, m
            RETURN {
                nodes: collect(distinct {
                    id: id(n),
                    labels: labels(n),
                    properties: properties(n),
                    x: coalesce(n.x, 0),
                    y: coalesce(n.y, 0)
                }),
                relationships: collect(distinct {
                    source: id(startNode(r)),
                    target: id(endNode(r)),
                    type: type(r)
                }) WHERE r IS NOT NULL,
                nodeTypes: collect(distinct labels(n)[0]),
                locations: collect(distinct n.location),
                sublocations: collect(distinct n.sublocation)
            }
        """)
        
        data = result.single()
        
        # Clean up the data
        cleaned_data = {
            'nodes': [node for node in data[0]['nodes'] if node['id'] is not None],
            'relationships': [rel for rel in data[0]['relationships'] if rel['source'] is not None and rel['target'] is not None],
            'nodeTypes': [t for t in data[0]['nodeTypes'] if t is not None],
            'locations': [l for l in data[0]['locations'] if l is not None],
            'sublocations': [s for s in data[0]['sublocations'] if s is not None]
        }
        
        return jsonify(cleaned_data)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    
    with driver.session() as session:
        result = session.run("""
            MATCH (n)
            WHERE any(prop in keys(n) WHERE toString(n[prop]) CONTAINS $query)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN {
                nodes: collect(distinct {
                    id: id(n),
                    labels: labels(n),
                    properties: properties(n),
                    x: coalesce(n.x, 0),
                    y: coalesce(n.y, 0)
                }),
                relationships: collect(distinct {
                    source: id(startNode(r)),
                    target: id(endNode(r)),
                    type: type(r)
                }) WHERE r IS NOT NULL
            }
        """, query=query)
        
        data = result.single()
        return jsonify(data[0])

@app.route('/update_layout', methods=['POST'])
def update_layout():
    data = request.json
    node_id = data.get('id')
    x = data.get('x', 0)
    y = data.get('y', 0)
    
    with driver.session() as session:
        session.run("""
            MATCH (n)
            WHERE id(n) = $id
            SET n.x = $x, n.y = $y
        """, id=node_id, x=x, y=y)
    
    return jsonify({'status': 'success'})

@app.route('/node_info/<node_id>')
def node_info(node_id):
    with driver.session() as session:
        result = session.run("""
            MATCH (n)
            WHERE id(n) = $id
            RETURN {
                id: id(n),
                labels: labels(n),
                properties: properties(n)
            } as node
        """, id=int(node_id))
        
        node = result.single()
        return jsonify(node[0])

@app.route('/neighbors/<node_id>')
def get_neighbors(node_id):
    with driver.session() as session:
        result = session.run("""
            MATCH (n)-[r]-(m)
            WHERE id(n) = $id
            RETURN {
                nodes: collect(distinct {
                    id: id(m),
                    labels: labels(m),
                    properties: properties(m),
                    x: coalesce(m.x, 0),
                    y: coalesce(m.y, 0)
                }),
                relationships: collect({
                    source: id(startNode(r)),
                    target: id(endNode(r)),
                    type: type(r)
                })
            }
        """, id=int(node_id))
        
        data = result.single()
        return jsonify(data[0])

if __name__ == '__main__':
    app.run(debug=True)
