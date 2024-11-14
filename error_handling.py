from functools import wraps
from neo4j.exceptions import ServiceUnavailable, AuthError
from flask import jsonify
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_neo4j_error(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ServiceUnavailable as e:
            logger.error(f"Neo4j database is unavailable: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'error': 'Database connection error',
                'message': 'Unable to connect to the database. Please check if the Neo4j service is running and accessible.',
                'details': str(e)
            }), 503
        except AuthError as e:
            logger.error(f"Neo4j authentication error: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'error': 'Authentication error',
                'message': 'Database authentication failed. Please verify your credentials.',
                'details': str(e)
            }), 401
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred. Please contact support.',
                'details': str(e)
            }), 500
    return wrapper

# Example usage in routes:
'''
@app.route('/api/graph/data')
@handle_neo4j_error
def get_graph_data():
    with get_neo4j_driver().session() as session:
        result = session.run("MATCH (n) RETURN n LIMIT 10")
        return jsonify([dict(record['n']) for record in result])
'''
