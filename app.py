from flask import Flask, jsonify
from neo4j import GraphDatabase
import os

app = Flask(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt+s://4e5eeae5.databases.neo4j.io:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "<REDACTED_PASSWORD>")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_neo4j_driver():
    return driver

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/api/labels')
def get_labels():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('CALL db.labels() YIELD label RETURN label ORDER BY label')
            labels = [record['label'] for record in result]
            return jsonify(labels)
    except Exception as e:
        app.logger.error(f"Error in get_labels: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/relationship-types')
def get_relationship_types():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType')
            relationship_types = [record['relationshipType'] for record in result]
            return jsonify(relationship_types)
    except Exception as e:
        app.logger.error(f"Error in get_relationship_types: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/locations')
def get_locations():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WHERE n.location IS NOT NULL
                RETURN DISTINCT n.location AS location
                ORDER BY location
            ''')
            locations = [record['location'] for record in result]
            return jsonify(locations)
    except Exception as e:
        app.logger.error(f"Error in get_locations: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)