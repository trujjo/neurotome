from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase
import os
import logging
import json

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j Configuration using bolt protocol
uri = "bolt://4e5eeae5.databases.neo4j.io:7687"
user = "neo4j"
password = "Poconoco16!"

def serialize_neo4j_data(value):
    """Handle Neo4j data type serialization"""
    if hasattr(value, 'items'):
        return dict(value)
    elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
        return list(value)
    return str(value)

def get_neo4j_driver():
    try:
        driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            encrypted=True
        )
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1")
            result.single()
            logger.info("Successfully connected to Neo4j")
        
        return driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        raise

def get_graph_data():
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # First, let's see what kind of nodes we have
            query = """
            MATCH (n)
            RETURN DISTINCT labels(n) as labels
            LIMIT 5
            """
            result = session.run(query)
            labels = [record["labels"] for record in result]
            logger.info(f"Found node labels: {labels}")

            # Now get some actual nodes
            query = """
            MATCH (n)
            RETURN n, labels(n) as labels, properties(n) as props
            LIMIT 5
            """
            result = session.run(query)
            
            data = []
            for record in result:
                node_data = {
                    "labels": record["labels"],
                    "properties": {
                        k: serialize_neo4j_data(v)
                        for k, v in record["props"].items()
                    }
                }
                data.append(node_data)
            
            logger.info(f"Retrieved {len(data)} nodes")
            return data
    except Exception as e:
        logger.error(f"Error fetching graph data: {str(e)}")
        raise
    finally:
        if 'driver' in locals():
            driver.close()

@app.route('/')
def index():
    try:
        data = get_graph_data()
        return render_template('index.html', data=data)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in index route: {error_msg}")
        return render_template('index.html', error=error_msg)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
