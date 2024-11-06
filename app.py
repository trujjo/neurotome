from flask import Flask, render_template, request
from neo4j import GraphDatabase
import os
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j Configuration using bolt protocol
uri = "bolt://4e5eeae5.databases.neo4j.io:7687"  # Changed to bolt://
user = "neo4j"
password = "Poconoco16!"

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
            query = """
            MATCH (n)
            RETURN n LIMIT 5
            """
            result = session.run(query)
            data = [dict(record["n"]) for record in result]
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
