from flask import Flask, render_template, request
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import os
import logging
import requests
import time

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j Configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j+s://4e5eeae5.databases.neo4j.io')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Poconoco16!')

def get_driver(max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                connection_timeout=120,  # Increase timeout to 120 seconds
                max_connection_lifetime=60 * 60,  # 1 hour
                max_connection_pool_size=50
            )
            # Verify connectivity
            driver.verify_connectivity()
            return driver
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

def fetch_data():
    try:
        driver = get_driver()
        with driver.session(connection_timeout=120) as session:  # Increase session timeout
            result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 10")
            data = []
            for record in result:
                data.append({
                    "node1": dict(record['n']),
                    "relationship": dict(record['r']),
                    "node2": dict(record['m'])
                })
            return data
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        raise
    finally:
        if 'driver' in locals():
            driver.close()

@app.route('/')
def index():
    try:
        # Print the IP address for debugging
        response = requests.get('https://api.ipify.org?format=json')
        ip = response.json()['ip']
        logger.info(f"Current IP Address: {ip}")
        
        data = fetch_data()
        return render_template('index.html', data=data)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html', error=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
