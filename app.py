# Add at top
from functools import wraps
from datetime import datetime

# Add connection pooling
driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
    max_connection_lifetime=3600
)

# Add decorator for error handling
def handle_db_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {f.__name__}: {str(e)}")
            return jsonify({"error": "An internal error occurred"}), 500
    return wrapper

# Add cleanup
@app.teardown_appcontext
def close_db(error):
    if driver:
        driver.close()

# Move routes before if __name__ == "__main__"
# Add proper environment handling
if __name__ == "__main__":
    app.run(debug=os.environ.get('FLASK_ENV') == 'development')