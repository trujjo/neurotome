from flask import Flask, render_template
from neo4j import GraphDatabase
import os

app = Flask(__name__)

# Set up the connection details
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j+s://4e5eeae5.databases.neo4j.io')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Poconoco16!')

# Create a driver instance
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def fetch_data():
    with driver.session() as session:
        # Example query to fetch nodes and relationships
        result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 10")
        data = []
        for record in result:
            data.append({
                "node1": record['n'],
                "relationship": record['r'],
                "node2": record['m']
            })
        return data

@app.route('/')
def index():
    data = fetch_data()
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
