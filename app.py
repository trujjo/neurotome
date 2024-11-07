from flask import Flask, render_template, jsonify
from neo4j import GraphDatabase
import os
from contextlib import contextmanager

app = Flask(__name__)

# Configuration
URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
AUTH = ("neo4j", "Poconoco16!")

# Database connection management
@contextmanager
def get_db_connection():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        yield driver
    finally:
        driver.close()

class Neo4jConnection:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        
    def close(self):
        self.driver.close()
        
    def query(self, query, parameters=None):
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record for record in result]
            except Exception as e:
                print(f"Query failed: {e}")
                return None

# Routes
@app.route('/')
def index():
    """Main visualization page"""
    return render_template('visualization.html')

@app.route('/graph/data')
def get_graph_data():
    """API endpoint to fetch graph data"""
    try:
        with get_db_connection() as driver:
            with driver.session() as session:
                # Basic query to get nodes and relationships
                query = """
                MATCH (n)-[r]->(m)
                RETURN collect(distinct {
                    id: id(n),
                    label: labels(n)[0],
                    properties: properties(n)
                }) as nodes,
                collect(distinct {
                    source: id(n),
                    target: id(m),
                    type: type(r),
                    properties: properties(r)
                }) as relationships
                """
                result = session.run(query)
                graph_data = result.single()
                return jsonify(graph_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/graph/stats')
def get_graph_stats():
    """API endpoint to fetch graph statistics"""
    try:
        with get_db_connection() as driver:
            with driver.session() as session:
                # Query to get basic graph statistics
                query = """
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->()
                RETURN 
                count(distinct n) as nodeCount,
                count(distinct r) as relationshipCount,
                collect(distinct labels(n)) as labels
                """
                result = session.run(query)
                stats = result.single()
                return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/graph/search/<label>')
def search_nodes(label):
    """API endpoint to search nodes by label"""
    try:
        with get_db_connection() as driver:
            with driver.session() as session:
                query = f"""
                MATCH (n:{label})
                RETURN n
                LIMIT 100
                """
                result = session.run(query)
                nodes = [record['n'] for record in result]
                return jsonify(nodes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        with get_db_connection() as driver:
            with driver.session() as session:
                result = session.run("RETURN 1")
                return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Configuration for development
if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Set debug mode based on environment
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    # Run the application
    app.run(
        host='0.0.0.0',  # Makes the server publicly available
        port=port,
        debug=debug
    )
