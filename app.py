from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase, exceptions
import os

app = Flask(__name__)

# Use environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://4e5eeae5.databases.neo4j.io:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your-password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/filters')
def get_filters():
    node_types = request.args.getlist('nodeTypes[]')
    locations = request.args.getlist('locations[]')
    
    try:
        with driver.session() as session:
            query = """
            MATCH (n)
            WHERE (size($types) = 0 OR any(type IN $types WHERE n:type))
            AND (size($locations) = 0 OR n.location IN $locations)
            WITH n
            MATCH (n)-[r]-(m)
            RETURN n, r, m
            """
            result = session.run(query, types=node_types, locations=locations)
            return jsonify({"success": True, "data": [dict(record) for record in result]})
    except exceptions.ServiceUnavailable:
        return jsonify({"success": False, "error": "Database connection failed"})

if __name__ == '__main__':
    app.run(debug=True)
