from functools import wraps
from neo4j.exceptions import ServiceUnavailable, AuthError
from flask import jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_neo4j_error(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ServiceUnavailable as e:
            logger.error(f"Neo4j database is unavailable: {str(e)}")
            return jsonify({
                'error': 'Database connection error',
                'message': 'Unable to connect to the database. Please try again later.'
            }), 503
        except AuthError as e:
            logger.error(f"Neo4j authentication error: {str(e)}")
            return jsonify({
                'error': 'Authentication error',
                'message': 'Database authentication failed.'
            }), 401
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred.'
            }), 500
    return wrapper

# Example usage in routes:
@app.route('/api/graph/data')
@handle_neo4j_error
def get_graph_data():
    with get_neo4j_driver().session() as session:
        result = session.run("MATCH (n) RETURN n LIMIT 10")
        return jsonify([dict(record['n']) for record in result])

