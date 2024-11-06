from flask import Flask, render_template, request
from neo4j import GraphDatabase
import os
import logging
import requests
import time

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j Configuration - using neo4j+s:// protocol for Aura
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j+s://4e5eeae5.databases.neo4j.io:7687')  # Added explicit port
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Poconoco16!')

def get_driver():
    try:
        # Simplified connection approach for Aura
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_pool_size=50
        )
        return driver
    except Exception as e:
        logger.error(f"Failed to create driver: {str(e)}")
        raise

def fetch_data():
    driver = None
    try:
        driver = get_driver()
        with driver.session() as session:
            # Simple query to test connection
            result = session.run("MATCH (n) RETURN n LIMIT 1")
            data = [dict(record['n']) for record in result]
            return data
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        raise
    finally:
        if driver:
            driver.close()

@app.route('/')
def index():
    try:
        data = fetch_data()
        return render_template('index.html', data=data)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html', error=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
