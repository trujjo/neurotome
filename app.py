from flask import Flask, render_template, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Add configuration for Neo4j
app.config['NEO4J_URI'] = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
app.config['NEO4J_USER'] = "neo4j"
app.config['NEO4J_PASSWORD'] = "Poconoco16!"  # Better to use environment variables

@app.route('/')
def index():
    return render_template('index.html', 
                         neo4j_uri=app.config['NEO4J_URI'],
                         neo4j_user=app.config['NEO4J_USER'],
                         neo4j_password=app.config['NEO4J_PASSWORD'])

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
