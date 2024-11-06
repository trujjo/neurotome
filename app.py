from flask import Flask, render_template, render_template_string, jsonify, request
from neo4j import GraphDatabase
import logging
import time
from neo4j.exceptions import ServiceUnavailable, AuthError

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j connection configuration
NEO4J_URI = "bolt://4e5eeae5.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Poconoco16!"

class Neo4jConnection:
    def __init__(self):
        self._driver = None
        self._retry_count = 3
        self._retry_delay = 1  # seconds

    def connect(self):
        retry_count = 0
        last_exception = None

        while retry_count < self._retry_count:
            try:
                self._driver = GraphDatabase.driver(
                    NEO4J_URI,
                    auth=(NEO4J_USER, NEO4J_PASSWORD),
                    max_connection_lifetime=300,  # 5 minutes
                    max_connection_pool_size=50,
                    connection_timeout=15,        # 15 seconds timeout
                    max_retry_time=15            # 15 seconds retry
                )
                # Test the connection
                with self._driver.session() as session:
                    result = session.run("RETURN 1 as num").single()
                    if result and result.get("num") == 1:
                        logger.info("Successfully connected to Neo4j database")
                        return True
            except AuthError as ae:
                logger.error(f"Authentication failed: {str(ae)}")
                raise  # Don't retry auth failures
            except Exception as e:
                last_exception = e
                retry_count += 1
                logger.warning(f"Connection attempt {retry_count} failed: {str(e)}")
                if retry_count < self._retry_count:
                    time.sleep(self._retry_delay)
                continue
            
        logger.error(f"Failed to connect after {self._retry_count} attempts. Last error: {str(last_exception)}")
        raise last_exception

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def get_session(self):
        if not self._driver:
            self.connect()
        return self._driver.session()

def get_all_nodes():
    try:
        connection = Neo4jConnection()
        connection.connect()  # Explicitly connect first
        
        with connection.get_session() as session:
            # Modified query to be more specific and efficient
            query = """
            MATCH (n)
            WHERE n.name IS NOT NULL
            RETURN DISTINCT n.name as name
            LIMIT 1000
            """
            result = session.run(query)
            nodes = [record["name"] for record in result]
            
        connection.close()
        return nodes
    except Exception as e:
        logger.error(f"Error getting nodes: {str(e)}")
        return []

@app.route('/')
def index():
    try:
        nodes = get_all_nodes()
        if not nodes:
            logger.warning("No nodes returned from database")
            return render_template_string(html_template, 
                                       nodes=[], 
                                       error="Unable to retrieve nodes from database")
        return render_template_string(html_template, nodes=nodes)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template_string(html_template, 
                                   nodes=[], 
                                   error="Failed to connect to database")

# ... rest of your code remains the same ...

if __name__ == '__main__':
    # For Render.com deployment
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
