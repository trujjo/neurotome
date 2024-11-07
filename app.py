from flask import Flask, jsonify, request
from neo4j import GraphDatabase
import os

app = Flask(__name__)

# Neo4j Configuration
URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
AUTH = ("neo4j", "Poconoco16!")

driver = GraphDatabase.driver(uri, auth=(username, password))

@app.route('/')
def home():
    return '''
        <form action="/search" method="get">
            <input type="text" name="q" placeholder="Search properties...">
            <input type="submit" value="Search">
        </form>
        <div id="results"></div>
    '''

@app.route('/search')
def search():
    search_term = request.args.get('q', '')
    
    def search_nodes(tx, term):
        query = """
        MATCH (n)
        WHERE any(prop in keys(n) WHERE toString(n[prop]) CONTAINS $term)
        RETURN n
        LIMIT 10
        """
        result = tx.run(query, term=term)
        return [dict(record["n"].items()) for record in result]

    try:
        with driver.session() as session:
            results = session.read_transaction(search_nodes, search_term)
            return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.teardown_appcontext
def close_db(error):
    if driver is not None:
        driver.close()

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
