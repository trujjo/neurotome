from flask import Flask, render_template, request
from neo4j import GraphDatabase
import os
import logging
import requests

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    try:
        # Print the IP address for debugging
        response = requests.get('https://api.ipify.org?format=json')
        ip = response.json()['ip']
        logger.info(f"Current IP Address: {ip}")
        
        # Your existing code...
        data = fetch_data()
        return render_template('index.html', data=data)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return f"An error occurred: {str(e)}", 500

# ... rest of your existing code ...




from flask import Flask, render_template
from neo4j import GraphDatabase
import os
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables with fallbacks
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j+s://4e5eeae5.databases.neo4j.io')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Poconoco16!')

def get_driver():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        # Verify connectivity
        driver.verify_connectivity()
        return driver
    except Exception as e:
        logger.error(f"Failed to create driver: {str(e)}")
        raise

def fetch_data():
    try:
        driver = get_driver()
        with driver.session() as session:
            # Simple query to test connection
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
        data = fetch_data()
        return render_template('index.html', data=data)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
