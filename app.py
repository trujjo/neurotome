from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase
import os
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

uri = "bolt://4e5eeae5.databases.neo4j.io:7687"
user = "neo4j"
password = "Poconoco16!"

def get_neo4j_driver():
    try:
        driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            encrypted=True
        )
        with driver.session() as session:
            result = session.run("RETURN 1")
            result.single()
            logger.info("Successfully connected to Neo4j")
        return driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        raise

def get_nodes_and_relationships():
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Query to get nodes and their relationships
            query = """
            MATCH (n)-[r]->(m)
            RETURN 
                labels(n) as source_labels,
                properties(n) as source_props,
                type(r) as relationship,
                labels(m) as target_labels,
                properties(m) as target_props
            """
            result = session.run(query)
            
            graph_data = []
            for record in result:
                graph_data.append({
                    'source': {
                        'labels': record['source_labels'],
                        'properties': record['source_props']
                    },
                    'relationship': record['relationship'],
                    'target': {
                        'labels': record['target_labels'],
                        'properties': record['target_props']
                    }
                })
            return graph_data
    except Exception as e:
        logger.error(f"Error fetching graph data: {str(e)}")
        raise
    finally:
        if 'driver' in locals():
            driver.close()

@app.route('/')
def index():
    try:
        data = get_nodes_and_relationships()
        return render_template('index.html', data=data)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in index route: {error_msg}")
        return render_template('index.html', error=error_msg)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
