from flask import Flask, render_template, jsonify
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import logging
import atexit
from error_handling import handle_neo4j_error

load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate required environment variables
required_env_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Neo4j connection configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize Neo4j driver
driver = None

def init_neo4j_driver():
    global driver
    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        # Test connection
        with driver.session() as session:
            session.run("RETURN 1")
        logger.info("Successfully connected to Neo4j database")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise

def close_neo4j_driver():
    global driver
    if driver:
        driver.close()
        logger.info("Neo4j driver closed")

# Initialize driver on startup
init_neo4j_driver()

# Register cleanup function
atexit.register(close_neo4j_driver)

def get_neo4j_driver():
    global driver
    if not driver:
        raise RuntimeError("Neo4j driver not initialized")
    return driver

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for deployment"""
    try:
        with get_neo4j_driver().session() as session:
            session.run("RETURN 1")
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "database": "disconnected"}), 503

@app.route('/api/nodes/random')
@handle_neo4j_error
def get_random_nodes():
    with get_neo4j_driver().session() as session:
        result = session.run('''
            MATCH (n)
            WITH n, rand() as random
            ORDER BY random
            LIMIT 50
            MATCH (n)-[rel]-(m)
            RETURN DISTINCT n, rel, m
            LIMIT 100
        ''')
        
        nodes = []
        for record in result:
            node = record['n']
            related_node = record['m']
            relationship = record['rel']
            nodes.append({
                'n': {
                    'id': node.id,
                    'labels': list(node.labels),
                    'properties': dict(node)
                },
                'm': {
                    'id': related_node.id,
                    'labels': list(related_node.labels),
                    'properties': dict(related_node)
                },
                'rel': {
                    'type': relationship.type,
                    'properties': dict(relationship)
                }
            })
        
        logger.info(f"Fetched {len(nodes)} node relationships")
        return jsonify(nodes)

@app.route('/api/neo4j/status')
@handle_neo4j_error
def neo4j_status():
    with get_neo4j_driver().session() as session:
        result = session.run("CALL dbms.components() YIELD name, versions, edition")
        info = result.single()
        return jsonify({
            "status": "connected",
            "database_info": {
                "name": info["name"],
                "version": info["versions"][0],
                "edition": info["edition"]
            }
        })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # Only use debug mode in development
    debug_mode = os.getenv("FLASK_ENV") == "development"
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))