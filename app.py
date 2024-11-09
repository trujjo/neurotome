from flask import Flask, render_template, jsonify
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

@app.route('/get_graph_data')
def get_graph_data():
    with get_neo4j_driver().session() as session:
        # Query to get nodes and relationships
        result = session.run("""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN collect(distinct {
                id: id(n),
                labels: labels(n),
                properties: properties(n)
            }) as nodes,
            collect(distinct {
                source: id(startNode(r)),
                target: id(endNode(r)),
                type: type(r),
                properties: properties(r)
            }) as relationships
        """)
        graph_data = result.single()
        return jsonify({
            'nodes': graph_data['nodes'],
            'relationships': graph_data['relationships']
        })

if __name__ == '__main__':
    app.run(debug=True)
